---
phase: 1
title: "Skeleton & Install"
status: done
priority: P1
effort: "1d"
dependencies: []
---

# Phase 1: Skeleton & Install

## Overview

Bootstrap repo skeleton + Antigravity integration files. After this phase, `/visual-prompt` is autocompletable in Antigravity (even if the workflow is still stub). Foundation for all later phases.

## Context Links

- Reference codebase: `/home/dung/VIBE_CODING/Grammar_check/chinese-novel-proofreader/` (SKILL.md, gemini-extension.json, antigravity/INSTALL.md, commands/proofread.toml)
- Brainstorm §5 (file layout), §11 (phase preview)

## Requirements

**Functional:**
- Antigravity recognizes `visual-prompt` skill (SKILL.md loadable by extension)
- `/visual-prompt` slash command autocompletes in chat
- One-shot installer for Linux/Mac (`setup.sh`) and Windows (`setup.bat` with copy fallback)
- `.gitignore` excludes cache directories

**Non-functional:**
- SKILL.md ≤200 lines (Antigravity context budget)
- Install completes in <10s
- Symlink survives skill updates (no manual re-link needed unless renaming)

## Architecture

**Install paths verified 2026-05-22 against `/cli-tran` skill (working reference on this machine):**

- Extension root: `~/.gemini/extensions/visual-prompt/` (contains `gemini-extension.json`, `commands/`, `skills/visual-prompt/`)
- Slash command symlink: `~/.gemini/commands/visual-prompt.toml` → `~/.gemini/extensions/visual-prompt/commands/visual-prompt.toml`
- Antigravity CLI plugin registry (optional, adds skill to Antigravity-specific discovery): `~/.gemini/antigravity-cli/plugins/visual-prompt/plugin.json` (minimal `{"name": "visual-prompt"}`) + `~/.gemini/antigravity-cli/plugins/visual-prompt/skills/visual-prompt/SKILL.md` (symlink to extension's SKILL.md)

**Repo layout:**
```
visual-prompt/
├── SKILL.md                       # Loaded by extension — frontmatter + workflow overview
├── gemini-extension.json          # 4 fields: name/version/description/contextFileName
├── commands/
│   └── visual-prompt.toml         # description + 6-step prompt block
├── skills/visual-prompt/          # Mirror for skill discovery (symlink target points here)
│   └── SKILL.md                   # symlink → ../../SKILL.md
├── plugin.json                    # Antigravity CLI plugin manifest (just {"name": "visual-prompt"})
├── antigravity/
│   └── INSTALL.md                 # Cross-platform install guide
├── setup.sh                       # Linux/Mac symlink installer
├── setup.bat                      # Windows installer (admin symlink + copy fallback)
├── .gitignore                     # exclude .work/, __pycache__/, *.pyc
└── README.md                      # Skeleton VN quick start (Phase 6 expands)
```

**Install symlinks created by setup.sh:**
1. `~/.gemini/extensions/visual-prompt` → `<repo>` (whole repo as extension)
2. `~/.gemini/commands/visual-prompt.toml` → `<repo>/commands/visual-prompt.toml`
3. `~/.gemini/antigravity-cli/plugins/visual-prompt` → `<repo>` (registers as Antigravity plugin)

## Related Code Files

### Create
- `SKILL.md` — frontmatter (name, version 0.1.0, description, license MIT) + 6-step overview body
- `gemini-extension.json` — `{"name": "visual-prompt", "version": "0.1.0", "description": "...", "contextFileName": "SKILL.md"}`
- `commands/visual-prompt.toml` — `description = "..."` + `prompt = """6-step workflow..."""` (full prompt in Phase 4)
- `skills/visual-prompt/SKILL.md` — symlink to root SKILL.md (skill discovery convention)
- `plugin.json` — `{"name": "visual-prompt"}` (Antigravity CLI plugin registry minimal manifest)
- `antigravity/INSTALL.md` — Linux/Mac/Windows symlink + copy fallback instructions
- `setup.sh` — 3 symlinks (verified pattern from `/cli-tran`):
  ```bash
  mkdir -p ~/.gemini/extensions ~/.gemini/commands ~/.gemini/antigravity-cli/plugins
  ln -sfn "$(pwd)" ~/.gemini/extensions/visual-prompt
  ln -sf "$(pwd)/commands/visual-prompt.toml" ~/.gemini/commands/visual-prompt.toml
  ln -sfn "$(pwd)" ~/.gemini/antigravity-cli/plugins/visual-prompt
  ```
- `setup.bat` — PowerShell-equivalent with admin symlink + copy fallback for non-admin
- `.gitignore` — `.work/`, `__pycache__/`, `*.pyc`, `.DS_Store`, output `_visuals/` example dirs

### Modify
- (none — greenfield)

### Delete
- (none)

## Implementation Steps

1. **Write SKILL.md** with frontmatter (name: visual-prompt, version: 0.1.0, license: MIT) + body containing: philosophy (LLM-driven, Python minimal), workflow overview (6 steps with 1-line summaries), input/output spec, limitations (Vietnamese proofread only, no đam mỹ/ngôn tình)
2. **Write gemini-extension.json** — exact 4 fields from proofreader pattern, adjusted for `visual-prompt`
3. **Write commands/visual-prompt.toml** with `description = "..."` and `prompt = """..."""` (stub `prompt` for now — Phase 4 fills detailed 6-step workflow)
4. **Create antigravity/skills/visual-prompt/** as symlink target — Phase 1 sets directory; Phase 4 prompt files land here
5. **Write antigravity/INSTALL.md** copying proofreader structure but adjust paths + skill name; include Linux/Mac symlink + Windows admin symlink + Windows non-admin copy fallback sections
6. **Write setup.sh** — POSIX shell, idempotent (`ln -sf`), prints success/failure clearly. Detects `~/.gemini/` parent missing → `mkdir -p`. Exit non-zero on failure.
7. **Write setup.bat** — PowerShell wrapper, tries `New-Item -ItemType SymbolicLink` first, falls back to `Copy-Item -Recurse` with WARNING about manual re-sync on update
8. **Write .gitignore** — minimal entries
9. **Write README.md skeleton** — 30-line VN quick start: install command + 1-line usage + link to HUONG-DAN-SU-DUNG.md (Phase 6 creates full guide)
10. **Run setup.sh locally** to verify symlinks resolve correctly
11. **Test in Antigravity:** open IDE, type `/` → confirm `visual-prompt` autocompletes

## Todo List

- [ ] SKILL.md written (frontmatter + 6-step overview)
- [ ] gemini-extension.json written
- [ ] commands/visual-prompt.toml stub written (Phase 4 fills prompt body)
- [ ] antigravity/skills/visual-prompt/ directory exists
- [ ] antigravity/INSTALL.md written (Linux/Mac + Windows admin + Windows non-admin)
- [ ] setup.sh written + executable bit (`chmod +x`)
- [ ] setup.bat written
- [ ] .gitignore written
- [ ] README.md skeleton written
- [ ] setup.sh runs successfully on local Linux
- [ ] Antigravity autocompletes `/visual-prompt`

## Success Criteria

- [ ] `bash setup.sh` exits 0 on Linux
- [ ] `~/.gemini/extensions/visual-prompt` is symlink to repo
- [ ] `~/.gemini/commands/visual-prompt.toml` is symlink to repo's `commands/visual-prompt.toml`
- [ ] `~/.gemini/antigravity-cli/plugins/visual-prompt` is symlink to repo
- [ ] Opening Antigravity → `/` → `visual-prompt` shows up
- [ ] Selecting `/visual-prompt` shows the (stub) description from TOML

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Windows users without admin can't symlink | `setup.bat` falls back to `Copy-Item`; INSTALL.md flags re-sync requirement |
| Antigravity changes context file convention | Pin to `contextFileName: "SKILL.md"` (current v3.6 pattern); Phase 5 verifies |
| SKILL.md exceeds context budget | Cap at 200 lines; defer details to references/ (Phase 3) |
| Repo path has spaces ("1. OTHERS") | `setup.sh` quotes `$(pwd)`; tested with space-containing path |

## Security Considerations

- No secrets in any file (all paths are local user-relative)
- Setup scripts don't `sudo` or write outside `~/.gemini/`
- `.gitignore` excludes `.work/` (may contain partial novel text)

## Next Steps

- **Unlocks:** Phase 2 (Python scripts can be added to `scripts/` dir) + Phase 3 (references/ dir exists)
- **Verification needed:** Manual Antigravity test (autocomplete check)
