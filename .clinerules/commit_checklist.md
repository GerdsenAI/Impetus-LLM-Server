# Commit Checklist for AI Agents

This checklist ensures consistent commit procedures across all AI agents (Claude, Gemini, etc.) working on the Impetus-LLM-Server project.

## Pre-Commit Checklist

Before EVERY commit, complete these steps:

### 1. ✅ Implementation Complete
- [ ] Feature/fix is fully implemented
- [ ] Code follows project standards
- [ ] No TODOs or placeholder code remains

### 2. ✅ Tests Pass
- [ ] Run relevant tests: `python -m pytest tests/`
- [ ] No test failures
- [ ] No new warnings introduced

### 3. ✅ Update TODO.md
- [ ] Mark completed task with [x]
- [ ] Update MVP section progress specifically
- [ ] Add any new tasks discovered (MVP tasks go in MVP section)
- [ ] Update task priorities if needed
- [ ] Ensure task descriptions are accurate
- [ ] Check if MVP is now complete

### 4. ✅ Code Quality
- [ ] Run formatter: `black src/ gerdsen_ai_server/src/`
- [ ] Run linter: `flake8 src/ gerdsen_ai_server/src/`
- [ ] Fix any issues found

### 5. ✅ Documentation
- [ ] Update relevant docs if needed
- [ ] Add/update code comments
- [ ] Update API docs for new endpoints

## Commit Workflow

```bash
# 1. Complete your implementation
# ... coding ...

# 2. Run tests
python -m pytest tests/

# 3. Update TODO.md
# Open TODO.md and update task status

# 4. Format code
black src/ gerdsen_ai_server/src/

# 5. Stage ALL changes (including TODO.md)
git add -A

# 6. Commit with descriptive message
git commit -m "feat: [Brief description]

- [Detail 1]
- [Detail 2]
- Update TODO.md with task completion"

# 7. IMMEDIATELY continue to next task
# DO NOT wait for permission
# DO NOT ask if you should proceed
```

## Example Commit Messages

### Feature Implementation
```
feat: Implement GGUF model loader

- Add GGUF format detection and validation
- Extract model metadata including quantization
- Support memory-mapped loading for efficiency
- Update TODO.md with completed task
```

### Bug Fix
```
fix: Resolve import error in integrated_mlx_manager

- Change AppleFrameworksIntegration to EnhancedAppleFrameworksIntegration
- Fix prevents server startup failure
- Update TODO.md with bug fix completion
```

### Documentation Update
```
docs: Update commit procedures for autonomous operation

- Add TODO.md update requirement before commits
- Clarify no permission requests during development
- Ensure Gemini compatibility in workflows
- Update TODO.md with documentation task
```

## Important Reminders

1. **MVP FOCUS**: Only work on MVP section tasks until complete
2. **AUTONOMOUS OPERATION**: Continue working without permission requests
3. **TODO.md IS MANDATORY**: Never commit without updating TODO.md (especially MVP section)
4. **COMMIT FREQUENTLY**: After each logical unit of work
5. **CONTINUE IMMEDIATELY**: Start next task right after committing
6. **NO PROMPTING**: Don't ask user if you should continue
7. **MVP = SUCCESS**: When any model loads and works with Cline, MVP is done!

## For Gemini Agents

This checklist applies equally to Gemini agents:
- Follow same commit procedures
- Update TODO.md before every commit
- Work autonomously without permission requests
- Use generic terminology (not Claude-specific)

## Quick Reference

```bash
# The essential sequence:
implement → test → update_todo → format → add → commit → continue
```

Remember: The goal is continuous, uninterrupted progress toward MVP completion!