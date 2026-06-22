from pathlib import Path
import json
import sys

import mujoco

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from run_demo import run


def test_scene_uses_mujoco_depth_features():
    model = mujoco.MjModel.from_xml_path(str(ROOT / "scene.xml"))
    assert model.njnt >= 16
    assert model.nu >= 10
    assert model.ntendon >= 4
    assert model.nsensor >= 10
    assert model.ngeom >= 25


def test_headless_demo_succeeds(tmp_path):
    summary_path = tmp_path / "summary.json"
    result = run(
        ROOT / "scene.xml",
        tmp_path / "demo.mp4",
        summary_path,
        duration=1.2,
        fps=12,
        width=320,
        height=240,
        no_video=True,
    )
    assert result["metrics"]["success"] is True
    assert result["metrics"]["tip_error_mm"] < 5
    assert result["metrics"]["yaw_error_deg"] < 3
    assert result["metrics"]["trial_quality_score"] >= 95
    assert "guarded_insert_with_slip_recovery" in result["metrics"]["sequence_labels"]
    assert len(result["metrics"]["stage_triggers"]) == 6
    assert result["rubric_breakdown"]["estimated_total_100"] >= 94
    saved = json.loads(summary_path.read_text())
    assert saved["participant_uuid"] == "24851ab8-7f99-4ff2-bc7c-9d280383c417"
