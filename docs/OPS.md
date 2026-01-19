# OPS — Team Workflow

Purpose
- Capture the team's operational workflow and decision rules.

Workflow
1. ChatGPT decides
   - ChatGPT is responsible for making decisions about direction, approaches, and trade-offs.
2. Copilot codes via PR
   - Copilot implements the decided work by opening a pull request with the changes.
3. GitHub is the source of truth
   - The repository is the canonical state; all confirmed decisions and approved code live in GitHub.
4. confirmed = decision
   - When a change or decision is marked "confirmed" (e.g., via PR review/merge or an explicit confirmation), it becomes the team's decision and should be treated as authoritative.
5. no auto-optimization
   - Do not perform automatic or silent optimizations. Any optimization that changes behavior must be proposed, reviewed, and confirmed.
6. SWING and DAY separated
   - Treat longer-term/large-impact changes (SWING) separately from short-term/daily changes (DAY).
   - Use distinct branches/PR labels to keep SWING and DAY work isolated and clearly reviewable.

Notes
- Keep PR descriptions explicit about whether a change is SWING or DAY.
- Use labels and branch naming conventions to make the intent visible (e.g., `swing/*` and `day/*` branches).
