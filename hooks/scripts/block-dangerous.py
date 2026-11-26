#!/usr/bin/env python3
"""PreToolUse hook: refuse a few obviously destructive Bash commands.

Claude Code sends the pending tool call as JSON on stdin. Exiting with
code 2 blocks the call, and the text written to stderr is shown to Claude
so it can choose another approach. Exit code 0 lets the call through.
"""
import json
import re
import sys

BLOCKED = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?[a-zA-Z]*\s+(/|~|\$HOME)(\s|$)", "recursive delete of / or the home directory"),
    (r"\bgit\s+push\b.*(--force\b|-f\b)(?!-with-lease)", "force push (use --force-with-lease instead)"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard discards uncommitted work"),
    (r":\(\)\s*\{\s*:\|:&\s*\};:", "fork bomb"),
    (r"\bmkfs(\.\w+)?\b", "formatting a filesystem"),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # Never break the session on malformed input.

    command = payload.get("tool_input", {}).get("command", "")
    for pattern, reason in BLOCKED:
        if re.search(pattern, command):
            print(f"starter-kit blocked this command: {reason}.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
