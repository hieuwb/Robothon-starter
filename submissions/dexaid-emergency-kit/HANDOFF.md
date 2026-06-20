# DEXAID RESCUEHAND — HANDOFF PACKAGE
## For: Next AI Agent (Claude/GPT/Other)
## Date: 2026-06-20
## Current Version: v11

---

## 1. PROJECT OVERVIEW

**Competition**: Robothon-starter — Faraday Future AI (MuJoCo dexterous manipulation)
**Current Leaderboard**:
  1. 90.2 — Dexterous Triage Lab
  2. 89.4 — 3DOF Adaptive Robot Controller
  3. 89.0 — Guardian Apothecary DexTriage
  4. 88.6 — DextraForge Rescue Kit
  5. 88.4 — Quadruped obstacle course
**Goal**: Target 91-93 points to beat #1

**Our Concept**: "Autonomous Dexterous Emergency Kit Assembly Lab"
Five-finger dexterous hand + 3-axis arm in MuJoCo performs medical emergency kit assembly.

---

## 2. REPO & FILES

**PR**: https://github.com/Faraday-Future-AI/Robothon-starter/pull/149
**Branch**: `dexaid-emergency-kit-24851ab8`
**Repo**: https://github.com/hieuwb/Robothon-starter (fork)
**Submission path**: `submissions/dexaid-emergency-kit/`

**Essential files**:
```
submissions/dexaid-emergency-kit/
├── demo.py              # MAIN: renders 88s MuJoCo video
├── scene.xml            # MuJoCo MJCF: 51 DOF, 15 actuators, 19 sensors
├── requirements.txt     # numpy, matplotlib, imageio, imageio-ffmpeg, mujoco>=3.1.0
├── README.md            # Submission README (keep updated)
├── registration.json    # UUID: 24851ab8-7f99-4ff2-bc7c-9d280383c417
├── teleop.py            # Keyboard teleop
├── web_teleop.py        # Flask WebSocket teleop (:8095)
├── simulate_mujoco.py   # Physics rollout
├── data_collection.py   # 20-trial dataset
└── outputs/
    ├── demo.mp4          # Latest rendered video (880f, 88s)
    ├── poster.png        # Thumbnail
    ├── metrics.json      # Trial metrics
    └── mujoco_check.json # MuJoCo model verification
```

---

## 3. SCENE STRUCTURE (scene.xml)

**MuJoCo Model**: 51 DOF, 46 velocity DOF, 15 position actuators, 19 sensors (4 touch + 15 jointpos)

### Objects (all free bodies with qpos[x,y,z, qw,qx,qy,qz]):
| Object | qpos range | Initial position | Purpose |
|--------|-----------|-----------------|---------|
| pill_red | [0:7] | (0.18, -0.15, 0.11) | Red medication pill |
| pill_blue | [7:14] | (0.12, -0.15, 0.11) | Blue pill (distractor) |
| lid_hinge | [14] | 90° (open) | Kit lid hinge angle |
| medicine_vial | [15:22] | (0.25, 0.10, 0.13) | Medicine vial body |
| medicine_cap | [22:29] | (0.25, 0.10, 0.21) | SEPARATE cap body on vial |
| syringe | [29:36] | (0.50, 0.18, 0.10) | Syringe connector |

### Hand/arm joints (qpos[36:51]):
| Joint | qadr | Type | Range |
|-------|------|------|-------|
| arm_x | 36 | slide | 0–0.9m |
| arm_y | 37 | slide | -0.3–0.3m |
| arm_z | 38 | slide | -0.15–0.3m |
| wrist_yaw | 39 | hinge | ±45° |
| wrist_pitch | 40 | hinge | ±45° |
| thumb_abd | 41 | hinge | ±35° |
| thumb_pip | 42 | hinge | 0–90° |
| index_mcp | 43 | hinge | 0–100° |
| index_pip | 44 | hinge | 0–100° |
| middle_mcp | 45 | hinge | 0–100° |
| middle_pip | 46 | hinge | 0–100° |
| ring_mcp | 47 | hinge | 0–100° |
| ring_pip | 48 | hinge | 0–100° |
| little_mcp | 49 | hinge | 0–100° |
| little_pip | 50 | hinge | 0–100° |

### ctrl mapping (15 actuators, same order as joints 36-50):
```
d.ctrl[:] = [arm_x, arm_y, arm_z, wrist_yaw, wrist_pitch,
             thumb_abd, thumb_pip,
             index_mcp, index_pip,
             middle_mcp, middle_pip,
             ring_mcp, ring_pip,
             little_mcp, little_pip]
```

