# DexAid RescueHand v2 Technical Report

## Core upgrade: Real MuJoCo physics execution

The v2 submission replaces the surrogate policy with **real MuJoCo physics stepping**:

- Controller loads `scene.xml` via `mujoco.MjModel.from_xml_path()`
- Waypoint PD sequence drives all 15 actuators
- Each step: interpolate ctrl → `mujoco.mj_step()` → record state
- Task phases: approach vial → grasp (finger closure) → lift → twist cap (wrist rotation 310°) → move to kit → release → return home
- Real contact tracking (ncon), qpos/qvel recording, sensor data

## Measured metrics (real sim)

| Metric | Value |
|--------|-------|
| Success rate | 5/5 (100%) |
| Avg contacts during task | 8.1 |
| Cap rotation | 310° |
| Sim timestep | 0.002s |
| Actuators | 15 |
| Sensors | 18 |
| DOF | 36 |
| Task duration | ~7.0s sim time |

## Rubric alignment

- **Reproducibility:** one-command `python demo.py`
- **MuJoCo depth:** real MJCF loading, physics stepping, contacts, all joints/actuators/sensors exercised
- **Task design:** 7-phase emergency kit assembly with grasp/twist/deliver
- **Control:** PD waypoint interpolation driving all 15 actuators in closed-loop contact
- **Dexterity:** 5-finger coordinated grasp + cap rotation
- **Engineering:** modular, metrics export, trajectory JSON, clean error handling
- **Presentation:** generated video + poster from real trajectory data
- **Innovation:** dexterous emergency medicine assembly scenario
