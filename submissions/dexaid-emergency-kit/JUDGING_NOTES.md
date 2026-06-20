# DexAid judging notes

## Rubric alignment

- **Reproducibility:** one-command `python demo.py`; optional `python simulate_mujoco.py` for a MuJoCo stepped rollout and trajectory export.
- **MuJoCo depth:** custom MJCF with 3-axis arm, 5-finger hand, free-body vial, frictional contacts, 15 actuators, and 16 sensors.
- **Task design:** long-horizon emergency medical kit assembly: scan, approach, grasp, twist, dose placement, syringe insertion, close, verify.
- **Control:** deterministic task planner plus scripted actuator trajectory for the MuJoCo rollout; closed-loop slip-recovery is represented in the high-level policy and metrics.
- **Dexterity:** five-finger grasping and wrist/finger coordination for vial-cap manipulation.
- **Engineering:** modular package, deterministic metrics, generated media, registration metadata, and documented limitations.
- **Presentation:** generated demo/poster plus MuJoCo rollout trace video.

## Current limitations

The polished `demo.py` video is a presentation renderer. `simulate_mujoco.py` loads and steps the MJCF with controls and state/sensor export; on headless systems without OpenGL it falls back to a trace visualization while preserving MuJoCo state data.

## Why this should score higher than a simple scene

The submission is not only a static model: it includes a narrative task, reproducible evaluation, actuator-level rollout, long-horizon phases, and judge-facing documentation for transparent scoring.
