#!/usr/bin/env python3
"""Headless MuJoCo rollout: loads scene.xml, applies actuator controls,
steps physics, records states/actions/sensors, and writes a video. If OpenGL
is unavailable, it falls back to a matplotlib state-trace video while keeping
all trajectory data from real MuJoCo stepping.
"""
import os, json, pathlib
os.environ.setdefault("MUJOCO_GL", "glfw")
import numpy as np
import imageio.v2 as imageio
import mujoco

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "outputs"; OUT.mkdir(exist_ok=True)
PHASES = ["scan tray","approach vial","five-finger pregrasp","grasp and lift","twist cap","place dose","insert syringe","close kit","verify seal"]

def ramp(t,a,b):
    if t<=a: return 0.0
    if t>=b: return 1.0
    x=(t-a)/(b-a); return x*x*(3-2*x)

def controls(t,nu):
    u=np.zeros(nu)
    u[0]=0.10+0.55*ramp(t,.05,.45); u[1]=0.10*(1-ramp(t,.25,.70))-.10*ramp(t,.65,.90)
    u[2]=0.02+0.08*ramp(t,.20,.35)-0.03*ramp(t,.72,.92); u[3]=np.deg2rad(35)*np.sin(2*np.pi*max(0,t-.35))*ramp(t,.35,.75); u[4]=np.deg2rad(-10+20*ramp(t,.45,.75))
    close=ramp(t,.22,.38)*(1-ramp(t,.82,.95)); twist=.35*np.sin(8*np.pi*t)*ramp(t,.40,.62)
    for i,v in enumerate([18,65,70,68,72,70,62,60,55,54], start=5):
        if i<nu: u[i]=np.deg2rad(close*(v+twist*10))
    return u

def make_trace_frame(state, w=960, h=540):
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(w/120,h/120),dpi=120)
    ax.set_facecolor('#101216'); fig.patch.set_facecolor('#101216'); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
    t=state['frame']/239; q=state['qpos_head']; ctrl=state['ctrl']
    ax.text(.04,.92,'MuJoCo stepped rollout (OpenGL fallback view)',color='white',fontsize=15,weight='bold')
    ax.text(.04,.84,f"phase: {state['phase']}   sim time: {state['time']:.2f}s",color='#7ee787',fontsize=12)
    ax.add_patch(plt.Rectangle((.08,.20),.84,.08,color='#252a31'))
    ax.add_patch(plt.Rectangle((.70,.30),.18,.12,ec='#58a6ff',fc='#123b66',lw=2)); ax.text(.79,.45,'kit',color='white',ha='center')
    hx=.12+.70*ramp(t,.05,.75); hy=.54+.08*np.sin(4*np.pi*t)
    ax.add_patch(plt.Rectangle((hx-.04,hy-.03),.08,.06,fc='#d6a57e',ec='white'))
    close=min(1,max(0,abs(ctrl[5])/70 if len(ctrl)>5 else 0))
    for k,dy in enumerate([-.045,-.022,0,.022,.045]):
        bend=.035+.055*close
        ax.plot([hx+.04,hx+.04+bend],[hy+dy,hy+dy*.5],color='#ffd0a8',lw=5,solid_capstyle='round')
    ax.add_patch(plt.Circle((.25,.48),.04,color='#e6edf3')); ax.add_patch(plt.Rectangle((.23,.52),.04,.03,angle=float(ctrl[3]) if len(ctrl)>3 else 0,color='#ff6b5a'))
    ax.text(.04,.12,'qpos[:8] '+np.array2string(np.array(q), precision=2), color='#d6d6d6', fontsize=9)
    fig.canvas.draw(); arr=np.asarray(fig.canvas.buffer_rgba())[:,:,:3].copy(); plt.close(fig); return arr

def main():
    model=mujoco.MjModel.from_xml_path(str(ROOT/'scene.xml')); data=mujoco.MjData(model)
    fps, seconds = 30, 8; frames=[]; states=[]; renderer=None
    try:
        renderer=mujoco.Renderer(model,height=540,width=960)
    except Exception as e:
        render_error=str(e)[:180]
    else:
        render_error=None
    spf=max(1,int((1/fps)/model.opt.timestep))
    for f in range(fps*seconds):
        t=f/(fps*seconds-1); data.ctrl[:]=controls(t,model.nu)
        for _ in range(spf): mujoco.mj_step(model,data)
        phase=PHASES[min(len(PHASES)-1,int(t*len(PHASES)))]
        st={"frame":f,"time":float(data.time),"phase":phase,"qpos_head":[float(x) for x in data.qpos[:min(8,model.nq)]],"ctrl":[float(x) for x in data.ctrl[:]],"sensor_head":[float(x) for x in data.sensordata[:min(8,model.nsensor)]]}
        states.append(st)
        if renderer:
            renderer.update_scene(data); frames.append(renderer.render())
        else:
            frames.append(make_trace_frame(st))
    imageio.mimsave(OUT/'mujoco_rollout.mp4',frames,fps=fps,quality=8,macro_block_size=1)
    (OUT/'mujoco_rollout.json').write_text(json.dumps({"frames":len(frames),"fps":fps,"nq":int(model.nq),"nv":int(model.nv),"nu":int(model.nu),"nsensor":int(model.nsensor),"render_fallback":bool(render_error),"render_error":render_error,"phases":PHASES,"states":states},indent=2))
    print(json.dumps({"ok":True,"video":"outputs/mujoco_rollout.mp4","trajectory":"outputs/mujoco_rollout.json","frames":len(frames),"nu":int(model.nu),"nsensor":int(model.nsensor),"render_fallback":bool(render_error)},indent=2))
if __name__=='__main__': main()
