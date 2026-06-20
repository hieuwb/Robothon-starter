#!/usr/bin/env python3
"""Export a compact dataset from the deterministic policy for judge inspection."""
import json, pathlib
from robothon.controller import EmergencyKitPolicy, PHASES
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
policy=EmergencyKitPolicy(seed=2026)
trials=[policy.run_trial(i+1).__dict__ for i in range(50)]
trajectory=[{"t":t,"phase":phase,"hand_x":x,"hand_y":y,"cap_angle_deg":angle,"slip_m":slip} for t,phase,x,y,angle,slip in policy.trajectory(300)]
path=OUT/'dataset.json'
path.write_text(json.dumps({"phases":PHASES,"trials":trials,"trajectory":trajectory},indent=2))
print(json.dumps({"ok":True,"dataset":str(path.relative_to(ROOT)),"trials":len(trials),"trajectory_points":len(trajectory)},indent=2))
