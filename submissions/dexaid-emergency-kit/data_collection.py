#!/usr/bin/env python3
"""Export compact dataset from real MuJoCo controller for judge inspection."""
import json, pathlib
from robothon.controller import RealTaskController, run_trials, PHASES
ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "outputs"; OUT.mkdir(exist_ok=True)

trial_data = run_trials(10)
ctrl = RealTaskController()
traj, metrics = ctrl.execute()

path = OUT / "dataset.json"
path.write_text(json.dumps({
    "phases": PHASES,
    "trial_summary": {
        "trials": trial_data["trials"],
        "success_rate": trial_data["success_rate"],
        "results": trial_data["results"],
    },
    "demo_trajectory": traj,
    "demo_metrics": metrics,
}, indent=2))
print(json.dumps({"ok": True, "dataset": str(path.relative_to(ROOT)), "trials": trial_data["trials"], "success_rate": trial_data["success_rate"]}, indent=2))
