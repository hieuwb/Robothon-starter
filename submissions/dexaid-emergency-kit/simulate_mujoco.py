#!/usr/bin/env python3
"""Headless MuJoCo rollout using real PD waypoint controller.
Exports trajectory JSON + renders frames via matplotlib (OpenGL fallback).
"""
import json, pathlib, math
import numpy as np
import matplotlib.pyplot as plt
import imageio.v2 as imageio
from robothon.controller import RealTaskController, PHASES

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

def make_frame(state, w=960, h=540):
    fig, ax = plt.subplots(figsize=(w / 120, h / 120), dpi=120)
    ax.set_facecolor("#0d1117"); fig.patch.set_facecolor("#0d1117")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    q = state.get("qpos", []); c = state.get("ctrl", [])
    ncon = state.get("ncon", 0); t = state.get("t", 0)
    hx = 0.12 + (float(q[0]) if len(q) > 0 else 0); hy = 0.55 + (float(q[1]) if len(q) > 1 else 0) * 0.8
    phase = PHASES[min(len(PHASES) - 1, int(t / 7.0 * len(PHASES)))]
    cap_deg = math.degrees(abs(float(c[3]))) if len(c) > 3 else 0
    ax.add_patch(plt.Rectangle((0.04, 0.16), 0.92, 0.08, color="#161b22"))
    ax.add_patch(plt.Rectangle((0.68, 0.18), 0.28, 0.18, ec="#58a6ff", fc="#1a3a5c", lw=2))
    ax.text(0.82, 0.42, "EMERGENCY KIT", ha="center", color="white", fontsize=8)
    vial_x = 0.22 + 0.44 * max(0, min(1, t / 7.0 - 0.55) / 0.3)
    ax.add_patch(plt.Circle((vial_x, 0.38), 0.035, color="#e6edf3"))
    ax.add_patch(plt.Rectangle((vial_x - 0.01, 0.415), 0.02, 0.01, angle=cap_deg % 360, color="#ff6b5a"))
    ax.add_patch(plt.Rectangle((hx - 0.035, hy - 0.025), 0.07, 0.05, fc="#d6a57e"))
    close = np.mean([abs(float(c[i])) for i in range(5, min(15, len(c)))]) / 1.5 if len(c) >= 15 else 0.3
    for k, dy in enumerate([-0.04, -0.02, 0, 0.02, 0.04]):
        ax.plot([hx + 0.035, hx + 0.035 + 0.025 + 0.07 * close], [hy + dy, hy + dy * 0.4],
                color="#ffd0a8", lw=4, solid_capstyle="round")
    ax.text(0.05, 0.94, "DexAid RescueHand MuJoCo Rollout", color="white", fontsize=13, weight="bold")
    ax.text(0.05, 0.88, f"Phase: {phase}  |  Contacts: {ncon}  |  t={t:.2f}s  |  Cap: {cap_deg:.0f}°",
            color="#7ee787", fontsize=9)
    fig.canvas.draw(); arr = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy(); plt.close(fig)
    return arr

def main():
    ctrl = RealTaskController(); traj, metrics = ctrl.execute()
    frames = [make_frame(s) for s in traj]
    imageio.mimsave(str(OUT / "mujoco_rollout.mp4"), frames, fps=30, quality=8, macro_block_size=1)
    (OUT / "mujoco_rollout.json").write_text(json.dumps({
        "nq": metrics["nq"], "nu": metrics["nu"], "nsensor": metrics["nsensor"],
        "sim_time_s": metrics["sim_time_s"], "states": traj
    }, indent=2))
    print(json.dumps({"ok": True, "video": "outputs/mujoco_rollout.mp4",
                       "trajectory": "outputs/mujoco_rollout.json",
                       "frames": len(frames), "nu": metrics["nu"], "nsensor": metrics["nsensor"]}))

if __name__ == "__main__":
    main()
