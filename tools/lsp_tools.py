"""LSP Tools — Agent-facing go-to-definition and signature/hover tools.

Uses ``agent.lsp_client`` to communicate with a per-workspace Language Server.
All failures are non-fatal: the tool returns a helpful error string directing
the agent to fall back to ``search_files`` or ``read_file``.

Toolset: ``lsp``  (opt-in, not in _HERMES_CORE_TOOLS by default).

Author: N7 Hermes Agent
"""

import json
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import unquote as _url_unquote

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Availability check
# ---------------------------------------------------------------------------

def _check_lsp_available() -> bool:
    """Return True if the LSP toolset should be offered to the model.

    Currently always True — the tools handle missing servers gracefully at
    call time.  This could later gate on a config flag like ``lsp.enabled``.
    """
    return True


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _get_context_lines(filepath: str, start_line: int, n: int = 10) -> str:
    """Read up to *n* lines around *start_line* from *filepath*.

    Returns a formatted string with line numbers, or an empty string on error.
    *start_line* is 0-indexed (as returned by LSP).
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        begin = max(0, start_line - 2)
        end = min(len(lines), start_line + n)
        parts = []
        for i in range(begin, end):
            marker = " → " if i == start_line else "   "
            parts.append(f"{marker}{i + 1:4d} │ {lines[i]}")
        return "\n".join(parts)
    except Exception:
        return ""


def _uri_to_path(uri: str) -> str:
    """Convert a file:// URI to an absolute path string."""
    if uri.startswith("file:///"):
        # Windows: file:///C:/foo → C:/foo
        raw = uri[8:]  # strip file:///
        return _url_unquote(raw)
    if uri.startswith("file://"):
        return _url_unquote(uri[7:])
    return uri


# ---------------------------------------------------------------------------
#  Tool handlers
# ---------------------------------------------------------------------------

def lsp_goto_definition(path: str, line: int, character: int, task_id: str = None) -> str:
    """Execute textDocument/definition and return results as JSON."""
    try:
        from agent.lsp_client import get_client
    except ImportError:
        return tool_error(
            "LSP client module not available. "
            "Use search_files to locate definitions instead."
        )

    client = get_client(path)
    if client is None:
        return tool_error(
            f"No LSP server available for {path}. "
            "Use search_files to locate definitions instead."
        )

    locations = client.goto_definition(path, line, character)
    if not locations:
        return tool_result(
            success=False,
            message=f"No definition found at {Path(path).name}:{line}:{character}. "
                    "Try search_files as fallback.",
        )

    results = []
    for loc in locations:
        uri = loc.get("uri", "")
        range_data = loc.get("range", {})
        start = range_data.get("start", {})
        def_line = start.get("line", 0)  # 0-indexed
        def_char = start.get("character", 0)

        def_path = _uri_to_path(uri)
        context = _get_context_lines(def_path, def_line)

        results.append({
            "path": def_path,
            "line": def_line + 1,  # convert to 1-indexed for agent
            "character": def_char + 1,
            "context": context,
        })

    return tool_result(
        success=True,
        definitions=results,
        count=len(results),
    )


def lsp_get_signature(path: str, line: int, character: int, task_id: str = None) -> str:
    """Execute textDocument/hover and return signature + docstring."""
    try:
        from agent.lsp_client import get_client
    except ImportError:
        return tool_error(
            "LSP client module not available. "
            "Use read_file with StartLine/EndLine to check function signatures."
        )

    client = get_client(path)
    if client is None:
        return tool_error(
            f"No LSP server available for {path}. "
            "Use read_file with StartLine/EndLine to check function signatures."
        )

    hover_text = client.hover(path, line, character)
    if not hover_text:
        return tool_result(
            success=False,
            message=f"No hover information at {Path(path).name}:{line}:{character}. "
                    "Try read_file with StartLine/EndLine as fallback.",
        )

    return tool_result(
        success=True,
        signature=hover_text,
        source=f"{Path(path).name}:{line}:{character}",
    )


# ---------------------------------------------------------------------------
#  Handler wrappers (match registry.register handler signature)
# ---------------------------------------------------------------------------

def _handle_goto_definition(args: dict, **kwargs) -> str:
    return lsp_goto_definition(
        path=args.get("path", ""),
        line=args.get("line", 1),
        character=args.get("character", 1),
        task_id=kwargs.get("task_id"),
    )


def _handle_get_signature(args: dict, **kwargs) -> str:
    return lsp_get_signature(
        path=args.get("path", ""),
        line=args.get("line", 1),
        character=args.get("character", 1),
        task_id=kwargs.get("task_id"),
    )


# ---------------------------------------------------------------------------
#  Schemas
# ---------------------------------------------------------------------------

LSP_GOTO_DEFINITION_SCHEMA = {
    "name": "lsp_goto_definition",
    "description": (
        "Jump to the definition of a symbol (function, class, variable) at the "
        "given position in a Python file. Returns the file path, line number, "
        "and surrounding code context of where the symbol is defined. "
        "More precise than search_files for navigating code — use this when "
        "you know the exact file and position of a symbol reference."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to the Python file containing the symbol reference.",
            },
            "line": {
                "type": "integer",
                "description": "1-indexed line number where the symbol appears.",
            },
            "character": {
                "type": "integer",
                "description": "1-indexed column number within the line (position of the symbol name).",
            },
        },
        "required": ["path", "line", "character"],
    },
}

LSP_GET_SIGNATURE_SCHEMA = {
    "name": "lsp_get_signature",
    "description": (
        "Get the function signature, parameter types, return type, and docstring "
        "for a symbol at the given position in a Python file. "
        "Use this instead of read_file when you only need to know a function's "
        "parameters and usage — it returns just the signature and docs without "
        "loading the entire file into context."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to the Python file containing the symbol.",
            },
            "line": {
                "type": "integer",
                "description": "1-indexed line number where the symbol appears.",
            },
            "character": {
                "type": "integer",
                "description": "1-indexed column number within the line.",
            },
        },
        "required": ["path", "line", "character"],
    },
}

# ---------------------------------------------------------------------------
#  Registration
# ---------------------------------------------------------------------------

registry.register(
    name="lsp_goto_definition",
    toolset="lsp",
    schema=LSP_GOTO_DEFINITION_SCHEMA,
    handler=_handle_goto_definition,
    check_fn=_check_lsp_available,
    emoji="🔍",
)

registry.register(
    name="lsp_get_signature",
    toolset="lsp",
    schema=LSP_GET_SIGNATURE_SCHEMA,
    handler=_handle_get_signature,
    check_fn=_check_lsp_available,
    emoji="📝",
)
