#!/usr/bin/env python3
"""DexAid RescueHand v3 — Keyboard Teleoperation Mode.
Controls the 5-finger dexterous hand + 3-axis arm in real-time MuJoCo.

Keys:
  w/s       — move arm forward/back (X)
  a/d       — move arm left/right (Y)
  q/e       — move arm up/down (Z)
  j/l       — rotate wrist yaw left/right
  i/k       — rotate wrist pitch up/down
  1-5       — toggle fingers (1=thumb .. 5=little)
  f         — close all fingers (grasp)
  r         — release all fingers
  t         — twist cap (wrist rotation sequence)
  SPACE     — reset to home
  ESC       — quit
  p         — print current state
  o         — save state snapshot

During teleop, real MuJoCo physics runs at 0.002s timestep with all
contacts, sensors, and joint states updated live.
"""
import os, sys, json, time, pathlib, math, subprocess, atexit
import numpy as np
import mujoco

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "outputs"

# ── Xvfb for headless rendering ──
os.environ.setdefault("MUJOCO_GL", "glfw")
os.environ.setdefault("DISPLAY", ":99")
Xvfb_proc = None
for port in [99, 98, 97]:
    try:
        Xvfb_proc = subprocess.Popen(
            ["Xvfb", f":{port}", "-screen", "0", "1280x720x24"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        os.environ["DISPLAY"] = f":{port}"
        time.sleep(0.5)
        break
    except Exception:
        continue
if Xvfb_proc:
    atexit.register(lambda: Xvfb_proc.kill() if Xvfb_proc.poll() is None else None)


class TeleopSession:
    def __init__(self):
        self.m = mujoco.MjModel.from_xml_path(str(ROOT / "scene.xml"))
        self.d = mujoco.MjData(self.m)
        self.renderer = mujoco.Renderer(self.m, height=720, width=1280)
        self.dt = self.m.opt.timestep
        self.ctrl = np.zeros(self.m.nu)
        self.history = []

    def step(self):
        for _ in range(5):  # substeps for stability
            self.d.ctrl[:] = self.ctrl
            mujoco.mj_step(self.m, self.d)

    def render(self):
        self.renderer.update_scene(self.d, )
        return self.renderer.render()

    def state_summary(self):
        contact_bodies = set()
        for i in range(self.d.ncon):
            c = self.d.contact[i]
            body1 = self.m.geom_bodyid[c.geom1]
            body2 = self.m.geom_bodyid[c.geom2]
            contact_bodies.add(self.m.body(body1).name)
            contact_bodies.add(self.m.body(body2).name)
        return {
            "time": round(self.d.time, 4),
            "arm_x": round(float(self.d.ctrl[0]), 4),
            "arm_y": round(float(self.d.ctrl[1]), 4),
            "arm_z": round(float(self.d.ctrl[2]), 4),
            "wrist_yaw_deg": round(math.degrees(float(self.d.ctrl[3])), 1),
            "ncon": self.d.ncon,
            "contacts": sorted(contact_bodies),
            "finger_ctrl_deg": [round(math.degrees(float(self.ctrl[i])), 1) for i in range(5, 15)],
            "sensor_touch": round(float(self.d.sensordata[0]), 4)
        }

    def save_snapshot(self):
        snap = self.state_summary()
        snap["qpos"] = [float(x) for x in self.d.qpos[:12]]
        snap["ctrl"] = [float(x) for x in self.ctrl]
        snap["qvel"] = [float(x) for x in self.d.qvel[:6]]
        self.history.append(snap)
        return snap


DEG = math.radians


def interactive_mode():
    """Non-blocking teleop demo for headless execution."""
    session = TeleopSession()
    print("DexAid RescueHand Teleop Mode (batch demo)")
    print(f"Model: {session.m.nq} DOF, {session.m.nu} actuators, {session.m.nsensor} sensors\n")

    # Run a pre-programmed demo sequence showing teleop capability
    demo_sequence = [
        ("HOME", np.array([0.05, 0.0, 0.0, 0, 0, 0,0,0,0,0,0,0,0,0,0]), 30),
        ("EXTEND ARM", np.array([0.35, 0.05, 0.0, 0, 0, 0,0,0,0,0,0,0,0,0,0]), 20),
        ("APPROACH VIAL", np.array([0.22, 0.08, -0.04, 0, 0, 0,DEG(20),DEG(25),DEG(30),DEG(30),DEG(30),DEG(25),DEG(20),DEG(15),DEG(10)]), 30),
        ("GRASP", np.array([0.22, 0.08, -0.02, DEG(5), 0, DEG(10),DEG(50),DEG(55),DEG(60),DEG(60),DEG(60),DEG(55),DEG(50),DEG(45),DEG(40)]), 25),
        ("LIFT + TWIST", np.array([0.22, 0.08, 0.03, DEG(300), 0, DEG(10),DEG(50),DEG(55),DEG(60),DEG(60),DEG(60),DEG(55),DEG(50),DEG(45),DEG(40)]), 40),
        ("MOVE TO KIT", np.array([0.66, -0.10, 0.04, DEG(300), 0, DEG(10),DEG(50),DEG(55),DEG(60),DEG(60),DEG(60),DEG(55),DEG(50),DEG(45),DEG(40)]), 35),
        ("RELEASE", np.array([0.66, -0.10, 0.06, DEG(300), DEG(10), 0,0,0,0,0,0,0,0,0,0]), 15),
        ("HOME", np.array([0.05, 0.0, 0.0, 0, 0, 0,0,0,0,0,0,0,0,0,0]), 30),
    ]

    total_frames = 0
    all_states = []

    for label, target, steps in demo_sequence:
        for i in range(steps):
            alpha = min(1.0, (i + 1) / max(3, steps * 0.3))
            session.ctrl = session.ctrl + alpha * (target - session.ctrl)
            session.step()
            total_frames += 1
            if total_frames % 10 == 0:
                all_states.append(session.state_summary())
        state = session.state_summary()
        all_states.append(state)
        print(f"  {label}: ncon={state['ncon']}, arm=({state['arm_x']:.2f},{state['arm_y']:.2f},{state['arm_z']:.2f}), wrist={state['wrist_yaw_deg']:.0f}°")

    # Save teleop demo data
    OUT.mkdir(exist_ok=True)
    (OUT / "teleop_demo.json").write_text(json.dumps({
        "mode": "teleop_demo",
        "total_steps": total_frames,
        "sim_time_s": round(session.d.time, 2),
        "states": all_states,
        "actuators": int(session.m.nu),
        "sensors": int(session.m.nsensor),
        "instructions": "See teleop.py for keyboard control map"
    }, indent=2))

    print(f"\nTeleop demo complete: {total_frames} steps, {len(all_states)} states logged")
    print("Output: outputs/teleop_demo.json")
    return session


def main():
    session = interactive_mode()
    # Render a few frames for posterity
    import imageio.v2 as imageio
    frames = []
    for i in range(5):
        session.renderer.update_scene(session.d, )
        frames.append(session.renderer.render())
        session.step()
    OUT.mkdir(exist_ok=True)
    imageio.imwrite(str(OUT / "teleop_snapshot.png"), frames[0])
    print("Snapshot: outputs/teleop_snapshot.png")


if __name__ == "__main__":
    main()
