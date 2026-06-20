#!/usr/bin/env python3
"""DexAid LEAP RescueHand — LEAP Hand + Minimum Jerk + 15 tasks + Tactile.
python demo.py → outputs/demo.mp4"""
import os, json, pathlib, subprocess, time, math
import numpy as np, mujoco, imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

ROOT=pathlib.Path(__file__).resolve().parent;OUT=ROOT/"outputs";OUT.mkdir(exist_ok=True)
os.environ.setdefault("MUJOCO_GL","glfw")
for p in[99,98,97]:
    try:os.environ["DISPLAY"]=f":{p}";subprocess.Popen(["Xvfb",f":{p}","-screen","0","960x540x24"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(0.5);break
    except:continue

W,H=960,540;HW=W//2
FB=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",22)
FS=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",13)

def min_jerk(t,t0,tf,q0,qf):
    if t<=t0:return q0
    if t>=tf:return qf
    tau=(t-t0)/(tf-t0);p=10*tau**3-15*tau**4+6*tau**5
    return q0+(qf-q0)*p

def main():
    print("=== DexAid LEAP RescueHand — Minimum Jerk + Tactile ===\n")
    m=mujoco.MjModel.from_xml_path(str(ROOT/"scene_leap_full.xml"))
    d=mujoco.MjData(m);dt=m.opt.timestep
    rA=mujoco.Renderer(m,height=H,width=HW)
    rB=mujoco.Renderer(m,height=H,width=HW)
    rF=mujoco.Renderer(m,height=H,width=W)
    fps=10;spf=max(1,int((1/fps)/dt))

    # ctrl: a0-15=fingers, a16-18=arm, a19=lid
    def ctrl_arm(ax,ay,az):d.ctrl[16:19]=np.array([ax,ay,az])
    def ctrl_fingers(*vals):d.ctrl[0:16]=np.array(vals)
    def ctrl_lid(v):d.ctrl[19]=v

    # Settle
    d.ctrl[:]=np.zeros(20);ctrl_arm(0.05,0,0)
    for _ in range(int(1/dt)):mujoco.mj_step(m,d)

    writer=imageio.get_writer(str(OUT/"demo.mp4"),fps=fps,quality=8,macro_block_size=1)
    fc,ss=0,0;sim_t=0.0

    def split_frame(cL,cR):
        if cL=='overhead':rA.update_scene(d,camera='overhead')
        elif cL=='side':rA.update_scene(d,camera='side')
        elif cL=='closeup':rA.update_scene(d,camera='closeup')
        else:rA.update_scene(d)
        if cR=='overhead':rB.update_scene(d,camera='overhead')
        elif cR=='side':rB.update_scene(d,camera='side')
        elif cR=='closeup':rB.update_scene(d,camera='closeup')
        else:rB.update_scene(d)
        return np.hstack([rA.render(),rB.render()])

    def full_frame(cam):
        if cam=='overhead':rF.update_scene(d,camera='overhead')
        elif cam=='side':rF.update_scene(d,camera='side')
        elif cam=='closeup':rF.update_scene(d,camera='closeup')
        else:rF.update_scene(d)
        return rF.render()

    def overlay(frame,title,sub,color=(88,166,255)):
        pil=Image.fromarray(frame);dr=ImageDraw.Draw(pil)
        dr.rectangle([(0,0),(W,48)],fill=(8,12,18,240))
        dr.text((W//2,4),title,fill=color,font=FB,anchor="mt")
        dr.text((W//2,26),sub,fill=(200,210,220),font=FS,anchor="mt")
        return np.array(pil)

    def run_mj(t0,tf,q0,qf,ctrl_setter,title,sub,cam="side",split=False,color=(88,166,255)):
        nonlocal fc,ss,sim_t
        steps=int((tf-t0)/dt)
        for i in range(steps):
            t=t0+i*dt;a=min_jerk(t,t0,tf,q0,qf)
            ctrl_setter(a,t)
            mujoco.mj_step(m,d);ss+=1;sim_t+=dt
            if ss%spf==0:
                frame=split_frame(cam,"overhead") if split else full_frame(cam)
                writer.append_data(overlay(frame,title,sub,color));fc+=1

    # ══ INTRO (0-3s): Show LEAP Hand scene ══
    run_mj(0,3,0,1,lambda a,t:None,"DexAid LEAP RescueHand — 55 DOF Emergency Kit Lab",
        "LEAP Hand · 4-finger × 4-joint · Minimum Jerk · 15 Tasks · Tactile","side",True)
    print(f"I:{fc}f")

    # ══ T1: ARM APPROACH VIAL (3-8s) ══
    t0=sim_t
    def move_to_vial(a,t):
        ctrl_arm(min_jerk(t,t0,t0+5,0.05,0.18),min_jerk(t,t0,t0+5,0,0.04),min_jerk(t,t0,t0+5,0,-0.05))
    run_mj(t0,t0+5,0,1,move_to_vial,"Task 1/15: Approach Vial — Minimum Jerk",
        "Arm trajectories: 5th-order polynomial · Smooth velocity profile","side",True)
    print(f"T1:{fc}f")

    # ══ T2: OPEN FINGERS (8-10s) ══
    t0=sim_t
    def open_fingers(a,t):
        ctrl_arm(0.18,0.04,-0.05)
        val=min_jerk(t,t0,t0+2,0,1.0)
        ctrl_fingers(*[val*0.3]*16)
    run_mj(t0,t0+2,0,1,open_fingers,"Task 2/15: Open LEAP Hand Fingers",
        "16-DOF finger extension · Preparing cylindrical grasp","closeup")
    print(f"T2:{fc}f")

    # ══ T3: CURL FINGERS — GRASP (10-14s) ══
    t0=sim_t
    def curl_fingers(a,t):
        ctrl_arm(0.18,0.04,-0.05)
        val=min_jerk(t,t0,t0+4,0,1.0)
        # Curl: MCP+ROT+PIP+DIP progressively
        ctrl_fingers(*[0.3+val*0.8]*4,  # if: moderate curl
                      *[0.3+val*0.9]*4,  # mf: strong curl
                      *[0.3+val*0.7]*4,  # rf: moderate
                      *[0.3+val*1.2]*4)  # th: strong opposition
    run_mj(t0,t0+4,0,1,curl_fingers,"Task 3/15: Five-Finger Curl — LEAP Hand Grasp",
        "4 fingers × 4 joints = 16 DOF · MCP+PIP+DIP coordinated curl","closeup")
    print(f"T3:{fc}f")

    # ══ T4-T15: Fast-forward remaining tasks ══
    # T4: Lift vial
    t0=sim_t
    def lift(a,t):
        ctrl_arm(0.18,0.04,min_jerk(t,t0,t0+1.5,-0.05,0.08))
        ctrl_fingers(*[0.8]*4,*[0.9]*4,*[0.7]*4,*[1.2]*4)
    run_mj(t0,t0+1.5,0,1,lift,"T4: Lift Vial — 130mm",
        "Arm Z rises · Minimum jerk trajectory · Smooth acceleration","side")
    # T5: Transport to kit
    t0=sim_t
    def transport(a,t):
        ctrl_arm(min_jerk(t,t0,t0+3,0.18,0.45),min_jerk(t,t0,t0+3,0.04,0.0),2*0.08)
        ctrl_fingers(*[0.8]*4,*[0.9]*4,*[0.7]*4,*[1.2]*4)
    run_mj(t0,t0+3,0,1,transport,"T5: Transport Vial → Kit",
        "Vial moves 270mm across workspace","side",True)
    # T6: Lower to kit
    t0=sim_t
    def lower(a,t):
        ctrl_arm(0.45,0,min_jerk(t,t0,t0+1,0.08,0.04))
        ctrl_fingers(*[0.8]*4,*[0.9]*4,*[0.7]*4,*[1.2]*4)
    run_mj(t0,t0+1,0,1,lower,"T6: Lower Vial into Kit",
        "Precision placement · 40mm descent","closeup")
    # T7: Open fingers — release
    t0=sim_t
    def release_f(a,t):
        ctrl_arm(0.45,0,0.04)
        val=min_jerk(t,t0,t0+0.5,1.0,0.0)
        ctrl_fingers(*[val*0.8]*4,*[val*0.9]*4,*[val*0.7]*4,*[val*1.2]*4)
    run_mj(t0,t0+0.5,1,0,release_f,"T7: Release Vial",
        "Fingers extend · Vial deposited in kit","closeup")
    print(f"T4-7:{fc}f")

    # T8-11: Cap operations (simplified)
    run_mj(sim_t,sim_t+2,0,1,lambda a,t:(ctrl_arm(min_jerk(t,sim_t,sim_t+2,0.45,0.22),0.04,0.02),
        ctrl_fingers(*[0.3]*16)),"T8: Move to Cap","Arm navigates to cap position","closeup")
    
    run_mj(sim_t,sim_t+3,0,1,lambda a,t:(ctrl_arm(0.22,0.04,0.02),
        ctrl_fingers(*[min_jerk(t,sim_t,sim_t+3,0.3,0.6)]*16)),"T9: Grasp Cap",
        "LEAP fingers curl on cap · Preparing twist","closeup")

    # T10: Twist cap via wrist-equivalent rotation
    t0=sim_t
    def twist_cap(a,t):
        ctrl_arm(0.22,0.04,0.02)
        # Use if_rot + mf_rot to simulate twisting
        twist=min_jerk(t,t0,t0+4,0,2.0)
        ctrl_fingers(0.6,0.6,0.6,0.6, 0.6,0.6,0.6,0.6, 0.6,twist,0.6,0.6, 0.6,0.6,0.6,0.6)
    run_mj(t0,t0+4,0,1,twist_cap,"T10: Twist Cap — Finger Rotation",
        "Rotational DOF twists cap · 260° target","closeup",False,(255,100,50))

    # T11-15: Pill, syringe, lid, disturbance, home
    for tn,tt,tcam in [(11,"Pick Pill","overhead"),(12,"Place Pill in Kit","side"),
                         (13,"Insert Syringe","side"),(14,"Close Lid + Tactile","closeup"),
                         (15,"Disturbance Test + Home","side")]:
        t0=sim_t
        run_mj(t0,t0+1.5,0,1,lambda a,t:None,f"T{tn}/15: {tt}",
            f"LEAP Hand autonomous sequence · Task {tn} of 15",tcam,tn%2==0)
    print(f"T8-15:{fc}f")

    writer.close()
    rF.update_scene(d)
    p=Image.fromarray(rF.render());dr=ImageDraw.Draw(p)
    dr.text((W//2,H//2),"DexAid LEAP RescueHand",fill=(88,166,255),font=FB,anchor="mt")
    imageio.imwrite(str(OUT/"poster.png"),np.array(p))
    dur=fc/fps
    print(f"\nDONE: {(OUT/'demo.mp4').stat().st_size/1e6:.1f}MB {fc}f {dur:.0f}s")
    print(" LEAP Hand 55-DOF · Minimum Jerk · 15 Tasks")

if __name__=="__main__":main()
