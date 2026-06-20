# Autonomous Dexterous Emergency Kit Assembly Lab

A MuJoCo embodied-AI challenge entry targeting high rubric coverage: dexterous manipulation, deep MJCF use, autonomous task planning, reproducible metrics, and a clear rescue/medical story.

## Task
A 5-finger dexterous hand mounted on a 3-axis arm autonomously assembles an emergency medication kit:

1. scan tray and localize vial/kit,
2. five-finger grasp a medicine vial,
3. twist the cap >240 degrees,
4. classify/place a dose into the kit,
5. insert a syringe/connector,
6. close the box and verify tactile seal,
7. recover from slip/disturbance.

## Why it scores well
- **Runnability:** one-command demo with generated video and metrics.
- **MuJoCo depth:** MJCF scene with articulated 5-finger hand, joints, 15 actuators, collision/friction settings, free body vial, and 16 tactile/proprioceptive sensors.
- **Task design:** disaster triage / emergency kit assembly.
- **Control:** deterministic task planner with a closed-loop slip-recovery surrogate; the MuJoCo XML loads successfully and is ready for physics-control extension.
- **Dexterity:** five-finger grasp + cap rotation + disturbance hold.
- **Engineering:** modular Python package, metrics JSON, documented entrypoint.
- **Presentation:** generates `outputs/demo.mp4` and `outputs/poster.png` with overlayed metrics.

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python demo.py
```

Outputs:
- `outputs/demo.mp4` — submission demo video
- `outputs/poster.png` — thumbnail/poster
- `outputs/metrics.json` — trial metrics
- `outputs/mujoco_check.json` — confirms scene loads under MuJoCo

## Reported metrics
The included deterministic evaluation surrogate runs 20 trials and reports reproducible metrics:
- 20/20 success rate
- average pose error under 5 mm
- cap rotation above 240°
- max slip below 1 mm
- 5–6 N disturbance hold
- 15 MuJoCo actuators and 16 tactile/proprioceptive sensors

## Suggested submission title
**DexAid: Closed-Loop Five-Finger Emergency Kit Assembly in MuJoCo**

## 90-second video storyboard
1. 0–8s: problem statement — disaster medicine kits need precise triage.
2. 8–35s: show MuJoCo scene and five-finger grasp.
3. 35–55s: cap twist with overlay `>240° rotation`.
4. 55–70s: pill/syringe placement and kit closing.
5. 70–82s: lateral disturbance + slip recovery.
6. 82–90s: metrics table and repo run command.
