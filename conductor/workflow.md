# Workflow - gemini-tools

## Operational Rules
1. Every executable CLI script must be placed under `bin/` and start with `#!/usr/bin/env -S uv run`.
2. Every script edit must be accompanied by an update to `skills/how-to-use-gemini-tools/SKILL.md`.
3. All output paths in metadata JSON sidecars must be normalized with `to_tilde_path()`.
4. Git commit messages must use single quotes `git commit -m '...'`.
5. Maintain `Justfile` tasks with default target `list -> just -l`.
