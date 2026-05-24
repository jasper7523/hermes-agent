# Heartbeat Protocol ??Agent Wake-up Instructions

> This file defines what the agent MUST do each time it is woken up
> (by human, by Cron, or by Worker).
> **Do NOT just output plans. You MUST make actual progress.**

## Wake-up Procedure

1. **Load context**: Read the following files in order:
   - `memory/current-state.md` ??Where am I?
   - `memory/task-queue.md` ??What should I do next?
   - `memory/run-state.md` ??What did I do last time?

2. **Check inbox**: Scan `inbox/` for pending envelopes.

3. **Check blockers**: Review `task-queue.md` BLOCKED section.
   - If blocked ??report to N1 and STOP.
   - If not blocked ??continue.

4. **Select task**: Pick the first item from NOW queue.
   - If NOW is empty ??promote the first NEXT item to NOW.
   - If NEXT is also empty ??report idle status and STOP.

5. **Execute ONE work unit**: Make actual, measurable progress.
   - Write/modify at least one file, report, or code change.
   - Do NOT just say "I will do X next time."

6. **Update state files**:
   - `memory/current-state.md` ??Update completed items
   - `memory/task-queue.md` ??Move completed tasks to DONE
   - `memory/run-state.md` ??Record what was done this run

7. **Report**: Summarize in your response:
   - What was completed
   - Which files were updated
   - What the next run should continue
   - Whether human decision is needed (Y/N)

