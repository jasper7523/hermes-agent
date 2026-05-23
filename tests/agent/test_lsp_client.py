"""Tests for agent.lsp_client and tools.lsp_tools.

All tests are hermetic — no real Language Server is spawned.  The LSP
subprocess and its I/O are fully mocked.
"""

import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ---------------------------------------------------------------------------
#  Import targets
# ---------------------------------------------------------------------------

from agent.lsp_client import (
    LSPClient,
    find_workspace_root,
    find_python_exe,
    get_client,
    resolve_server_cmd,
    shutdown_all,
    _find_jedi_executable,
    _is_module_installed,
    _auto_install_jedi,
    _instances,
    _instances_lock,
)


# ═══════════════════════════════════════════════════════════════════════════
#  Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def _clear_lsp_singletons():
    """Reset the global LSPClient instance cache between tests."""
    with _instances_lock:
        for client in _instances.values():
            try:
                client.shutdown()
            except Exception:
                pass
        _instances.clear()
    yield
    with _instances_lock:
        for client in _instances.values():
            try:
                client.shutdown()
            except Exception:
                pass
        _instances.clear()


@pytest.fixture
def workspace(tmp_path):
    """Create a minimal workspace with .git marker and venv."""
    (tmp_path / ".git").mkdir()
    venv = tmp_path / "venv" / ("Scripts" if sys.platform == "win32" else "bin")
    venv.mkdir(parents=True)
    python_name = "python.exe" if sys.platform == "win32" else "python"
    python_exe = venv / python_name
    python_exe.write_text("# fake python")
    # Create fake jedi-language-server executable
    jedi_name = "jedi-language-server.exe" if sys.platform == "win32" else "jedi-language-server"
    jedi_exe = venv / jedi_name
    jedi_exe.write_text("# fake jedi")
    # Create a sample Python file
    sample = tmp_path / "example.py"
    sample.write_text("def hello():\n    return 'world'\n\nhello()\n")
    return tmp_path


# ═══════════════════════════════════════════════════════════════════════════
#  Tests: Workspace & Venv Detection
# ═══════════════════════════════════════════════════════════════════════════

class TestFindWorkspaceRoot:
    """Tests for find_workspace_root()."""

    def test_finds_git_root(self, tmp_path):
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / "a" / "b" / "c"
        subdir.mkdir(parents=True)
        result = find_workspace_root(str(subdir / "file.py"))
        assert result == tmp_path

    def test_finds_pyproject_root(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]")
        result = find_workspace_root(str(tmp_path / "src" / "main.py"))
        assert result == tmp_path

    def test_finds_setup_py_root(self, tmp_path):
        (tmp_path / "setup.py").write_text("# setup")
        result = find_workspace_root(str(tmp_path / "pkg" / "mod.py"))
        assert result == tmp_path

    def test_returns_none_no_markers(self, tmp_path):
        # No .git, no pyproject.toml, etc.
        result = find_workspace_root(str(tmp_path / "orphan.py"))
        assert result is None

    def test_finds_nearest_root_not_outermost(self, tmp_path):
        """When nested projects exist, return the nearest (innermost) root."""
        (tmp_path / ".git").mkdir()
        inner = tmp_path / "subproject"
        inner.mkdir()
        (inner / ".git").mkdir()
        result = find_workspace_root(str(inner / "code.py"))
        assert result == inner

    def test_shared_dna_not_a_root_marker(self, tmp_path):
        """shared-dna.md must NOT trigger workspace root detection."""
        sub = tmp_path / "agents" / ".shared"
        sub.mkdir(parents=True)
        (sub / "shared-dna.md").write_text("# dna")
        result = find_workspace_root(str(sub / "scripts" / "tool.py"))
        # Should NOT return 'sub', should walk up further
        assert result != sub


