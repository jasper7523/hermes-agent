"""LSP Client — Lightweight Language Server Protocol adapter for hermes-agent.

Provides go-to-definition and hover/signature queries by managing a
``jedi-language-server`` (or ``pyright-langserver``) subprocess over stdio.

Key design decisions (from Phase 4 design contract):
  - Q7 (C): Hybrid server detection — prefer jedi-language-server, fall back
    to pyright if USE_PYRIGHT=1 and node is available.
  - Q8 (B): Background ``threading.Thread`` reads stdout; main thread sends
    requests and blocks on ``queue.Queue`` with hard timeout.
  - Q9 (A): Auto-install jedi-language-server into the project venv when
    missing.

Workspace & venv detection algorithm:
  1. Walk up from the target file to find the nearest project root
     (.git, pyproject.toml, setup.py, shared-dna.md).
  2. Locate the venv inside that root (venv/ → .venv/ → system Python).
  3. Start the language server scoped to that workspace root.
  4. Cache one LSPClient instance per workspace root to avoid duplicate
     processes when N5/N8 share the same Agent_Hub workspace.

Safety:
  - 3-second hard timeout on every request.
  - atexit + __del__ cleanup to prevent orphan processes.
  - All failures are non-fatal: callers get None and can fall back to
    grep/view_file.

Author: N7 Hermes Agent
"""

import atexit
import json
import logging
import os
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_REQUEST_TIMEOUT_SECS = 5.0  # Hard timeout per LSP request
_INIT_TIMEOUT_SECS = 10.0  # Longer timeout for initialize handshake

# Markers that indicate a project root directory
_ROOT_MARKERS = (".git", "pyproject.toml", "setup.py", "setup.cfg", "shared-dna.md")

# Venv directory names to probe (in priority order)
_VENV_DIRS = ("venv", ".venv")

# ---------------------------------------------------------------------------
# Singleton cache: workspace_root → LSPClient
# ---------------------------------------------------------------------------

_instances: Dict[str, "LSPClient"] = {}
_instances_lock = threading.Lock()


# ═══════════════════════════════════════════════════════════════════════════
#  Workspace & Venv Detection
# ═══════════════════════════════════════════════════════════════════════════

def find_workspace_root(filepath: str) -> Optional[Path]:
    """Walk up from *filepath* to find the nearest project root."""
    current = Path(filepath).resolve()
    if current.is_file():
        current = current.parent

    # Walk up until we hit the drive root
    while current != current.parent:
        for marker in _ROOT_MARKERS:
            if (current / marker).exists():
                return current
        current = current.parent

    return None


def find_python_exe(workspace_root: Path) -> Path:
    """Locate the best Python executable for *workspace_root*.

    Probes venv/Scripts/python.exe (Windows) and venv/bin/python (Unix)
    inside the workspace root.  Falls back to ``sys.executable``.
    """
    for vdir in _VENV_DIRS:
        venv_path = workspace_root / vdir
        if not venv_path.is_dir():
            continue
        # Windows
        candidate = venv_path / "Scripts" / "python.exe"
        if candidate.exists():
            return candidate
        # Unix
        candidate = venv_path / "bin" / "python"
        if candidate.exists():
            return candidate

    return Path(sys.executable)