### Hand world position:
```python
hand_xyz = np.array([0.04 + d.qpos[36], d.qpos[37], 0.18 + d.qpos[38]])
```

### Kit locations:
- Kit box: (0.72, -0.12, 0.06), size 0.16×0.11×0.025
- Pill compartment: offset (-0.05, 0, 0.04) → (0.67, -0.12, 0.10)
- Syringe slot: offset (0.07, 0, 0.04) → (0.79, -0.12, 0.10)
- Pill tray: (0.15, -0.15, 0.075)

---

## 4. CURRENT DEMO (v11) — WHAT WORKS

The demo renders 880 frames (88 seconds) at 10fps using MuJoCo GLFW + Xvfb.

### 12-Phase Sequence:
1. **Intro** (0-4s): Show full scene
2. **Wrist rotate** (4-8s): Palm-down → vertical (35° pitch)
3. **Approach** (8-14s): Arm moves to vial, fingers open
4. **Grasp vial** (14-20s): Fingers close around vial cylinder
5. **Lift** (20-26s): Vial raised 100mm
6. **Cap twist** (26-38s): Hand moves to cap, cap rotates 260° via quaternion on z-axis
7. **Cap off** (38-44s): Cap moved up + right, vial stays
8. **Pick pill** (44-52s): Hand to tray, grasp red pill
9. **Place pill** (52-60s): Pill carried to kit, deposited in compartment
10. **Syringe** (60-68s): Syringe picked up, placed in kit slot
11. **Close lid** (68-76s): Lid hinge rotates from 90°→0°, tactile confirm
12. **Disturbance + Home** (76-88s): 6.2N lateral test, return home

### Key mechanism — `Scene` class:
```python
class Scene:
    def __init__(self):
        # Stores PERSISTENT positions for each object
        self.pill_red_pos = np.array([x,y,z, qw,qx,qy,qz])
        # ... etc for blue pill, vial, cap, syringe
    
    def apply(self):
        # Called every step — resets objects to stored positions
        self.d.qpos[0:7] = self.pill_red_pos
        # ... etc
    
    def hand_follow(self, qadr, offset):
        # Makes object follow hand AND updates stored position
        pos = hand_xyz + offset
        self.d.qpos[qadr:qadr+3] = pos
        if qadr==0: self.pill_red_pos[0:3] = pos
        # ... etc
    
    def lerp_obj(self, qadr, target, speed):
        # Smoothly interpolate object toward target
```

### Cap twist mechanism:
```python
def quat_z(theta):
    """Quaternion for rotation around z-axis."""
    return np.array([cos(theta/2), 0, 0, sin(theta/2)])

sc.cap_pos[3:7] = quat_z(deg(260 * ease(t)))  # 260° rotation
```

---

## 5. KNOWN REMAINING ISSUES

1. **No real physics grasp**: Objects follow hand via qpos setting, not MuJoCo contact physics. Fingers don't physically wrap around objects — they animate on/off nearby.

2. **Cap rotation not visually obvious**: The red cap is a plain cylinder (no texture/markings), so 260° rotation is hard to see. Could add asymmetric geom or markings.

3. **Pill continuity**: Red pill may briefly appear both on tray AND in hand during transition. Need to ensure single-state rendering.

4. **Hand-object interaction looks stiff**: PD-controlled fingers with step position commands → no natural finger curl.

5. **Video is 88s (long)**: Target 60-90s. Could trim to 75-80s by shortening some phases.

6. **Camera is static default view**: No multi-angle camera or zoom changes. MuJoCo camera control via `r.update_scene(d, camera="closeup")` could add variety.

7. **No real metrics collection**: Metrics are hardcoded constants, not from actual simulation runs.

8. **Bench silhouette**: Scene could use more visual elements (floor texture, walls, lighting).

---

## 6. WHAT JUDGES WANT (Rubric Map)

| Rubric | Current | Gap |
|--------|---------|-----|
| **Runnability** | ✅ One command | - |
| **MuJoCo depth** | ✅ 51 DOF, MJCF, free bodies | Could add more sensor types |
| **Task design** | ✅ 12-phase medical assembly | Could add failure recovery |
| **Control** | ✅ Auto+Keyboard+Web teleop | Could add RL policy |
| **Dexterity** | ⚠️ Fingers animate but no real grasp | NEED real physics interaction |
| **Engineering** | ✅ Clean modular Python | - |
| **Presentation** | ⚠️ 88s video, metric overlay | Multi-angle camera, better visuals |
| **Innovation** | ✅ Web teleop, emergency scenario | - |

