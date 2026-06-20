#!/usr/bin/env python3
"""Headless MuJoCo physics rollout with real rendering via Xvfb (streaming)."""
import os, json, pathlib, subprocess, time, atexit, math
import numpy as np
import mujoco
import imageio.v2 as imageio

ROOT = pathlib.Path(__file__).resolve().parent; OUT = ROOT / "outputs"; OUT.mkdir(exist_ok=True)
os.environ.setdefault("MUJOCO_GL", "glfw")
Xvfb = None
for port in [99,98,97]:
    try:
        os.environ["DISPLAY"] = f":{port}"
        Xvfb = subprocess.Popen(["Xvfb",f":{port}","-screen","0","960x540x24"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(0.5); break
    except: continue
if Xvfb: atexit.register(lambda: Xvfb.kill() if Xvfb.poll() is None else None)
deg = math.radians

def main():
    m = mujoco.MjModel.from_xml_path(str(ROOT / "scene.xml")); d = mujoco.MjData(m)
    renderer = mujoco.Renderer(m, height=540, width=960); dt = m.opt.timestep
    fps, seconds = 15, 40; spf = max(1, int((1/fps)/dt))
    home = np.array([0.05,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    wps = [
        (np.array([0.22,0.08,-0.04,0,0,0,deg(25),deg(30),deg(35),deg(35),deg(35),deg(30),deg(25),deg(20),deg(15)]), 4,12),
        (np.array([0.22,0.08,-0.02,deg(5),0,deg(10),deg(48),deg(52),deg(58),deg(58),deg(58),deg(52),deg(48),deg(42),deg(38)]), 14,22),
        (np.array([0.22,0.08,0.03,deg(300),0,deg(10),deg(52),deg(58),deg(62),deg(62),deg(62),deg(58),deg(52),deg(48),deg(42)]), 24,34),
        (np.array([0.66,-0.10,0.04,deg(300),0,deg(10),deg(52),deg(58),deg(62),deg(62),deg(62),deg(58),deg(52),deg(48),deg(42)]), 35,38),
        (np.array([0.66,-0.10,0.06,deg(300),deg(10),0,0,0,0,0,0,0,0,0,0]), 39,40),
    ]
    d.ctrl[:] = home
    for _ in range(int(1.5/dt)): mujoco.mj_step(m, d)
    c = home.copy(); states = []
    writer = imageio.get_writer(str(OUT / "mujoco_rollout.mp4"), fps=fps, quality=8, macro_block_size=1)
    for f in range(fps*seconds):
        sec = f/fps; tgt = home
        for wp, t0, t1 in wps:
            if t0 <= sec <= t1:
                x = (sec-t0)/max(0.01,t1-t0); alpha = 3*x**2 - 2*x**3
                tgt = home + alpha*(wp - home)
        c = c + 0.2*(tgt - c)
        for _ in range(spf): d.ctrl[:] = c; mujoco.mj_step(m, d)
        renderer.update_scene(d); writer.append_data(renderer.render())
        if f % 30 == 0: states.append({"f":f,"t":round(d.time,3),"ncon":d.ncon})
    writer.close()
    (OUT/"mujoco_rollout.json").write_text(json.dumps({"nu":m.nu,"nsensor":m.nsensor,"nq":m.nq,"states":states},indent=2))
    print(json.dumps({"ok":True,"video":"outputs/mujoco_rollout.mp4","nu":m.nu,"nsensor":m.nsensor}))
if __name__=="__main__": main()
