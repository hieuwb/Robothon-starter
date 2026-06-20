# DexAid RescueHand v14 — Real Contact Physics + Assisted Manipulation

**Five-finger dexterous hand with hybrid real-contact + weld-assisted manipulation in MuJoCo.**

## Approach
- **Palm push**: Real MuJoCo contact physics — box geom makes contact with vial, pushes via physics
- **Cap twist**: Wrist-driven 260° rotation with notch marker
- **Pill/syringe**: Palm-scoop placement
- **Lid close**: Real hinge joint physics + tactile sensor

## Quick Start
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python demo.py  # 69s MuJoCo video at 12fps
```

## Metrics (from simulation)
| Metric | Value |
|--------|-------|
| Palm push distance | 4mm (real contact) |
| Contacts at end | 108 |
| Cap rotation | 260° |
| Pill placed | ✓ |
| Syringe placed | ✓ |
| Lid sealed | ✓ |
| DOF | 51 |
| Actuators | 15 |
| Sensors | 19 |

## Control Modes
- `demo.py` — Autonomous hybrid sequence
- `teleop.py` — Keyboard teleop
- `web_teleop.py` — Browser teleop (Flask/WebSocket :8095)
- `data_collection.py` — Batch dataset

## Scene
- 5-finger hand with sphere-tipped fingers (r=18mm)
- 3-axis arm (0.9m X × 0.5m Y × 0.4m Z)
- Medicine vial + separate cap with notch marker
- Red/blue pills on tray
- Syringe connector
- Kit box with hinged lid + tactile sensor
- 3 cameras: overhead, side, closeup

Demo: https://raw.githubusercontent.com/hieuwb/Robothon-starter/dexaid-emergency-kit-24851ab8/submissions/dexaid-emergency-kit/outputs/demo.mp4
