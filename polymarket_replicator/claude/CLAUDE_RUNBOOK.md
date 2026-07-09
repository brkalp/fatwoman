# Claude maintenance runbook

You are the maintenance agent for the Polymarket replicator project. Run
from the project root. Do the following, in order:

1. **Read today's log** `logs/project_one_YYYYMMDD.txt` (and yesterday's if
   today is short). Look for ERROR lines, uncaught exceptions, scripts that
   started but never logged `=== RUN END`, and suspicious values (0 users
   selected, 0 signals for many hours, fill rate near 0).

2. **Read `tasks/`**: each `*.md` file is a task from the user to improve
   the flow. Implement what is asked, then move the file to `tasks/done/`.

3. **Fix bugs you found.** Keep changes minimal and in the style of the
   existing code.

4. **Test against the paper account before trusting any fix.** Run
   `./run_paper_test.sh` - it re-runs the whole flow (mock api) against the
   dedicated test paper account in `paper_test/` and then runs pytest.
   Fills must book, account state must advance, and the pnl reporter must
   run. Never test with --dry-run: a dry run books nothing and hides
   exactly the execution/state bugs you are trying to catch. Use
   `./run_paper_test.sh --reset` only when a strategy change makes the
   accumulated test account meaningless - say so in your notes.

5. **Version bumps**: if you changed *strategy logic* (selection filters,
   sizing, risk, exits - not plain bugfixes), add a new `## xx` entry at the
   top of `CHANGELOG.md` and create `strategy/STRATEGY_xx.md` describing the
   new logic. Output files pick up the new `_xx` suffix automatically.

6. **Leave notes**: log what you did with
   `python scripts/claude_note.py "<short summary>"` so it lands in the
   daily .txt overview. Also note anything you saw but did not fix.

Never delete data files, never touch `.env`, and never remove the HALT file
if one exists - a human put it there.
