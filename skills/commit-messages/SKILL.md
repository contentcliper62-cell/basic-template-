---
name: commit-messages
description: Write git commit messages in the Conventional Commits format. Use whenever you are about to create a git commit or the user asks for a commit message.
---

# Commit messages

Write every commit message in the Conventional Commits format:

```
<type>(<optional scope>): <summary>

<optional body>
```

## Rules

- **type** is one of: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`.
- **summary** is in the imperative mood ("add", not "added"), lowercase, no trailing period, 72 characters at most.
- **body** explains *why* the change was made, wrapped at 72 characters. Leave it out for trivial changes.
- Mark breaking changes with `!` after the type (`feat!: ...`) and a `BREAKING CHANGE:` line in the body.

## Examples

```
feat(auth): add password reset by email
```

```
fix: stop crash when config file is empty

The loader assumed at least one key and indexed into an empty dict.
```
