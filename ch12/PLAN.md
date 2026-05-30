# Nanocode (ch12) Improvement Plan

## Goal
Upgrade nanocode.py from a minimal single-file agent into a more powerful, reliable, and extensible coding agent while preserving its simplicity.

---

# 1. Core Architectural Improvements

## 1.1 Modularization (Optional but Recommended)
- Split large functions logically (tools, LLM, UI, memory)
- Keep single-file option via sections or flags
- Improve readability and testability

## 1.2 Typed Interfaces
- Add type hints across all functions
- Define Tool schema with TypedDict or dataclass
- Improves reliability + IDE support

## 1.3 Config Layer
- Add config (env + file fallback)
- Model selection, temperature, timeout, etc.

---

# 2. Agent Intelligence Improvements

## 2.1 Better Planning Layer
- Add explicit planning step before execution
- Maintain PLAN.md iteration loop
- Allow agent to revise plan mid-task

## 2.2 Tool Selection Optimization
- Add tool descriptions + examples
- Bias toward fewer unnecessary tool calls
- Add tool usage scoring heuristics

## 2.3 Multi-Step Task Tracking
- Add task state object:
  - goal
  - steps
  - completed steps
- Improves long-running tasks (like building apps)

---

# 3. Memory System Upgrades

## 3.1 Structured Memory
- Replace plain markdown scratchpad with sections:
  - goals
  - decisions
  - bugs encountered
  - fixes

## 3.2 Retrieval
- Load only relevant memory chunks
- Avoid dumping entire file into prompt

## 3.3 Session Persistence Modes
- ephemeral
- persistent
- project-scoped memory

---

# 4. Tooling Improvements

## 4.1 Safer File Editing
- Add diff-based editing instead of string replace
- Add preview before commit

## 4.2 Code Execution Sandbox
- Add timeout + output limits
- Capture stdout/stderr separately

## 4.3 New Tools
- run_tests
- lint_code
- format_code
- git status / commit
- dependency installer (pip/npm)

---

# 5. Context & Code Search Improvements

## 5.1 Smart Code Search
- Rank files by relevance
- Limit context size automatically

## 5.2 File Summarization
- Summarize large files before sending to LLM

## 5.3 Context Window Management
- Token budget tracking
- Prioritize high-signal files

---

# 6. Reliability & Safety

## 6.1 Retry Logic
- Handle API failures
- Exponential backoff

## 6.2 Tool Error Recovery
- Detect failure patterns
- Auto-retry with fixes

## 6.3 Guardrails
- Confirm destructive actions
- Limit recursion depth

---

# 7. UX Improvements (CLI)

## 7.1 Better Output Rendering
- Streaming responses
- Colored sections (thought/action/result)

## 7.2 Command System
- /plan
- /tools
- /memory
- /retry

## 7.3 Interactive Feedback
- Ask user for clarification only when stuck

---

# 8. Extensibility

## 8.1 Plugin System
- Register tools dynamically
- Load from folder

## 8.2 Provider Abstraction
- Support multiple LLMs cleanly
- OpenAI / Claude / local

---

# 9. Testing & Evaluation

## 9.1 Fake LLM (already hinted in book)
- Deterministic testing

## 9.2 Scenario Tests
- Fix bug task
- Build feature task
- Refactor task

## 9.3 Metrics
- Success rate
- Tool usage count
- Iteration count

---

# 10. Advanced (Optional)

## 10.1 Self-Reflection Loop
- Agent critiques its own output
- Improves over iterations

## 10.2 Parallel Tool Calls
- Allow multiple reads/searches per loop

## 10.3 Autonomous Mode
- Run without user input until task complete

---

# Suggested Implementation Order

1. Add type hints + config
2. Improve tools (safe edit, sandbox)
3. Add planning system
4. Improve memory structure
5. Add context management
6. Add reliability + retries
7. Enhance CLI UX
8. Add plugins + extensibility

---

# Expected Outcome

After these improvements, nanocode evolves from:

- Minimal agent → Production-capable agent
- Reactive → Strategic planner
- Stateless → Context-aware system
- Manual debugging → Self-healing loop

---

# Notes

Keep the spirit of Nanocode:
- Simple
- Transparent
- Hackable

Avoid over-engineering (no heavy frameworks).