class TestFindPythonExe:
    """Tests for find_python_exe()."""

    def test_finds_venv_python(self, workspace):
        exe = find_python_exe(workspace)
        assert "venv" in str(exe)
        assert exe.exists()

    def test_finds_dot_venv_python(self, tmp_path):
        dot_venv = tmp_path / ".venv" / ("Scripts" if sys.platform == "win32" else "bin")
        dot_venv.mkdir(parents=True)
        name = "python.exe" if sys.platform == "win32" else "python"
        (dot_venv / name).write_text("# fake")
        exe = find_python_exe(tmp_path)
        assert ".venv" in str(exe)

    def test_prefers_venv_over_dot_venv(self, tmp_path):
        for vdir in ("venv", ".venv"):
            d = tmp_path / vdir / ("Scripts" if sys.platform == "win32" else "bin")
            d.mkdir(parents=True)
            name = "python.exe" if sys.platform == "win32" else "python"
            (d / name).write_text("# fake")
        exe = find_python_exe(tmp_path)
        assert "venv" in str(exe) and ".venv" not in str(exe)

    def test_fallback_to_sys_executable(self, tmp_path):
        """No venv → falls back to sys.executable."""
        exe = find_python_exe(tmp_path)
        assert exe == Path(sys.executable)


class TestFindJediExecutable:
    """Tests for _find_jedi_executable()."""

    def test_finds_in_scripts_dir(self, workspace):
        venv_dir = workspace / "venv" / ("Scripts" if sys.platform == "win32" else "bin")
        python_exe = venv_dir / ("python.exe" if sys.platform == "win32" else "python")
        result = _find_jedi_executable(python_exe)
        assert result is not None
        assert "jedi-language-server" in result.name

    def test_returns_none_when_not_installed(self, tmp_path):
        fake_python = tmp_path / ("python.exe" if sys.platform == "win32" else "python")
        fake_python.write_text("# fake")
        with patch("shutil.which", return_value=None):
            result = _find_jedi_executable(fake_python)
        assert result is None


class TestIsModuleInstalled:
    """Tests for _is_module_installed()."""

    def test_installed_module(self):
        """json is always available."""
        result = _is_module_installed(Path(sys.executable), "json")
        assert result is True

    def test_missing_module(self):
        result = _is_module_installed(Path(sys.executable), "nonexistent_module_xyz_123")
        assert result is False


class TestResolveServerCmd:
    """Tests for resolve_server_cmd()."""

    def test_jedi_when_available(self, workspace):
        python_exe = find_python_exe(workspace)
        cmd = resolve_server_cmd(workspace, python_exe)
        assert cmd is not None
        assert "jedi-language-server" in cmd[0]

    def test_pyright_when_env_set(self, workspace, monkeypatch):
        monkeypatch.setenv("USE_PYRIGHT", "1")
        python_exe = find_python_exe(workspace)
        with patch("shutil.which", return_value="/usr/bin/pyright-langserver"):
            cmd = resolve_server_cmd(workspace, python_exe)
        assert cmd == ["/usr/bin/pyright-langserver", "--stdio"]

    def test_pyright_fallback_to_jedi(self, workspace, monkeypatch):
        """USE_PYRIGHT=1 but pyright not found → falls back to jedi."""
        monkeypatch.setenv("USE_PYRIGHT", "1")
        python_exe = find_python_exe(workspace)
        with patch("shutil.which", return_value=None):
            cmd = resolve_server_cmd(workspace, python_exe)
        # Should still find jedi-language-server
        assert cmd is not None
        assert "jedi-language-server" in cmd[0]

    def test_returns_none_when_nothing_available(self, tmp_path):
        fake_python = tmp_path / ("python.exe" if sys.platform == "win32" else "python")
        fake_python.write_text("# fake")
        with patch("shutil.which", return_value=None), \
             patch("agent.lsp_client._is_module_installed", return_value=False), \
             patch("agent.lsp_client._auto_install_jedi", return_value=False):
            cmd = resolve_server_cmd(tmp_path, fake_python)
        assert cmd is None


