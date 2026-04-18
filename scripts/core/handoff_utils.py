from __future__ import annotations

import os
import platform
import socket
import sys
from pathlib import Path


def add_common_handoff_args(parser) -> None:
    parser.add_argument("--agent-id", help="Agent id that produced this handoff")
    parser.add_argument("--model-id", help="Model id used for this stage")
    parser.add_argument("--session-key", help="Session key or lane identifier")
    parser.add_argument("--channel", help="Origin channel, for example telegram")
    parser.add_argument("--tool-route", help="Tool route or execution surface used")
    parser.add_argument("--exec-command", help="Direct command used for the main stage action")
    parser.add_argument("--workdir", help="Working directory used during execution")
    parser.add_argument("--source-task", help="Short human-readable task description")
    parser.add_argument(
        "--input-files", nargs="*", default=[],
        help="Key upstream input files used by this stage"
    )
    parser.add_argument(
        "--notes", nargs="*", default=[],
        help="Extra note strings to preserve in the handoff"
    )


def _env_or_arg(arg_value: str | None, env_keys: list[str]) -> str | None:
    if arg_value:
        return arg_value
    for key in env_keys:
        value = os.environ.get(key)
        if value:
            return value
    return None


def build_handoff_provenance(args, script_path: Path, *, output_files: list[str] | None = None) -> dict:
    return {
        "runtime": {
            "agent_id": _env_or_arg(getattr(args, "agent_id", None), ["AGENT_ID", "OPENCLAW_AGENT_ID"]),
            "model_id": _env_or_arg(getattr(args, "model_id", None), ["MODEL_ID", "OPENCLAW_MODEL_ID"]),
            "session_key": _env_or_arg(getattr(args, "session_key", None), ["SESSION_KEY", "OPENCLAW_SESSION_KEY"]),
            "channel": _env_or_arg(getattr(args, "channel", None), ["CHANNEL", "OPENCLAW_CHANNEL"]),
            "tool_route": _env_or_arg(getattr(args, "tool_route", None), ["TOOL_ROUTE", "OPENCLAW_TOOL_ROUTE"]),
        },
        "execution": {
            "script": str(script_path),
            "argv": sys.argv[1:],
            "workdir": getattr(args, "workdir", None) or os.getcwd(),
            "exec_command": getattr(args, "exec_command", None),
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python": sys.version.split()[0],
        },
        "data_flow": {
            "source_task": getattr(args, "source_task", None),
            "input_files": getattr(args, "input_files", []) or [],
            "output_files": output_files or [],
        },
    }
