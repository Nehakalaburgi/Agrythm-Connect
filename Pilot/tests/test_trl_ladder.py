"""The README's animated TRL ladder must always show connect.models.REPORTED_TRL."""
import importlib.util
from pathlib import Path

import pytest

from connect.models import REPORTED_TRL as CURRENT_TRL

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("make_trl_ladder", ROOT / "scripts" / "make_trl_ladder.py")
ladder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ladder)


def test_committed_svg_matches_current_trl():
    expected = ladder.build_svg(CURRENT_TRL)
    actual = (ROOT / "docs" / "trl_ladder.svg").read_text(encoding="utf-8")
    assert actual == expected, "docs/trl_ladder.svg is stale: run `python scripts/make_trl_ladder.py`"


def test_readme_embeds_the_ladder_and_states_current_level():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/trl_ladder.svg" in readme
    assert f"Current TRL {CURRENT_TRL}" in readme


@pytest.mark.parametrize("level", range(10))
def test_exactly_one_level_is_marked_current(level):
    svg = ladder.build_svg(level)
    assert svg.count("WE ARE HERE") == 1
    assert svg.count("&#10003; DONE") == level


def test_invalid_level_is_rejected():
    with pytest.raises(ValueError):
        ladder.build_svg(10)
