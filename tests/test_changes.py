"""The change records must be well formed and fit their base."""

import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
release = pytest.importorskip("release", reason="needs ../NTUMC (ntumc.wordnet)")

from ntumc.wordnet import changes, lmf  # noqa: E402


@pytest.mark.parametrize("name", list(release.BASES))
def test_every_record_is_well_formed(name: str) -> None:
    # Act
    records = list(changes.read(release.BASES[name].changes))
    problems = [(r.id, p) for r in records for p in changes.validate(r)]
    ids = Counter(r.id for r in records)
    # Assert
    assert problems == []
    assert [i for i, n in ids.items() if n > 1] == []
    assert {r.lexicon for r in records} <= {name}


@pytest.mark.parametrize("name", list(release.BASES))
def test_the_records_apply_to_the_base_without_conflict(name: str) -> None:
    # Arrange
    base = release.BASES[name]
    if not base.xml.exists():
        pytest.skip("base release not downloaded: run release.py once")
    # Act
    _, conflicts = changes.apply(lmf.read(base.xml), changes.read(base.changes))
    # Assert
    assert conflicts == []


@pytest.mark.parametrize("name", list(release.BASES))
def test_no_ili_is_on_two_synsets(name: str) -> None:
    # Arrange
    base = release.BASES[name]
    if not base.xml.exists():
        pytest.skip("base release not downloaded: run release.py once")
    # Act
    items, _ = changes.apply(lmf.read(base.xml), changes.read(base.changes))
    # Assert
    assert changes.shared_ilis(items) == []


def test_each_base_has_its_own_files() -> None:
    # Act
    base = release.BASES["wnb-zsm"]
    # Assert
    assert base.name == "wnb-zsm-1.5"
    assert base.url.endswith("/v1.5/wnb-zsm-1.5.tar.xz")
    assert base.changes.name == "wnb-zsm-1.5.jsonl"