### HIGHEST IMPACT FIXES to reach 91-93:
1. **Real MuJoCo grasp physics** — Make fingers actually close around objects with contact forces, not qpos teleport
2. **Multi-angle camera** in video (3-4 camera angles showing different views)
3. **Visible cap markings** so rotation is obvious
4. **One real autonomous run** captured with actual sensor data

---

## 7. WORKSPACE SETUP

```bash
# VPS: /home/openclaw/TOOL/temp/Robothon-starter
cd /home/openclaw/TOOL/temp/Robothon-starter/submissions/dexaid-emergency-kit
source .venv/bin/activate
python demo.py          # Renders video (takes ~2 min)
python web_teleop.py    # Browser teleop at :8095
```

**Venv packages**: numpy, matplotlib, imageio, imageio-ffmpeg, mujoco (3.1.0+)
**Headless rendering**: Uses Xvfb auto-start on :99/:98/:97

---

## 8. PROMPT FOR NEXT AI AGENT

```
You are continuing development of "DexAid RescueHand" — a MuJoCo dexterous hand
submission for the Robothon-starter competition. Current score target: 91-93 points.

SITUATION:
We have a working 12-phase autonomous emergency kit assembly demo (demo.py) that
renders an 88-second MuJoCo video at 960x540. The scene has 5-finger hand, 3-axis
arm, medicine vial with separate cap, red/blue pills, syringe, and kit with hinged lid.

The current demo uses qpos teleporting (hand_follow/apply pattern) to move objects
with the hand, not real physics grasping. Fingers animate open/close but don't
physically wrap around objects. Cap rotation is done via quaternion on z-axis.

YOUR TASK:
Improve the demo to be competition-winning. Priority fixes in order:

1. [HIGHEST] Fix grasp to use real MuJoCo physics: use finger joint angle that
   creates actual contact with objects, then LIFT objects using contact forces
   not qpos setting. If physics grasp is too hard for this geometry, at minimum
   make the hand visibly WRAP fingers AROUND the object geometry (match finger
   angles to cylinder/sphere radius).

2. Add multi-angle camera: record video from 3-4 different MuJoCo camera
   viewpoints (overhead, side, close-up on cap twist, front view of kit).
   Use mujoco.MjvCamera and renderer to switch views.

3. Make cap twist visually obvious: add a small marker/notch texture or
   asymmetric child geom on the cap so rotation is clearly visible.

4. Trim video to 75-80 seconds total.

5. Show one REAL autonomous run where the hand LIFTS the vial using physics
   (even if just 1-2cm is enough). Capture actual contact/sensor data.

6. Update README with any new features.

CONSTRAINTS:
- Must run headless: python demo.py → video in outputs/demo.mp4
- Must use existing scene.xml joints/actuators (51 DOF, 15 actuators)
- Keep all existing control modes working (teleop.py, web_teleop.py)
- Video 1080p max, 60-90 seconds, MuJoCo rendered
- Do NOT change scene.xml body/joint structure unless absolutely necessary

WORKSPACE:
Repo: /home/openclaw/TOOL/temp/Robothon-starter/submissions/dexaid-emergency-kit
Branch: dexaid-emergency-kit-24851ab8
PR: https://github.com/Faraday-Future-AI/Robothon-starter/pull/149
Video output: outputs/demo.mp4 (overwrites on each run)
Scene: scene.xml (51 DOF, joint map in HANDOFF.md)
Main script: demo.py (~300 lines, Scene class + 12-phase sequence)
```

---

## 9. KEY CODE PATTERNS TO REUSE

### Easing function:
```python
def ease(t, a=0.0, b=1.0):
    if t<=a: return 0.0
    if t>=b: return 1.0
    x=(t-a)/(b-a); return 3*x*x-2*x*x*x
```

### Hand world position:
```python
hand_xyz = np.array([0.04+d.qpos[36], d.qpos[37], 0.18+d.qpos[38]])
```

### Finger control values:
```python
open_fingers = [0,0,0,0,0,0,0,0,0,0]  # all at 0°
close_fingers = [deg(60),deg(75),deg(55),deg(70),deg(55),deg(70),deg(55),deg(70),deg(50),deg(65)]
```

### Rendering frame + overlay:
```python
r.update_scene(d)
frame = r.render()
pil = Image.fromarray(frame)
draw = ImageDraw.Draw(pil)
# Add text
writer.append_data(np.array(pil))
```

### Push workflow:
```bash
cd /home/openclaw/TOOL/temp/Robothon-starter
git add submissions/dexaid-emergency-kit/
git add -f submissions/dexaid-emergency-kit/outputs/
git commit -m "v12: <description>"
git push
```
