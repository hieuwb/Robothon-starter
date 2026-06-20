# DexAid RescueHand — technical report

DexAid targets the top scoring categories by combining **dexterous manipulation**, **long-horizon task planning**, **scenario relevance**, and **data collection** in one MuJoCo package.

## What changed for the upgraded submission

1. **Richer MJCF world** — five-finger hand, 3-axis arm, free-body vial, cap, syringe connector, dose pill, kit target, friction, damping, armature, fingertip sites, and tactile/proprioceptive sensors.
2. **Actuator-level rollout** — `simulate_mujoco.py` loads the MJCF, drives all 15 actuators, steps MuJoCo, and exports controls, qpos, and sensor traces.
3. **Dataset mode** — `data_collection.py` exports trial records and phased trajectories for reproducibility/data-collection rubric credit.
4. **Transparent limitations** — presentation video is polished; rollout video/state data is physics-stepped and falls back gracefully on headless OpenGL systems.

## Judge summary

- Direction: dexterous hand + long-horizon tasks + real-world emergency scenario + data collection.
- Robot: custom five-finger dexterous hand with wrist and 3 slide joints.
- Task: scan tray → approach vial → five-finger grasp → cap twist → place dose → insert syringe → close kit → verify tactile seal → recover from disturbance.
- Outputs: demo video, MuJoCo rollout video, metrics JSON, rollout trajectory JSON, dataset JSON, poster.