def _is_module_installed(python_exe: Path, module_name: str) -> bool:
    """Check whether *module_name* is importable via *python_exe*."""
    try:
        result = subprocess.run(
            [str(python_exe), "-c", f"import {module_name}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def _auto_install_jedi(python_exe: Path) -> bool:
    """Attempt to pip-install jedi-language-server into the venv.

    Returns True on success, False on failure (network down, etc.).
    Failures are non-fatal — caller should fall back gracefully.
    """
    logger.info("LSP: auto-installing jedi-language-server via %s", python_exe)
    try:
        result = subprocess.run(
            [str(python_exe), "-m", "pip", "install", "-q", "jedi-language-server"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        if result.returncode == 0:
            logger.info("LSP: jedi-language-server installed successfully.")
            return True
        logger.warning(
            "LSP: pip install failed (rc=%d): %s",
            result.returncode,
            result.stderr.decode("utf-8", errors="replace")[:500],
        )
        return False
    except Exception as exc:
        logger.warning("LSP: auto-install failed: %s", exc)
        return False


def resolve_server_cmd(workspace_root: Path, python_exe: Path) -> Optional[List[str]]:
    """Determine the Language Server command line.

    Priority:
      1. Pyright if USE_PYRIGHT=1 and ``pyright-langserver`` is on PATH.
      2. jedi-language-server (auto-install if needed).
      3. None if nothing works (caller should disable LSP tools).
    """
    # --- Priority 1: Pyright (opt-in) ---
    if os.environ.get("USE_PYRIGHT") == "1":
        pyright_path = shutil.which("pyright-langserver")
        if pyright_path:
            return [pyright_path, "--stdio"]
        logger.debug("LSP: USE_PYRIGHT=1 but pyright-langserver not found on PATH.")

    # --- Priority 2: jedi-language-server ---
    if not _is_module_installed(python_exe, "jedi_language_server"):
        if not _auto_install_jedi(python_exe):
            return None

    return [str(python_exe), "-m", "jedi_language_server"]


# ═══════════════════════════════════════════════════════════════════════════
#  LSPClient
# ═══════════════════════════════════════════════════════════════════════════

class LSPClient:
    """Manages a single Language Server subprocess and its JSON-RPC I/O."""

    def __init__(self, workspace_root: Path, python_exe: Path):
        self.workspace_root = workspace_root
        self.workspace_uri = workspace_root.as_uri()
        self._python_exe = python_exe
        self._msg_id = 0
        self._responses: Dict[int, queue.Queue] = {}
        self._lock = threading.Lock()
        self._alive = False
        self._proc: Optional[subprocess.Popen] = None
        self._recv_thread: Optional[threading.Thread] = None
        self._initialized = False

        cmd = resolve_server_cmd(workspace_root, python_exe)
        if cmd is None:
            logger.warning("LSP: no suitable language server found for %s", workspace_root)
            return

        try:
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(workspace_root),
                bufsize=0,
            )
            self._alive = True
        except Exception as exc:
            logger.warning("LSP: failed to start server: %s", exc)
            return

        # Background reader thread (daemon so it dies with the process)
        self._recv_thread = threading.Thread(
            target=self._recv_loop, name="lsp-recv", daemon=True
        )
        self._recv_thread.start()

        # Register cleanup
        atexit.register(self.shutdown)

        # Perform LSP initialize handshake
        self._do_initialize()

    # ------------------------------------------------------------------
    #  JSON-RPC transport
    # ------------------------------------------------------------------

    def _recv_loop(self):
        """Background thread: continuously read JSON-RPC messages from stdout."""
        try:
            while self._alive and self._proc and self._proc.poll() is None:
                # Read headers until empty line
                content_length = -1
                while True:
                    raw_line = self._proc.stdout.readline()
                    if not raw_line:
                        # EOF — server exited
                        self._alive = False
                        return
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line:
                        # Empty line = end of headers
                        break
                    if line.lower().startswith("content-length:"):
                        try:
                            content_length = int(line.split(":", 1)[1].strip())
                        except ValueError:
                            pass

                if content_length <= 0:
                    continue

                # Read exactly content_length bytes
                body = b""
                while len(body) < content_length:
                    chunk = self._proc.stdout.read(content_length - len(body))
                    if not chunk:
                        self._alive = False
                        return
                    body += chunk

                try:
                    data = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError:
                    continue

                # Dispatch responses (have "id") to waiting queues
                msg_id = data.get("id")
                if msg_id is not None:
                    with self._lock:
                        q = self._responses.get(msg_id)
                    if q:
                        q.put(data)
                # Notifications (no "id") are silently consumed

        except Exception as exc:
            logger.debug("LSP recv thread stopped: %s", exc)
            self._alive = False

    def _send_request(self, method: str, params: dict, timeout: float = _REQUEST_TIMEOUT_SECS) -> Optional[dict]:
        """Send a JSON-RPC request and block until response or timeout.

        Returns the response dict, or None on timeout/error.
        """
        if not self._alive or not self._proc:
            return None

        with self._lock:
            self._msg_id += 1
            curr_id = self._msg_id
            q: queue.Queue = queue.Queue(maxsize=1)
            self._responses[curr_id] = q

        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": curr_id,
            "method": method,
            "params": params,
        })
        message = f"Content-Length: {len(payload.encode('utf-8'))}\r\n\r\n{payload}"

        try:
            self._proc.stdin.write(message.encode("utf-8"))
            self._proc.stdin.flush()
        except (OSError, BrokenPipeError):
            self._alive = False
            with self._lock:
                self._responses.pop(curr_id, None)
            return None

        try:
            response = q.get(timeout=timeout)
            return response
        except queue.Empty:
            logger.debug("LSP request '%s' timed out after %.1fs", method, timeout)
            return None
        finally:
            with self._lock:
                self._responses.pop(curr_id, None)

    def _send_notification(self, method: str, params: dict):
        """Send a JSON-RPC notification (no response expected)."""
        if not self._alive or not self._proc:
            return
        payload = json.dumps({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        })
        message = f"Content-Length: {len(payload.encode('utf-8'))}\r\n\r\n{payload}"
        try:
            self._proc.stdin.write(message.encode("utf-8"))
            self._proc.stdin.flush()
        except (OSError, BrokenPipeError):
            self._alive = False

    # ------------------------------------------------------------------
    #  LSP lifecycle
    # ------------------------------------------------------------------

    def _do_initialize(self):
        """Execute the LSP initialize/initialized handshake."""
        resp = self._send_request("initialize", {
            "processId": os.getpid(),
            "rootUri": self.workspace_uri,
            "rootPath": str(self.workspace_root),
            "capabilities": {
                "textDocument": {
                    "definition": {"dynamicRegistration": False},
                    "hover": {"dynamicRegistration": False, "contentFormat": ["markdown", "plaintext"]},
                    "synchronization": {
                        "didOpen": True,
                        "didChange": True,
                        "willSave": False,
                        "didSave": True,
                    },
                },
                "workspace": {
                    "workspaceFolders": True,
                },
            },
            "workspaceFolders": [
                {"uri": self.workspace_uri, "name": self.workspace_root.name}
            ],
        }, timeout=_INIT_TIMEOUT_SECS)

        if resp and "result" in resp:
            self._send_notification("initialized", {})
            self._initialized = True
            logger.info("LSP: initialized for workspace %s", self.workspace_root)
        else:
            logger.warning("LSP: initialize handshake failed for %s", self.workspace_root)
            self._alive = False

    @property
    def is_ready(self) -> bool:
        """True when the server is alive and has completed initialization."""
        return self._alive and self._initialized

    def shutdown(self):
        """Gracefully shut down the language server."""
        if not self._proc:
            return
        self._alive = False

        try:
            self._send_request("shutdown", {}, timeout=2.0)
            self._send_notification("exit", {})
        except Exception:
            pass

        try:
            self._proc.terminate()
            self._proc.wait(timeout=3)
        except Exception:
            try:
                self._proc.kill()
            except Exception:
                pass
        self._proc = None

    def __del__(self):
        try:
            self.shutdown()
        except Exception:
            pass

    # ------------------------------------------------------------------
    #  File synchronization (textDocument/didOpen)
    # ------------------------------------------------------------------

    def _did_open(self, filepath: Path):
        """Notify the server that we opened a file (so it can index it)."""
        uri = filepath.resolve().as_uri()
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        self._send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": "python",
                "version": 1,
                "text": text,
            }
        })

    # ------------------------------------------------------------------
    #  Public API: Go-to-Definition
    # ------------------------------------------------------------------

    def goto_definition(
        self, filepath: str, line: int, character: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Return definition locations for the symbol at the given position.

        Args:
            filepath: Absolute path to the file.
            line: 1-indexed line number (converted to 0-indexed for LSP).
            character: 1-indexed column (converted to 0-indexed for LSP).

        Returns:
            A list of ``{"uri": str, "range": {...}}`` dicts, or None on error.
        """
        if not self.is_ready:
            return None

        fpath = Path(filepath).resolve()
        self._did_open(fpath)

        resp = self._send_request("textDocument/definition", {
            "textDocument": {"uri": fpath.as_uri()},
            "position": {"line": line - 1, "character": character - 1},
        })
        if not resp:
            return None

        result = resp.get("result")
        if result is None:
            return None

        # Normalize: result can be a single Location, a list, or null
        if isinstance(result, dict):
            result = [result]
        if not isinstance(result, list):
            return None

        return result

    # ------------------------------------------------------------------
    #  Public API: Hover (signature + docstring)
    # ------------------------------------------------------------------

    def hover(self, filepath: str, line: int, character: int) -> Optional[str]:
        """Return hover information (signature + docstring) as markdown.

        Args:
            filepath: Absolute path to the file.
            line: 1-indexed line number.
            character: 1-indexed column.

        Returns:
            Markdown string with signature/docs, or None on error.
        """
        if not self.is_ready:
            return None

        fpath = Path(filepath).resolve()
        self._did_open(fpath)

        resp = self._send_request("textDocument/hover", {
            "textDocument": {"uri": fpath.as_uri()},
            "position": {"line": line - 1, "character": character - 1},
        })
        if not resp:
            return None

        result = resp.get("result")
        if not result or "contents" not in result:
            return None

        contents = result["contents"]

        # contents can be: str, {kind, value}, or [str | {kind, value}]
        if isinstance(contents, str):
            return contents
        if isinstance(contents, dict):
            return contents.get("value", "")
        if isinstance(contents, list):
            parts = []
            for item in contents:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(item.get("value", ""))
            return "\n\n".join(parts)

        return None


# ═══════════════════════════════════════════════════════════════════════════
#  Factory: get or create a cached LSPClient for a workspace
# ═══════════════════════════════════════════════════════════════════════════

def get_client(filepath: str) -> Optional[LSPClient]:
    """Return a ready LSPClient for the workspace containing *filepath*.

    Creates and caches one client per workspace root.  Returns None if no
    suitable workspace or language server can be found (non-fatal).
    """
    workspace_root = find_workspace_root(filepath)
    if workspace_root is None:
        logger.debug("LSP: no workspace root found for %s", filepath)
        return None

    key = str(workspace_root)

    with _instances_lock:
        client = _instances.get(key)
        if client and client.is_ready:
            return client
        # Evict dead clients
        if client:
            try:
                client.shutdown()
            except Exception:
                pass
            _instances.pop(key, None)

    # Create outside the lock to avoid blocking other workspaces
    python_exe = find_python_exe(workspace_root)
    client = LSPClient(workspace_root, python_exe)

    if not client.is_ready:
        return None

    with _instances_lock:
        # Double-check: another thread may have created one
        existing = _instances.get(key)
        if existing and existing.is_ready:
            client.shutdown()
            return existing
        _instances[key] = client

    return client


def shutdown_all():
    """Shut down all cached LSP client instances."""
    with _instances_lock:
        for client in _instances.values():
            try:
                client.shutdown()
            except Exception:
                pass
        _instances.clear()


atexit.register(shutdown_all)
