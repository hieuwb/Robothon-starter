# DexAid LEAP RescueHand v20

**Emergency Kit Lab — 15-Task Dexterous Manipulation with Full Auditability**

| Metric | Value |
|--------|-------|
| Robot | LEAP Hand (16-DOF) + 3-DOF Cartesian Arm |
| Scene DOF | 55 (50 velocity, 20 actuators) |
| Sensor count | 20 (touch, joint, force) |
| Tasks | 15 (vial grasp/lift/transport, cap twist, pill, syringe, lid, release) |
| Trajectory | 5th-order Minimum Jerk (smooth acceleration/deceleration) |
| Control | Cartesian impedance HUD, tactile slip margin |
| Robustness | Seeded 0.25N lateral disturbance — regrasp in 0.18s |
| Demo | 72 seconds, 640×360, 10 fps |
| Reproducibility | Single command: `python demo.py` → `outputs/demo.mp4` |

## Quick Start
```bash
pip install -r requirements.txt
python demo.py
# Output: outputs/demo.mp4 + metrics.json
```

## Technical Highlights
- **LEAP Hand** from MuJoCo Menagerie: 4 fingers × 4 joints (MCP/ROT/PIP/DIP), cylindrical thumb opposition
- **Cartesian arm**: 3 slide joints with position control (kp=220), minimum-jerk via 5th-order polynomial
- **Physics**: MuJoCo implicit integration, elliptic friction cone, multiccd contact
- **Sensors**: Touch site for lid detection, joint position sensors, force estimation
- **Audit trail**: metrics.json with 69 seeded trial statistics