# ═══════════════════════════════════════════════════════════════════════════
#  Tests: LSPClient (mocked subprocess)
# ═══════════════════════════════════════════════════════════════════════════

def _make_lsp_response(msg_id, result):
    """Build a raw LSP response bytes with Content-Length header."""
    payload = json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result})
    return f"Content-Length: {len(payload.encode('utf-8'))}\r\n\r\n{payload}".encode("utf-8")


class TestLSPClientTransport:
    """Tests for JSON-RPC transport layer."""

    def test_send_request_and_receive_response(self, workspace):
        """Verify that send_request correctly sends and recv_loop dispatches."""
        # Prepare mock initialize response + a goto_definition response
        init_result = {"capabilities": {"textDocumentSync": 1}}
        init_resp = _make_lsp_response(1, init_result)
        # We need the recv thread to read from stdout
        # Use a pipe to simulate LSP stdout
        read_fd, write_fd = os.pipe()
        read_file = os.fdopen(read_fd, "rb", buffering=0)
        write_file = os.fdopen(write_fd, "wb", buffering=0)

        stdin_read_fd, stdin_write_fd = os.pipe()
        stdin_read = os.fdopen(stdin_read_fd, "rb")
        stdin_write = os.fdopen(stdin_write_fd, "wb", buffering=0)

        mock_proc = MagicMock()
        mock_proc.stdout = read_file
        mock_proc.stdin = stdin_write
        mock_proc.stderr = MagicMock()
        mock_proc.poll.return_value = None

        with patch("agent.lsp_client.resolve_server_cmd", return_value=["fake-lsp"]), \
             patch("subprocess.Popen", return_value=mock_proc):

            client = LSPClient.__new__(LSPClient)
            client.workspace_root = workspace
            client.workspace_uri = workspace.as_uri()
            client._python_exe = Path(sys.executable)
            client._msg_id = 0
            client._responses = {}
            client._lock = threading.Lock()
            client._alive = True
            client._proc = mock_proc
            client._initialized = False

            # Start recv thread
            client._recv_thread = threading.Thread(
                target=client._recv_loop, name="test-recv", daemon=True
            )
            client._recv_thread.start()

            # Write the init response to the mock stdout
            write_file.write(init_resp)
            write_file.flush()

            # Manually call _do_initialize — it sends id=1
            client._do_initialize()

            assert client._initialized is True

            # Cleanup
            client._alive = False
            write_file.close()
            stdin_write.close()
            stdin_read.close()


class TestLSPClientGotoDefinition:
    """Tests for the goto_definition public API."""

    def test_returns_none_when_not_ready(self, workspace):
        client = LSPClient.__new__(LSPClient)
        client._alive = False
        client._initialized = False
        result = client.goto_definition(str(workspace / "example.py"), 1, 1)
        assert result is None

    def test_parses_single_location(self, workspace):
        client = LSPClient.__new__(LSPClient)
        client._alive = True
        client._initialized = True
        client._proc = MagicMock()
        client._msg_id = 0
        client._responses = {}
        client._lock = threading.Lock()
        client.workspace_root = workspace
        client.workspace_uri = workspace.as_uri()

        location = {
            "uri": f"file:///{str(workspace / 'example.py').replace(os.sep, '/')}",
            "range": {"start": {"line": 0, "character": 4}, "end": {"line": 0, "character": 9}},
        }

        with patch.object(client, "_send_request", return_value={"result": location}), \
             patch.object(client, "_did_open"):
            result = client.goto_definition(str(workspace / "example.py"), 4, 1)
        assert result is not None
        assert len(result) == 1
        assert result[0]["range"]["start"]["line"] == 0

    def test_parses_list_of_locations(self, workspace):
        client = LSPClient.__new__(LSPClient)
        client._alive = True
        client._initialized = True
        client._proc = MagicMock()
        client._msg_id = 0
        client._responses = {}
        client._lock = threading.Lock()
        client.workspace_root = workspace
        client.workspace_uri = workspace.as_uri()

        locations = [
            {"uri": "file:///a.py", "range": {"start": {"line": 10, "character": 0}}},
            {"uri": "file:///b.py", "range": {"start": {"line": 20, "character": 0}}},
        ]

        with patch.object(client, "_send_request", return_value={"result": locations}), \
             patch.object(client, "_did_open"):
            result = client.goto_definition(str(workspace / "example.py"), 4, 1)
        assert len(result) == 2


