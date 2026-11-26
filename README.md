# starter-kit

A starter Claude Code plugin. It includes one working example of each kind of plugin part, so you can copy the pattern, rename it and build your own.

| Part | File | What it does |
| --- | --- | --- |
| Slash command | `commands/summarize-changes.md` | `/starter-kit:summarize-changes [focus]` summarizes your uncommitted git changes. |
| Skill | `skills/commit-messages/SKILL.md` | Claude writes commit messages in the Conventional Commits format whenever it commits. |
| Hook | `hooks/hooks.json`, `hooks/scripts/block-dangerous.py` | Blocks destructive shell commands such as `rm -rf /`, `git reset --hard` and plain force pushes. |
| Subagent | `agents/code-reviewer.md` | A `code-reviewer` agent that reviews recent changes for bugs, clarity and missing tests. |
| MCP server | `.mcp.json`, `mcp/server.js` | Adds two tools, `current_time` and `word_count`, with no npm dependencies. |

## Requirements

- Claude Code
- `python3` (for the hook) and `node` 18 or newer (for the MCP server)

## Try it locally

From the folder that contains this repository:

```bash
claude --plugin-dir ./basic-template-
```

Then, inside Claude Code:

- Run `/starter-kit:summarize-changes` in any git repository.
- Ask Claude to "review my latest changes with the code-reviewer agent".
- Ask "what time is it in Tokyo?" to use the MCP tool.
- Run `/plugin` to see the plugin and its parts.

## Layout

```
.claude-plugin/plugin.json   Plugin manifest: name, version, description
commands/                    Slash commands, one Markdown file each
skills/<name>/SKILL.md       Skills Claude loads when a task matches
agents/                      Subagents, one Markdown file each
hooks/hooks.json             Hook configuration
hooks/scripts/               Scripts the hooks run
.mcp.json                    MCP servers the plugin starts
mcp/server.js                The example MCP server
```

Paths inside the plugin use `${CLAUDE_PLUGIN_ROOT}`, which Claude Code sets to the plugin's installed location.

## Make it your own

1. Change `name`, `description` and `author` in `.claude-plugin/plugin.json`.
2. Delete the parts you don't need, and add new files next to the examples.
3. Run `claude plugin validate .` to check your changes.
4. When you want to share it, add it to a marketplace (a repository with `.claude-plugin/marketplace.json`) and install it with `/plugin marketplace add <owner>/<repo>`.

## License

MIT
