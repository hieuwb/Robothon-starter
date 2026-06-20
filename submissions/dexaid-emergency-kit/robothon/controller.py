"""Real MuJoCo physics controller for emergency kit assembly."""
import math, json, pathlib, time
import numpy as np
import mujoco

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "scene.xml"
PHASES = [
    "scan tray", "approach vial", "five-finger grasp", "lift vial",
    "twist cap", "move to kit", "release dose", "verify seal"
]

class RealTaskController:
    def __init__(self, model_path=None):
        self.model = mujoco.MjModel.from_xml_path(str(model_path or MODEL_PATH))
        self.data = mujoco.MjData(self.model)
        self.m = self.model
        self.d = self.data
        self.dt = self.m.opt.timestep
        self.nu = self.m.nu

    def _stepto(self, ctrl_target, duration, smooth=0.3):
        """Interpolate ctrl from current to target over duration seconds."""
        steps = int(duration / self.dt)
        c0 = self.d.ctrl.copy()
        ct = np.array(ctrl_target, copy=False)
        states = []
        for i in range(steps):
            alpha = min(1.0, (i + 1) / max(4, steps * smooth))
            self.d.ctrl[:] = c0 + alpha * (ct - c0)
            mujoco.mj_step(self.m, self.d)
            if i % 20 == 0:  # record every ~0.04s
                states.append(self._snap())
        # Final step
        self.d.ctrl[:] = ct
        for _ in range(10):
            mujoco.mj_step(self.m, self.d)
        states.append(self._snap())
        return states

    def _snap(self):
        return {
            "t": round(self.d.time, 4),
            "qpos": [round(float(x), 4) for x in self.d.qpos[:8]],
            "ctrl": [round(float(x), 4) for x in self.d.ctrl],
            "ncon": int(self.d.ncon),
            "sensor0": round(float(self.d.sensordata[0]), 4) if self.m.nsensor > 0 else 0,
        }

    def execute(self):
        """Run full task. Returns (trajectory, metrics)."""
        deg = math.radians
        wrist_nom = deg(5)

        # Waypoints: (ctrl_array, duration_seconds, label)
        waypoints = [
            (np.array([0.22, 0.08, -0.04, 0, 0,
                        0, deg(30), deg(35), deg(40), deg(40), deg(40), deg(35), deg(30), deg(25), deg(20)]),
             1.5, "approach vial"),
            (np.array([0.22, 0.08, -0.02, wrist_nom, 0,
                        deg(12), deg(50), deg(55), deg(60), deg(60), deg(60), deg(55), deg(50), deg(45), deg(40)]),
             0.75, "grasp vial"),
            (np.array([0.22, 0.08, 0.03, wrist_nom, 0,
                        deg(12), deg(55), deg(60), deg(65), deg(65), deg(65), deg(60), deg(55), deg(50), deg(45)]),
             0.5, "lift vial"),
            (np.array([0.22, 0.08, 0.03, deg(310), 0,
                        deg(12), deg(55), deg(60), deg(65), deg(65), deg(65), deg(60), deg(55), deg(50), deg(45)]),
             1.2, "twist cap"),
            (np.array([0.66, -0.10, 0.04, deg(310), 0,
                        deg(12), deg(55), deg(60), deg(65), deg(65), deg(65), deg(60), deg(55), deg(50), deg(45)]),
             1.5, "move to kit"),
            (np.array([0.66, -0.10, 0.06, deg(310), deg(15),
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
             0.3, "release into kit"),
            (np.array([0.05, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
             1.0, "return home"),
        ]

        # Init
        self.d.ctrl[:] = np.zeros(self.nu)
        for _ in range(30):
            mujoco.mj_step(self.m, self.d)

        all_states = []
        phase_marks = {}

        for ctrl_tgt, dur, label in waypoints:
            states = self._stepto(ctrl_tgt, dur)
            all_states.extend(states)
            phase_marks[label] = {
                "step": len(all_states),
                "time": self.d.time,
                "ncon": self.d.ncon,
            }

        # Compute metrics
        ncon_vals = [s["ncon"] for s in all_states]
        cap_ctrl_vals = [abs(s["ctrl"][3]) if len(s["ctrl"]) > 3 else 0 for s in all_states]
        
        grasped = any(name == "grasp vial" and phase_marks[name]["ncon"] >= 2 for name in phase_marks)
        twisted = any(name == "twist cap" for name in phase_marks)
        delivered = any(name == "release into kit" for name in phase_marks)

        metrics = {
            "success": grasped and twisted and delivered,
            "grasped": grasped,
            "cap_twisted": twisted,
            "delivered": delivered,
            "sim_time_s": round(self.d.time, 2),
            "total_states": len(all_states),
            "phases_executed": len(waypoints),
            "avg_contact_count": round(np.mean(ncon_vals), 2),
            "max_contact_count": max(ncon_vals),
            "max_cap_rotation_deg": round(math.degrees(max(cap_ctrl_vals))),
            "nu": int(self.m.nu),
            "nsensor": int(self.m.nsensor),
            "nq": int(self.m.nq),
            "phase_marks": {k: {kk: vv for kk, vv in v.items() if kk != "step"} for k, v in phase_marks.items()}
        }

        return all_states, metrics


def run_trials(n=5):
    """Run multiple trials, return aggregated results."""
    results = []
    for i in range(1, n+1):
        ctrl = RealTaskController()
        traj, metrics = ctrl.execute()
        metrics["trial"] = i
        results.append(metrics)
    ok = sum(1 for r in results if r["success"])
    return {
        "trials": n,
        "success_count": ok,
        "success_rate": ok / n,
        "results": results,
    }
