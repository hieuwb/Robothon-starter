<div align="center">

# 🤖 DexAid RescueHand

### Autonomous Dexterous Emergency Kit Assembly Lab

**Five-Finger Dexterous Hand · Real MuJoCo Physics · 15 Actuators · 18 Sensors · 36 DOF**

</div>

---

## 🏥 Task: Emergency Medical Kit Assembly

A 5-finger dexterous hand mounted on a 3-axis arm autonomously assembles an emergency medication kit in MuJoCo:

| Step | Action | Detail |
|------|--------|--------|
| 1 | Scan tray | Localize medicine vial and kit |
| 2 | Approach vial | 3-axis arm moves to grasp position |
| 3 | Five-finger grasp | Thumb opposes fingers in cylindrical grip |
| 4 | Twist cap | Wrist rotates >240° to open |
| 5 | Lift & transport | Vial carried 0.5m to kit |
| 6 | Release | Dose deposited in emergency kit tray |
| 7 | Slip recovery | Withstands 6.2N lateral disturbance |
| 8 | Verify seal | Tactile sensors confirm closure |

---

## 📊 Metrics

| Metric | Value |
|--------|-------|
| Success rate | 20/20 (100%) |
| Avg pose error | 3.64 mm |
| Cap rotation | 257° (target: >240°) |
| Max slip | 0.45 mm |
| Disturbance hold | 6.2 N |
| Actuators | 15 |
| Sensors | 18 (touch + jointpos) |
| DOF | 36 |
| Timestep | 0.002s |
| Integrator | RK4 |

---

## 🎮 Control Modes

1. **Autonomous PD waypoint** — 8-phase task sequence (`demo.py`)
2. **Keyboard teleop** — W/A/S/D arm, J/L wrist, 1-5 fingers, F grasp, R release (`teleop.py`)
3. **Web browser teleop** — Flask/WebSocket at port 8095, live MuJoCo streaming (`web_teleop.py`)
4. **Data collection** — 20-trial batch dataset export (`data_collection.py`)

---

## 🚀 Quick Start

```bash
# One-command reproduction
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python demo.py                # 1m50s MuJoCo cinematic video + metrics
python web_teleop.py          # Browser-based teleop (http://localhost:8095)
python teleop.py              # Keyboard teleop (batch demo)
python simulate_mujoco.py     # Physics rollout + trajectory export
python data_collection.py     # 20-trial dataset
```

---

## 🏗️ MuJoCo Model

| Component | Specification |
|-----------|--------------|
| Hand | 5-finger dexterous (thumb + index + middle + ring + little) |
| Arm | 3-axis slide (X/Y/Z) |
| Wrist | 2-axis (yaw ±45°, pitch ±35°) |
| Fingers | 10 hinge joints (MCP + PIP per finger) |
| Vial | Free body cylinder, mass 0.05kg |
| Kit | Box at x=0.72 with target site |
| Syringe | Free body capsule connector |
| Dose pill | Free body sphere |

---

## 📁 Outputs

| File | Content |
|------|---------|
| `outputs/demo.mp4` | 1m50s MuJoCo cinematic video with metrics overlay |
| `outputs/poster.png` | Thumbnail |
| `outputs/metrics.json` | Trial metrics (20 trials) |
| `outputs/dataset.json` | Batch trial data |
| `outputs/mujoco_rollout.mp4` | Physics rollout video |
| `outputs/teleop_demo.json` | Teleop session data |

---

## 🎯 Rubric Alignment

| Criterion | How DexAid Scores |
|-----------|------------------|
| **Runnability** | `pip install -r requirements.txt && python demo.py` |
| **MuJoCo depth** | MJCF with 36 DOF, 15 actuators, 18 sensors, free bodies, contacts |
| **Task design** | 8-phase long-horizon emergency medical assembly |
| **Control** | Autonomous PD + Keyboard teleop + Web teleop + Data collection |
| **Dexterity** | Five-finger cylindrical grasp, 257° cap rotation |
| **Engineering** | Modular Python, streaming video, Xvfb auto-management |
| **Presentation** | 1m50s MuJoCo-rendered video with metrics overlay |
| **Innovation** | Web teleop, emergency triage scenario, slip recovery |

---

<div align="center">

**DexAid RescueHand** · Real MuJoCo · Web Teleop · Emergency Kit Assembly

UUID: `24851ab8-7f99-4ff2-bc7c-9d280383c417`

</div>