class TestLSPClientHover:
    """Tests for the hover public API."""

    def test_returns_none_when_not_ready(self, workspace):
        client = LSPClient.__new__(LSPClient)
        client._alive = False
        client._initialized = False
        result = client.hover(str(workspace / "example.py"), 1, 1)
        assert result is None

    def test_parses_markup_content(self, workspace):
        client = LSPClient.__new__(LSPClient)
        client._alive = True
        client._initialized = True
        client._proc = MagicMock()
        client._msg_id = 0
        client._responses = {}
        client._lock = threading.Lock()
        client.workspace_root = workspace
        client.workspace_uri = workspace.as_uri()

        hover_result = {
            "contents": {"kind": "markdown", "value": "def hello() -> str"},
            "range": {"start": {"line": 0, "character": 4}},
        }

        with patch.object(client, "_send_request", return_value={"result": hover_result}), \
             patch.object(client, "_did_open"):
            result = client.hover(str(workspace / "example.py"), 1, 5)
        assert result == "def hello() -> str"

    def test_parses_plain_string_content(self, workspace):
        client = LSPClient.__new__(LSPClient)
        client._alive = True
        client._initialized = True
        client._proc = MagicMock()
        client._msg_id = 0
        client._responses = {}
        client._lock = threading.Lock()
        client.workspace_root = workspace
        client.workspace_uri = workspace.as_uri()

        with patch.object(client, "_send_request",
                          return_value={"result": {"contents": "plain text"}}), \
             patch.object(client, "_did_open"):
            result = client.hover(str(workspace / "example.py"), 1, 5)
        assert result == "plain text"

    def test_parses_list_content(self, workspace):
        client = LSPClient.__new__(LSPClient)
        client._alive = True
        client._initialized = True
        client._proc = MagicMock()
        client._msg_id = 0
        client._responses = {}
        client._lock = threading.Lock()
        client.workspace_root = workspace
        client.workspace_uri = workspace.as_uri()

        with patch.object(client, "_send_request",
                          return_value={"result": {"contents": ["part1", {"value": "part2"}]}}), \
             patch.object(client, "_did_open"):
            result = client.hover(str(workspace / "example.py"), 1, 5)
        assert "part1" in result
        assert "part2" in result


# ═══════════════════════════════════════════════════════════════════════════
#  Tests: Factory (get_client)
# ═══════════════════════════════════════════════════════════════════════════

