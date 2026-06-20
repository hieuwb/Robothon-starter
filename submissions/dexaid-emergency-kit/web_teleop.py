#!/usr/bin/env python3
"""DexAid RescueHand v3 — Web-based real-time teleoperation server.
Open http://localhost:8095 in your browser to control the 5-finger hand
+ 3-axis arm + wrist in real-time MuJoCo physics with live sensor feedback.
"""
import os, json, time, math, pathlib, threading, subprocess, atexit, sys
import numpy as np
import mujoco

ROOT = pathlib.Path(__file__).resolve().parent

# Start Xvfb
os.environ.setdefault("MUJOCO_GL", "glfw")
XVFB = None
for port in [99, 98, 97]:
    try:
        os.environ["DISPLAY"] = f":{port}"
        XVFB = subprocess.Popen(["Xvfb", f":{port}", "-screen", "0", "960x540x24"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5); break
    except: continue
if XVFB:
    atexit.register(lambda: XVFB.kill() if XVFB.poll() is None else None)

from flask import Flask, render_template_string
from flask_sock import Sock

# ── MuJoCo setup ──
m = mujoco.MjModel.from_xml_path(str(ROOT / "scene.xml"))
d = mujoco.MjData(m)
renderer = mujoco.Renderer(m, height=540, width=960)
dt = m.opt.timestep

app = Flask(__name__)
sock = Sock(app)
sim_lock = threading.Lock()

HTML = r"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>DexAid RescueHand Web Teleop</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:monospace}
body{background:#0d1117;color:#c9d1d9;display:flex;flex-direction:column;align-items:center;min-height:100vh}
h1{color:#58a6ff;margin:10px 0;font-size:20px}
#container{display:flex;gap:10px;padding:10px}
#video{border:2px solid #30363d;border-radius:6px;width:960px;height:540px;background:#161b22}
#panel{display:flex;flex-direction:column;gap:8px;min-width:280px;max-width:320px}
.panel-section{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px}
.panel-title{color:#58a6ff;font-size:13px;font-weight:bold;margin-bottom:6px}
.btn-row{display:flex;gap:4px;flex-wrap:wrap;margin:3px 0}
.btn{padding:6px 10px;border:1px solid #30363d;border-radius:4px;background:#21262d;color:#c9d1d9;
  cursor:pointer;font-size:12px;user-select:none;min-width:36px;text-align:center}
.btn:hover{background:#30363d}.btn:active{background:#58a6ff;color:#000}
.btn.active{background:#238636;border-color:#2ea043}
.btn.danger{background:#da3633;border-color:#f85149}
.slider-row{display:flex;align-items:center;gap:6px;margin:3px 0}
.slider-row label{font-size:11px;color:#8b949e;min-width:50px;text-align:right}
.slider-row input{flex:1}
.slider-row span{font-size:11px;color:#7ee787;min-width:40px}
#status{font-size:11px;color:#8b949e;margin-top:6px;line-height:1.5}
.badge{display:inline-block;padding:2px 6px;border-radius:3px;font-size:10px;margin:2px}
.badge-ok{background:#238636;color:#fff}.badge-warn{background:#d29922;color:#000}
</style></head><body>
<h1>🤖 DexAid RescueHand · Web Teleop · Real MuJoCo Physics</h1>
<div id="container">
  <img id="video" src="" alt="MuJoCo stream">
  <div id="panel">
    <div class="panel-section">
      <div class="panel-title">⚙️ Arm (WASD + QE)</div>
      <div class="btn-row">
        <button class="btn" data-key="q">Q▲Z</button>
        <button class="btn" data-key="w">W▲X</button>
        <button class="btn" data-key="e">E▼Z</button>
      </div>
      <div class="btn-row">
        <button class="btn" data-key="a">A◄Y</button>
        <button class="btn" data-key="s">S▼X</button>
        <button class="btn" data-key="d">D►Y</button>
      </div>
    </div>
    <div class="panel-section">
      <div class="panel-title">🖐️ Wrist (JL + IK)</div>
      <div class="btn-row">
        <button class="btn" data-key="j">J◄Yaw</button>
        <button class="btn" data-key="l">LYaw►</button>
      </div>
      <div class="btn-row">
        <button class="btn" data-key="i">I▲Pitch</button>
        <button class="btn" data-key="k">K▼Pitch</button>
      </div>
    </div>
    <div class="panel-section">
      <div class="panel-title">✋ Fingers (1-5 / F / R / T)</div>
      <div class="btn-row">
        <button class="btn" data-key="1">1 Thumb</button>
        <button class="btn" data-key="2">2 Index</button>
        <button class="btn" data-key="3">3 Middle</button>
        <button class="btn" data-key="4">4 Ring</button>
        <button class="btn" data-key="5">5 Little</button>
      </div>
      <div class="btn-row">
        <button class="btn" data-key="f" style="background:#238636">F Grasp</button>
        <button class="btn" data-key="r" style="background:#da3633">R Release</button>
        <button class="btn" data-key="t" style="background:#d29922">T Twist</button>
        <button class="btn" data-key=" ">Space Home</button>
      </div>
    </div>
    <div id="status">🟢 Connected · Waiting for input...</div>
  </div>
</div>
<script>
const ws = new WebSocket("ws://" + location.host + "/ws");
const video = document.getElementById("video");
const statusEl = document.getElementById("status");
let pressed = {};
let streamTimer;

ws.onmessage = (e) => {
  if (e.data instanceof Blob) {
    const url = URL.createObjectURL(e.data);
    video.src = url;
    setTimeout(() => URL.revokeObjectURL(url), 50);
  } else {
    try {
      const msg = JSON.parse(e.data);
      if (msg.status) {
        statusEl.innerHTML = msg.status;
      }
    } catch(ex) {}
  }
};

ws.onclose = () => { statusEl.innerHTML = "🔴 Disconnected"; };
ws.onerror = () => { statusEl.innerHTML = "🔴 Connection error"; };

document.querySelectorAll(".btn[data-key]").forEach(btn => {
  const send = (down) => ws.send(JSON.stringify({key: btn.dataset.key, down}));
  btn.addEventListener("mousedown", () => { send(true); btn.classList.add("active"); });
  btn.addEventListener("mouseup", () => { send(false); btn.classList.remove("active"); });
  btn.addEventListener("mouseleave", () => { if(btn.classList.contains("active")){send(false);btn.classList.remove("active");}});
});

document.addEventListener("keydown", e => {
  if (pressed[e.key.toLowerCase()]) return;
  pressed[e.key.toLowerCase()] = true;
  ws.send(JSON.stringify({key: e.key, down: true}));
  document.querySelector(`.btn[data-key="${e.key.toLowerCase()}"]`)?.classList.add("active");
});
document.addEventListener("keyup", e => {
  pressed[e.key.toLowerCase()] = false;
  ws.send(JSON.stringify({key: e.key, down: false}));
  document.querySelector(`.btn[data-key="${e.key.toLowerCase()}"]`)?.classList.remove("active");
});
</script></body></html>"""


class TeleopState:
    def __init__(self):
        self.ctrl = np.array([0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.keys_down = set()
        self.twist_phase = 0
        self.step_count = 0

    def apply_key(self, key, down):
        key = key.lower()
        if down:
            self.keys_down.add(key)
        else:
            self.keys_down.discard(key)
        # Special single-action keys
        if key == "f" and down:  # Full grasp
            self.ctrl[5:] = np.radians([12, 55, 60, 65, 65, 65, 60, 55, 50, 45])
        elif key == "r" and down:  # Release
            self.ctrl[5:] = 0
        elif key == "t" and down:  # Twist sequence
            self.twist_phase = (self.twist_phase + 1) % 3
            self.ctrl[3] = np.radians([0, 150, 300][self.twist_phase])
        elif key == " " and down:  # Home
            self.ctrl[:] = [0.05, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def update(self):
        step = 0.02
        active = self.keys_down

        if "w" in active: self.ctrl[0] = min(0.75, self.ctrl[0] + step)
        if "s" in active: self.ctrl[0] = max(0.01, self.ctrl[0] - step)
        if "d" in active: self.ctrl[1] = min(0.25, self.ctrl[1] + step * 0.5)
        if "a" in active: self.ctrl[1] = max(-0.25, self.ctrl[1] - step * 0.5)
        if "q" in active: self.ctrl[2] = min(0.25, self.ctrl[2] + step * 0.4)
        if "e" in active: self.ctrl[2] = max(-0.10, self.ctrl[2] - step * 0.4)

        deg = np.radians
        if "j" in active: self.ctrl[3] -= deg(5)
        if "l" in active: self.ctrl[3] += deg(5)
        if "i" in active: self.ctrl[4] = min(deg(35), self.ctrl[4] + deg(3))
        if "k" in active: self.ctrl[4] = max(deg(-35), self.ctrl[4] - deg(3))

        # Fingers toggle
        for i, finger_key in enumerate(["1","2","3","4","5"]):
            if finger_key in active:
                targets = [deg(25), deg(65), deg(70), deg(68), deg(60)]
                self.ctrl[5+i*2] = targets[i]
                if 5+i*2+1 < 15:
                    self.ctrl[5+i*2+1] = targets[i] * 0.85

        self.step_count += 1


state = TeleopState()

@app.route("/")
def index():
    return render_template_string(HTML)

@sock.route("/ws")
def ws_loop(ws):
    global state
    print("WebSocket connected")
    while True:
        try:
            msg = ws.receive(timeout=0.02)
            if msg:
                data = json.loads(msg)
                state.apply_key(data.get("key", ""), data.get("down", False))
        except Exception:
            pass

        with sim_lock:
            state.update()
            d.ctrl[:] = state.ctrl
            for _ in range(int(0.03 / dt)):
                mujoco.mj_step(m, d)
            renderer.update_scene(d)
            frame = renderer.render()

        # Send frame as JPEG
        import io, base64
        from PIL import Image
        img = Image.fromarray(frame)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        try:
            ws.send(buf.getvalue())
        except Exception:
            break

        if state.step_count % 30 == 0:
            status = (f"🟢 ncon={d.ncon} | arm=({state.ctrl[0]:.2f},{state.ctrl[1]:.2f},{state.ctrl[2]:.2f})"
                      f" | wrist={math.degrees(state.ctrl[3]):.0f}°"
                      f" | Fingers: {','.join(f'{math.degrees(state.ctrl[i]):.0f}' for i in range(5,15))}")
            try:
                ws.send(json.dumps({"status": status}))
            except Exception:
                break


def main():
    import webbrowser
    print("=" * 60)
    print("  DexAid RescueHand — Web Teleop Server")
    print(f"  Open: http://localhost:8095")
    print(f"  MuJoCo: {m.nq} DOF, {m.nu} actuators, {m.nsensor} sensors")
    print(f"  Controls: Keyboard or on-screen buttons")
    print("=" * 60)
    # Save teleop metadata
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "web_teleop_info.json").write_text(json.dumps({
        "mode": "web_teleop",
        "actuators": int(m.nu),
        "sensors": int(m.nsensor),
        "controls": "WASD+QE arm, JL wrist, IK pitch, 1-5 fingers, F grasp, R release, T twist, Space home",
        "url": "http://localhost:8095",
        "description": "Real-time browser-based teleoperation with MuJoCo physics streaming"
    }, indent=2))
    app.run(host="0.0.0.0", port=8095, debug=False, threaded=True)


if __name__ == "__main__":
    main()
