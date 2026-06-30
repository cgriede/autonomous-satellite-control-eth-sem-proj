# Watch agent (other machine)

After `git pull`, hand this to a Cursor agent:

> Follow `.cursor/skills/long-run-watch/SKILL.md` and profile `profiles/ml-algo-overnight.md`. I started (or will start) `run_overnight.py` on this machine. Check every hour; post status to `.cursor/agents-discussion/message-queue.md` and chat under **Agents-Discussion Message-Queue**. Light-fix only in the experiment folder; ask me before production changes.

User starts the run:

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
python backend/scripts/experiments/ml_algo_overnight/run_overnight.py
```

Morning: `results/overnight_summary.json`.