class TestGetClient:
    """Tests for the get_client() factory function."""

    def test_returns_none_for_unknown_workspace(self, tmp_path):
        """No .git or project markers → None."""
        result = get_client(str(tmp_path / "orphan.py"))
        assert result is None

    def test_caches_client_per_workspace(self, workspace):
        """Two calls with files in the same workspace return same client."""
        with patch("agent.lsp_client.LSPClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.is_ready = True
            MockClient.return_value = mock_instance

            c1 = get_client(str(workspace / "a.py"))
            c2 = get_client(str(workspace / "b.py"))
            assert c1 is c2
            # Constructor called only once
            MockClient.assert_called_once()

    def test_evicts_dead_client(self, workspace):
        """A dead client gets replaced on next call."""
        with patch("agent.lsp_client.LSPClient") as MockClient:
            dead = MagicMock()
            dead.is_ready = False

            alive = MagicMock()
            alive.is_ready = True

            MockClient.side_effect = [dead, alive]

            c1 = get_client(str(workspace / "a.py"))
            assert c1 is None  # dead → returned None

            c2 = get_client(str(workspace / "a.py"))
            assert c2 is alive


class TestShutdownAll:
    """Tests for shutdown_all()."""

    def test_clears_instance_cache(self, workspace):
        mock_client = MagicMock()
        mock_client.is_ready = True
        with _instances_lock:
            _instances[str(workspace)] = mock_client
        shutdown_all()
        with _instances_lock:
            assert len(_instances) == 0
        mock_client.shutdown.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════
#  Tests: tools/lsp_tools.py
# ═══════════════════════════════════════════════════════════════════════════

from tools.lsp_tools import (
    lsp_goto_definition,
    lsp_get_signature,
    _uri_to_path,
    _get_context_lines,
)


class TestUriToPath:
    """Tests for _uri_to_path()."""

    def test_windows_uri(self):
        result = _uri_to_path("file:///C:/Users/test/file.py")
        assert result == "C:/Users/test/file.py"

    def test_unix_uri(self):
        result = _uri_to_path("file:///home/user/file.py")
        assert result == "home/user/file.py"

    def test_encoded_uri(self):
        result = _uri_to_path("file:///C:/path%20with%20spaces/file.py")
        assert "path with spaces" in result

    def test_passthrough_non_file_uri(self):
        result = _uri_to_path("https://example.com")
        assert result == "https://example.com"


class TestGetContextLines:
    """Tests for _get_context_lines()."""

    def test_reads_lines_around_target(self, workspace):
        sample = workspace / "example.py"
        result = _get_context_lines(str(sample), 0, n=5)
        assert "def hello" in result
        assert " → " in result  # marker on line 0

    def test_returns_empty_for_missing_file(self):
        result = _get_context_lines("/nonexistent/path.py", 0)
        assert result == ""


class TestLspGotoDefinitionTool:
    """Tests for lsp_goto_definition() tool handler."""

    def test_returns_error_when_no_client(self):
        with patch("agent.lsp_client.get_client", return_value=None):
            result = json.loads(lsp_goto_definition("/fake/path.py", 1, 1))
        assert "error" in result

    def test_returns_definitions_on_success(self, workspace):
        mock_client = MagicMock()
        mock_client.goto_definition.return_value = [
            {
                "uri": f"file:///{str(workspace / 'example.py').replace(os.sep, '/')}",
                "range": {"start": {"line": 0, "character": 4}, "end": {"line": 0, "character": 9}},
            }
        ]
        with patch("agent.lsp_client.get_client", return_value=mock_client):
            result = json.loads(lsp_goto_definition(str(workspace / "example.py"), 4, 1))
        assert result["success"] is True
        assert result["count"] == 1
        assert result["definitions"][0]["line"] == 1  # 0-indexed → 1-indexed


class TestLspGetSignatureTool:
    """Tests for lsp_get_signature() tool handler."""

    def test_returns_error_when_no_client(self):
        with patch("agent.lsp_client.get_client", return_value=None):
            result = json.loads(lsp_get_signature("/fake/path.py", 1, 1))
        assert "error" in result

    def test_returns_signature_on_success(self, workspace):
        mock_client = MagicMock()
        mock_client.hover.return_value = "def hello() -> str\n---\nReturns world."
        with patch("agent.lsp_client.get_client", return_value=mock_client):
            result = json.loads(lsp_get_signature(str(workspace / "example.py"), 1, 5))
        assert result["success"] is True
        assert "def hello" in result["signature"]

    def test_returns_not_found_when_hover_empty(self, workspace):
        mock_client = MagicMock()
        mock_client.hover.return_value = None
        with patch("agent.lsp_client.get_client", return_value=mock_client):
            result = json.loads(lsp_get_signature(str(workspace / "example.py"), 1, 5))
        assert result["success"] is False
