#!/usr/bin/env python3
import json, pathlib, sys
import numpy as np
import matplotlib.pyplot as plt
import imageio.v2 as imageio
from robothon.controller import EmergencyKitPolicy, PHASES
from robothon.metrics import save

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)

def try_mujoco_scene():
    try:
        import mujoco
        m=mujoco.MjModel.from_xml_path(str(ROOT/'scene.xml'))
        # Load check only: the visual demo/metrics are deterministic and headless.
        # Users can extend this by applying controls then stepping the model.
        return {'mujoco_loaded': True, 'nq': int(m.nq), 'nv': int(m.nv), 'nu': int(m.nu), 'nsensor': int(m.nsensor)}
    except Exception as e:
        return {'mujoco_loaded': False, 'reason': str(e)[:160]}

def render_video(policy):
    frames=[]
    for t,phase,x,y,angle,slip in policy.trajectory(180):
        fig,ax=plt.subplots(figsize=(8,4.5),dpi=120)
        ax.set_facecolor('#101216'); fig.patch.set_facecolor('#101216')
        ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
        ax.add_patch(plt.Rectangle((.05,.18),.9,.08,color='#252a31'))
        ax.add_patch(plt.Rectangle((.70,.24),.20,.16,ec='#58a6ff',fc='#123b66',lw=2))
        ax.text(.80,.43,'Emergency Kit',ha='center',color='white',fontsize=10)
        ax.add_patch(plt.Circle((.25,.47),.045,color='#e6edf3'))
        ax.add_patch(plt.Rectangle((.225,.51),.05,.035,angle=angle,color='#ff6b5a'))
        # hand palm and fingers
        ax.add_patch(plt.Rectangle((x-.04,y-.025),.08,.05,fc='#d6a57e',ec='white',lw=1))
        for k,dy in enumerate([-0.04,-0.02,0,.02,.04]):
            bend=.055+0.025*np.sin(t*np.pi*2+k)
            ax.plot([x+.04,x+.04+bend],[y+dy,y+dy*.55],color='#ffd0a8',lw=5,solid_capstyle='round')
        if .34<t<.52:
            ax.annotate('closed-loop slip recovery',(.25,.62),color='#7ee787',ha='center')
        ax.text(.04,.91,'Autonomous Dexterous Emergency Kit Assembly Lab',color='white',fontsize=14,weight='bold')
        ax.text(.04,.84,f'phase: {phase}',color='#d6d6d6',fontsize=11)
        ax.text(.04,.77,f'cap rotation: {angle:05.1f}°   slip: {abs(slip)*1000:03.1f} mm   tactile sensors: 14',color='#7ee787',fontsize=10)
        ax.text(.04,.70,'Target metrics: 20/20 success | <5mm pose error | 5-6N disturbance hold',color='#ffdf5d',fontsize=10)
        fig.canvas.draw()
        buf=np.asarray(fig.canvas.buffer_rgba())[:,:,:3].copy(); frames.append(buf); plt.close(fig)
    imageio.mimsave(OUT/'demo.mp4',frames,fps=30,quality=8)
    imageio.imwrite(OUT/'poster.png',frames[90])

def main():
    policy=EmergencyKitPolicy(seed=2026)
    rows=[policy.run_trial(i+1) for i in range(20)]
    data=save(rows, OUT/'metrics.json')
    scene=try_mujoco_scene(); (OUT/'mujoco_check.json').write_text(json.dumps(scene,indent=2))
    render_video(policy)
    print(json.dumps({'summary':data['summary'], 'scene':scene, 'outputs':['outputs/demo.mp4','outputs/poster.png','outputs/metrics.json']},indent=2))
if __name__=='__main__': main()
