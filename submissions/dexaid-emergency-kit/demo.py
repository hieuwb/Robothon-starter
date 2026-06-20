#!/usr/bin/env python3
"""DexAid RescueHand v4 — Working grasp + transport + release demo."""
import os, json, pathlib, subprocess, time, atexit, math
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "outputs"; OUT.mkdir(exist_ok=True)

os.environ.setdefault("MUJOCO_GL", "glfw")
XVFB = None
for port in [99,98,97]:
    try:
        os.environ["DISPLAY"] = f":{port}"
        XVFB = subprocess.Popen(["Xvfb",f":{port}","-screen","0","960x540x24"],
                                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(0.5); break
    except: continue

deg = math.radians; W, H = 960, 540
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
FS = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)

def overlay(frame, title, sub, t, ncon, vial):
    pil = Image.fromarray(frame); draw = ImageDraw.Draw(pil)
    draw.rectangle([(0,0),(W,50)], fill=(13,17,23,220))
    draw.text((W//2,8), title, fill=(88,166,255), font=FONT, anchor="mt")
    draw.text((W//2,32), sub, fill=(200,200,200), font=FS, anchor="mt")
    draw.rectangle([(0,H-32),(W,H)], fill=(13,17,23,200))
    info = f"t={t:.1f}s  Vial:({vial[0]:.2f},{vial[1]:.2f},{vial[2]:.3f})  Contacts:{ncon}  Act:15  Sens:18"
    draw.text((W//2,H-20), info, fill=(126,231,135), font=FS, anchor="mt")
    return np.array(pil)

def main():
    print("=== DexAid RescueHand v4 — Working Grasp Demo ===\n")
    m = mujoco.MjModel.from_xml_path(str(ROOT/"scene.xml"))
    d = mujoco.MjData(m); dt = m.opt.timestep
    renderer = mujoco.Renderer(m, height=H, width=W)
    FG, fps = list(range(7,17)), 15

    d.ctrl[:] = np.zeros(15)
    for _ in range(int(1/dt)): mujoco.mj_step(m, d)

    # Approach
    for gi in FG: m.geom_contype[gi] = m.geom_conaffinity[gi] = 0
    d.ctrl[:] = [0.12, 0.08, -0.03, 0,0, 0,0,0,0,0,0,0,0,0,0]
    for _ in range(int(1.5/dt)): mujoco.mj_step(m, d)

    # Grasp
    for gi in FG: m.geom_contype[gi] = m.geom_conaffinity[gi] = 1
    d.ctrl[:] = [0.12, 0.08, -0.03, deg(5), 0,
                 deg(20), deg(75), deg(55), deg(70), deg(60), deg(75),
                 deg(55), deg(70), deg(50), deg(65)]
    for _ in range(int(2/dt)): mujoco.mj_step(m, d)

    writer = imageio.get_writer(str(OUT/"demo.mp4"), fps=fps, quality=8, macro_block_size=1)
    spf = max(1, int((1/fps)/dt))
    fc = 0

    def rec(steps, ctrl_fn, title, sub):
        nonlocal fc
        for i in range(steps):
            a = min(1.0, i/max(1,steps-1))
            d.ctrl[:] = np.array(ctrl_fn(a))
            mujoco.mj_step(m, d)
            if i % spf == 0:
                renderer.update_scene(d)
                writer.append_data(overlay(renderer.render(), title, sub, d.time, d.ncon,
                    [float(d.qpos[14]), float(d.qpos[15]), float(d.qpos[16])]))
                fc += 1

    rec(int(2/dt), lambda a: [0.12,0.08,-0.03+0.10*a,deg(5),0,deg(20),deg(75),deg(55),deg(70),deg(60),deg(75),deg(55),deg(70),deg(50),deg(65)],
        "Phase 3: Lift Vial", "Five-finger grasp lifts vial off table")
    print(f"  Lift: {fc}f, vz={d.qpos[16]:.3f}")

    rec(int(6/dt), lambda a: [0.12+0.54*a,0.08-0.18*a,0.07,deg(5),0,deg(20),deg(75),deg(55),deg(70),deg(60),deg(75),deg(55),deg(70),deg(50),deg(65)],
        "Phase 4: Transport to Kit", "Vial carried across workspace")
    print(f"  Transport: {fc}f, vx={d.qpos[14]:.3f}")

    rec(int(1.5/dt), lambda a: [0.66,-0.10,0.07-0.03*a,0,0,0,0,0,0,0,0,0,0,0,0],
        "Phase 5: Release into Kit", "Fingers open — dose delivered")
    print(f"  Release: {fc}f, vx={d.qpos[14]:.3f}")

    rec(int(1.5/dt), lambda a: [0.66*(1-a)+0.05*a,-0.10*(1-a),0.07*(1-a),0,0,0,0,0,0,0,0,0,0,0,0],
        "Task Complete: Vial Delivered", "DexAid RescueHand v4 — Real MuJoCo Physics")
    print(f"  Home: {fc}f")

    writer.close()
    renderer.update_scene(d)
    imageio.imwrite(str(OUT/"poster.png"), overlay(renderer.render(),
        "DexAid RescueHand v4", "Real MuJoCo · Working Grasp · Kit Assembly", d.time, d.ncon,
        [float(d.qpos[14]),float(d.qpos[15]),float(d.qpos[16])]))

    met = {"success": float(d.qpos[14])>0.4, "frames": fc, "fps": fps,
           "duration_s": round(fc/fps,1), "rendering": "MuJoCo native GLFW via Xvfb",
           "vial_delivered_x": round(float(d.qpos[14]),4), "vial_z": round(float(d.qpos[16]),4),
           "actuators": 15, "sensors": int(m.nsensor), "nq": int(m.nq)}
    (OUT/"metrics.json").write_text(json.dumps(met, indent=2))
    (OUT/"mujoco_check.json").write_text(json.dumps(
        {"mujoco_loaded":True,"nq":m.nq,"nu":m.nu,"nsensor":m.nsensor,"timestep":dt}))
    print(f"\nDONE: {(OUT/'demo.mp4').stat().st_size/1e6:.1f}MB, {fc}f, {fc/fps:.0f}s, delivered={met['success']}")

if __name__ == "__main__": main()
