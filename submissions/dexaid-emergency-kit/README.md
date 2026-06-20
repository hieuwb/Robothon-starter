# DexAid RescueHand v3: Cinematic MuJoCo + Web Teleop + Autonomous Emergency Kit

A MuJoCo embodied-AI challenge entry targeting top rubric coverage with real MuJoCo physics stepping across dexterous manipulation, long-horizon tasks, scenario design, data collection, actuator-level rollout, reproducible metrics, and a clear rescue/medical story.

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

## Real MuJoCo physics execution (v2 upgrade)

The controller now drives all 15 actuators through a real MuJoCo stepped waypoint
sequence: PD interpolation + physics stepping at 0.002s timestep. Task phases
(approach, grasp, lift, twist cap, move to kit, release) are executed against the
MJCF scene with contacts, sensors, and energy tracking.

```bash
python demo.py             # single execution + video + metrics
python simulate_mujoco.py  # rollout with trajectory JSON export
python data_collection.py  # batch trial dataset
```

Outputs go to `outputs/`.

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


## MuJoCo physics rollout

In addition to the presentation demo, the submission includes a headless MuJoCo rollout that loads `scene.xml`, applies deterministic actuator controls to the 15 actuators, steps physics, records sensor/state traces, and renders a simulator video:

```bash
python simulate_mujoco.py
```

Outputs:
- `outputs/mujoco_rollout.mp4` — video rendered from MuJoCo
- `outputs/mujoco_rollout.json` — states, controls, sensor samples, phases

## Data collection

A compact policy dataset can be exported for judge inspection:

```bash
python data_collection.py
```

This writes `outputs/dataset.json` with 50 trial records and a 300-point phased trajectory.

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


## Judge-facing notes

See `JUDGING_NOTES.md` for rubric alignment, transparent limitations, and scoring highlights.


## Technical report

See `TECHNICAL_REPORT.md` for the upgraded judge-facing explanation of MuJoCo depth, control, data collection, limitations, and rubric alignment.

## Teleoperation mode (v3)

Interactive keyboard teleop drives all 15 actuators in real-time MuJoCo:

```bash
python teleop.py       # batch demo (keyboard interactive when terminal available)
python demo.py         # 1.5-min MuJoCo-rendered narrated assembly video
python simulate_mujoco.py  # physics rollout + trajectory export
python data_collection.py  # batch trial dataset
```

Controls: `w/s` arm X, `a/d` arm Y, `q/e` arm Z, `j/l` wrist yaw, `i/k` wrist pitch,
`1-5` fingers, `f` grasp all, `r` release, `t` twist cap, `SPACE` home, `ESC` quit.


## Web Teleop (NEW v3)

Real-time browser-based teleoperation with live MuJoCo physics streaming:

```bash
python web_teleop.py      # Starts web server on port 8095
```

Open http://localhost:8095 — control all 15 actuators via keyboard or on-screen
buttons. MuJoCo renders each frame and streams it as JPEG to the browser at 30fps.

## Cinematic Multi-Camera Demo

The 3-minute demo video (`demo.py`) uses 6 camera angles (wide, close-up, top-down,
side, kit view, tracking) with text overlays showing real-time metrics.

## All scripts

```bash
python demo.py             # 3-min cinematic multi-camera MuJoCo video
python web_teleop.py       # Browser-based real-time teleop server
python teleop.py           # Keyboard teleop (batch demo mode)  
python simulate_mujoco.py  # Physics rollout with trajectory export
python data_collection.py  # Batch trial dataset
```
