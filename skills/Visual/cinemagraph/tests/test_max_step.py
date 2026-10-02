"""`--check` flags a snap anywhere in the loop, not only at the wrap.

A choreographed reset that runs over the last 5% of a beat has not finished on the beat's
last sampled frame, so the beat snaps back to rest at the boundary with the next beat. The
same page with the reset finished before the last frame passes. Needs Pillow and
Playwright (Chromium), like the renderer.

    python tests/test_max_step.py      (or: pytest tests/)
"""
import argparse
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

import render_loop  # noqa: E402
from flat_page import BEATS, H, W, page_html  # noqa: E402

FRAMES = 60
PER_BEAT = FRAMES // BEATS  # 20 frames per beat: the last sampled frame sits at q = 0.95


def render(reset):
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "flat.html"
        page.write_text(page_html(reset=reset), encoding="utf-8")
        a = argparse.Namespace(page=page, frames=FRAMES, width=W, height=H, scale=1.0, alpha=False)
        frames, _wrap = render_loop.render_frames(a)
    return frames


def test_too_short_reset_is_flagged_at_the_beat_boundary():
    report = render_loop.step_report(render(reset=(0.95, 1.0)))
    assert report["flagged"], report
    # the snap is the step from a beat's last frame to the next beat's first frame
    assert any(i % PER_BEAT == PER_BEAT - 1 for i in report["snaps"]), report


def test_reset_that_ends_by_the_last_frame_passes():
    # four frames, ending at (F-1)/F = 0.95: large steps, but a fade, not a snap
    report = render_loop.step_report(render(reset=(0.75, 0.95)))
    assert not report["flagged"], report


def test_fade_steps_are_larger_than_the_median_but_not_snaps():
    # the hold is the median step; the reset's steps are many times it and still pass
    report = render_loop.step_report(render(reset=(0.75, 0.95)))
    assert report["max_step"] > 3 * report["median"] + 0.05, report
    assert not report["flagged"], report


if __name__ == "__main__":
    test_too_short_reset_is_flagged_at_the_beat_boundary()
    test_reset_that_ends_by_the_last_frame_passes()
    test_fade_steps_are_larger_than_the_median_but_not_snaps()
    print("ok: the max-step check flags a too-short reset and passes a finished one")
