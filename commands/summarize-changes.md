---
description: Summarize the uncommitted changes in this repository
argument-hint: "[focus area, optional]"
allowed-tools: Bash(git status:*), Bash(git diff:*)
---

## Context

- Status: !`git status --short`
- Diff (staged and unstaged): !`git diff HEAD --stat`

## Task

Summarize the changes above in plain language for a teammate:

1. One sentence on the overall purpose of the change.
2. A short bullet list of what changed, grouped by area.
3. Anything that looks unfinished or risky.

If the user gave a focus area, pay most attention to it: $ARGUMENTS
