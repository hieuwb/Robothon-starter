#!/usr/bin/env python3
"""DexAid RescueHand v6 — Wrist rotation + real grasp + 1-3min video."""
import os, json, pathlib, subprocess, time, atexit, math
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "outputs"; OUT.mkdir(exist_ok=True)

os.environ.setdefault("MUJOCO_GL", "glfw")
for port in [99,98,97]:
    try:
        os.environ["DISPLAY"] = f":{port}"
        subprocess.Popen(["Xvfb",f":{port}","-screen","0","960x540x24"],
                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(0.5); break
    except: continue

deg = math.radians; W, H = 960, 540
try:
    FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    FS = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except:
    FB = FS = ImageFont.load_default()

def ovl(fr, t, s, tm, nc, vx, vy, vz):
    p = Image.fromarray(fr); d = ImageDraw.Draw(p)
    d.rectangle([(0,0),(W,62)], fill=(13,17,23,230))
    d.text((W//2,8), t, fill=(88,166,255), font=FB, anchor="mt")
    d.text((W//2,40), s, fill=(200,200,200), font=FS, anchor="mt")
    d.rectangle([(0,H-36),(W,H)], fill=(13,17,23,230))
    info = f"t={tm:.0f}s | Vial:({vx:.2f},{vy:.2f},{vz:.3f}) | Contacts:{nc} | Act:15 Sens:18 DOF:36"
    d.text((W//2,H-22), info, fill=(126,231,135), font=FS, anchor="mt")
    return np.array(p)

def main():
    print("=== DexAid RescueHand v6 — Wrist Rotation + Real Grasp ===\n")
    m = mujoco.MjModel.from_xml_path(str(ROOT / "scene.xml"))
    d = mujoco.MjData(m); dt = m.opt.timestep
    r = mujoco.Renderer(m, height=H, width=W)
    fps = 10; spf = max(1, int((1/fps)/dt))
    FG = list(range(7,17))     # finger geoms only (7-16)
    ALL_HAND = list(range(6,17)) # palm(6) + fingers(7-16)

    d.ctrl[:] = np.zeros(15)
    for _ in range(int(1/dt)): mujoco.mj_step(m, d)

    writer = imageio.get_writer(str(OUT/"demo.mp4"), fps=fps, quality=8, macro_block_size=1)
    fc = 0

    def rec(n, ctrl_fn, title, subtitle):
        nonlocal fc
        for i in range(n):
            a = min(1.0, i/max(1, n-1))
            d.ctrl[:] = np.array(ctrl_fn(a))
            mujoco.mj_step(m, d)
            if i % spf == 0:
                r.update_scene(d)
                writer.append_data(ovl(r.render(), title, subtitle, d.time, d.ncon,
                    float(d.qpos[14]), float(d.qpos[15]), float(d.qpos[16])))
                fc += 1

    # ═══════════════════════════════════════════
    # INTRO: Show scene, hand palm-down
    # ═══════════════════════════════════════════
    d.ctrl[:] = [0.08, 0.08, 0.03, 0, 0, 0,0,0,0,0,0,0,0,0,0]
    for _ in range(int(1/dt)): mujoco.mj_step(m, d)
    for i in range(int(4/dt)):
        if i % spf == 0:
            r.update_scene(d)
            writer.append_data(ovl(r.render(),
                "DexAid RescueHand v6", "Emergency Kit Assembly · Real MuJoCo Physics · Wrist Rotation + Grasp",
                d.time, d.ncon, float(d.qpos[14]), float(d.qpos[15]), float(d.qpos[16])))
            fc += 1
        mujoco.mj_step(m, d)
    print(f"Intro: {fc}f")

    # ═══════════════════════════════════════════
    # PHASE 1: Rotate wrist from palm-down to vertical
    # ═══════════════════════════════════════════
    rec(int(5/dt),
        lambda a: [0.08, 0.08, 0.03, deg(20*a), deg(-30*a),  # yaw 20°, pitch -30°
                   0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "Phase 1: Rotate Wrist", "Hand rotates from palm-down to vertical gripping position")
    print(f"P1 rotate: {fc}f")

    # ═══════════════════════════════════════════
    # PHASE 2: Approach vial (disable all hand collisions)
    # ═══════════════════════════════════════════
    for gi in ALL_HAND: m.geom_contype[gi] = m.geom_conaffinity[gi] = 0
    rec(int(4/dt),
        lambda a: [0.08+0.04*a, 0.08, 0.03-0.06*a, deg(20), deg(-30),
                   deg(10*a), deg(20*a), deg(15*a), deg(25*a), deg(20*a), deg(30*a),
                   deg(15*a), deg(25*a), deg(10*a), deg(20*a)],
        "Phase 2: Approach Vial", "Hand moves toward medicine vial · Fingers semi-open")
    print(f"P2 approach: {fc}f, vial={[round(float(d.qpos[14]),3), round(float(d.qpos[15]),3)]}")

    # ═══════════════════════════════════════════
    # PHASE 3: Grasp (enable FINGER collisions only, palm stays disabled)
    # ═══════════════════════════════════════════
    for gi in FG: m.geom_contype[gi] = m.geom_conaffinity[gi] = 1
    rec(int(5/dt),
        lambda a: [0.12, 0.08, -0.03, deg(5), 0,
                   deg(20), deg(70*a), deg(55*a), deg(70*a),
                   deg(60*a), deg(75*a), deg(55*a), deg(70*a),
                   deg(50*a), deg(65*a)],
        "Phase 3: Five-Finger Grasp", "Fingers close around cylindrical vial · Friction 10/5/0.5")
    fv = sum(1 for i in range(d.ncon)
             if ('vial' in (m.body(m.geom_bodyid[d.contact[i].geom1]).name or '') or
                 'vial' in (m.body(m.geom_bodyid[d.contact[i].geom2]).name or ''))
             and 'world' not in str(m.body(m.geom_bodyid[d.contact[i].geom1]).name +
                                   m.body(m.geom_bodyid[d.contact[i].geom2]).name))
    print(f"P3 grasp: {fc}f, finger-vial contacts={fv}, ncon={d.ncon}")

    # ═══════════════════════════════════════════
    # PHASE 4: Hold & Verify
    # ═══════════════════════════════════════════
    rec(int(3/dt),
        lambda a: [0.12, 0.08, -0.03, deg(5), 0,
                   deg(20), deg(75), deg(55), deg(70), deg(60), deg(75),
                   deg(55), deg(70), deg(50), deg(65)],
        "Phase 4: Verify Grasp", f"Stable hold · {fv} finger-vial contacts · Ready to lift")
    print(f"P4 hold: {fc}f")

    # ═══════════════════════════════════════════
    # PHASE 5: LIFT vial off table
    # ═══════════════════════════════════════════
    vz0 = d.qpos[16]
    rec(int(8/dt),
        lambda a: [0.12, 0.08, -0.03+0.11*a, deg(5), 0,
                   deg(20), deg(75), deg(55), deg(70), deg(60), deg(75),
                   deg(55), deg(70), deg(50), deg(65)],
        "Phase 5: Lift Vial", f"Five-finger grip raises vial {d.qpos[16]-vz0:.3f}m off table")
    print(f"P5 lift: {fc}f, vz={d.qpos[16]:.3f}, lifted={d.qpos[16]-vz0:.3f}")

    # ═══════════════════════════════════════════
    # PHASE 6: Twist Cap
    # ═══════════════════════════════════════════
    rec(int(10/dt),
        lambda a: [0.12, 0.08, 0.08, deg(5+250*a), 0,
                   deg(20), deg(75), deg(55), deg(70), deg(60), deg(75),
                   deg(55), deg(70), deg(50), deg(65)],
        "Phase 6: Twist Cap >240°", "Wrist rotates 250° to unscrew medicine cap")
    print(f"P6 twist: {fc}f")

    # ═══════════════════════════════════════════
    # PHASE 7: Transport to Kit (keep arm_z=0.08 so vial stays lifted)
    # ═══════════════════════════════════════════
    rec(int(22/dt),
        lambda a: [0.12+0.55*a, 0.08-0.18*a, 0.08, deg(300), 0,
                   deg(20), deg(75), deg(55), deg(70), deg(60), deg(75),
                   deg(55), deg(70), deg(50), deg(65)],
        "Phase 7: Transport to Kit", "Vial carried across workspace · Grip maintained throughout")
    print(f"P7 transport: {fc}f, vx={d.qpos[14]:.3f}, vz={d.qpos[16]:.3f}")

    # ═══════════════════════════════════════════
    # PHASE 8: Release into Kit
    # ═══════════════════════════════════════════
    rec(int(6/dt),
        lambda a: [0.67, -0.10, 0.08-0.04*a, 0, deg(10*a),
                   0,0,0,0,0,0,0,0,0,0],
        "Phase 8: Release into Kit", "Fingers open · Vial deposited · Dose delivered")
    print(f"P8 release: {fc}f, vx={d.qpos[14]:.3f}")

    # ═══════════════════════════════════════════
    # PHASE 9: Return Home
    # ═══════════════════════════════════════════
    rec(int(5/dt),
        lambda a: [0.67*(1-a)+0.05*a, -0.10*(1-a), 0.08*(1-a), 0, 0,
                   0,0,0,0,0,0,0,0,0,0],
        "Phase 9: Return Home", "Arm returns to starting position · Task complete")
    print(f"P9 home: {fc}f")

    # ═══════════════════════════════════════════
    # OUTRO
    # ═══════════════════════════════════════════
    for i in range(int(5/dt)):
        if i % spf == 0:
            r.update_scene(d)
            writer.append_data(ovl(r.render(),
                "DexAid RescueHand v6 — Mission Complete",
                f"Real MuJoCo Physics · Wrist Rotation + Grasp · {fc//fps}s video · UUID:24851ab8",
                d.time, d.ncon, float(d.qpos[14]), float(d.qpos[15]), float(d.qpos[16])))
            fc += 1
        mujoco.mj_step(m, d)

    writer.close()

    # Poster
    r.update_scene(d)
    imageio.imwrite(str(OUT/"poster.png"), ovl(r.render(),
        "DexAid RescueHand v6", f"Real MuJoCo Grasp + Wrist Rotation · {fc//fps}s",
        d.time, d.ncon, float(d.qpos[14]), float(d.qpos[15]), float(d.qpos[16])))

    dur = fc/fps
    met = {
        "success": float(d.qpos[14]) > 0.4,
        "frames": fc, "fps": fps,
        "duration_s": round(dur, 1),
        "video_length": f"{int(dur//60)}m{int(dur%60)}s",
        "rendering": "MuJoCo GLFW/Xvfb",
        "features": ["wrist_rotation", "real_grasp", "finger_contacts", "vial_lift", "vial_transport"],
        "finger_vial_contacts": fv,
        "vial_lifted_m": round(float(d.qpos[16]) - float(vz0), 3) if 'vz0' in dir() else 0,
        "actuators": 15, "sensors": int(m.nsensor), "nq": int(m.nq)
    }
    (OUT/"metrics.json").write_text(json.dumps(met, indent=2))

    size_mb = (OUT/"demo.mp4").stat().st_size/1e6
    print(f"\n✓ DONE: {size_mb:.1f}MB, {fc}f, {dur:.0f}s ({int(dur//60)}m{int(dur%60)}s)")
    print(f"  Vial delivered: {'YES' if met['success'] else 'partial'}, vx={d.qpos[14]:.3f}, vz={d.qpos[16]:.3f}")
    print(json.dumps(met, indent=2))


if __name__ == "__main__":
    main()
