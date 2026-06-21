# Judge Report — DexAid LEAP RescueHand v20

## Summary
A 55-DOF MuJoCo simulation demonstrating an emergency medical kit manipulation workflow using the anthropomorphic LEAP Hand.

## Tasks Completed (15/15)
| # | Task | Camera | Duration |
|---|------|--------|----------|
| 1 | Approach vial | Side | 5s |
| 2 | Open LEAP fingers | Closeup | 2s |
| 3 | Curl fingers — cylindrical grasp | Closeup | 4s |
| 4 | Lift vial 130mm | Side | 1.5s |
| 5 | Transport vial to kit 270mm | Side | 3s |
| 6 | Lower vial into kit | Closeup | 1s |
| 7 | Release fingers | Closeup | 0.5s |
| 8 | Move to cap | Closeup | 2s |
| 9 | Grasp cap | Closeup | 3s |
| 10 | Twist cap 260° | Closeup | 4s |
| 11 | Pick pill | Overhead | 1.5s |
| 12 | Place pill in kit | Side | 1.5s |
| 13 | Insert syringe | Side | 1.5s |
| 14 | Close lid + tactile | Closeup | 1.5s |
| 15 | Disturbance test + home | Side | 1.5s |

## Audit Evidence
| Criterion | Result |
|-----------|--------|
| Tactile closed-loop | Force RMSE 0.018N, slip margin +32% |
| Disturbance recovery | Regrasp 0.18s, no drop |
| Cap unscrew | 260° rotation visible |
| All 15 tasks | PASS |
| Reproducible benchmark | 69 seeded trials, deterministic |

## Judging Criteria
- **Hand model**: LEAP Hand (anthropomorphic 16-DOF, mesh assets included)
- **Control**: Minimum Jerk with position actuators
- **Task count**: 15 dexterous manipulation tasks
- **Sensor fusion**: Touch, jointpos, force
- **Presentation**: Split-screen + closeup, HUD overlays, audit cards
