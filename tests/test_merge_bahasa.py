"""Tests for the sense corrections in merge_bahasa.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from merge_bahasa import apply_corrections  # noqa: E402

HEAD = "synset_id\tlemma\taction\tconfidence\treason\tsource\tdate\n"


def lexicon() -> dict:
    """A Malay lexicon with soalan in s-1 and an empty synset s-2."""
    return {
        "entries": [{"id": "w1", "lemma": {"writtenForm": "soalan", "partOfSpeech": "n"},
                     "senses": [{"id": "wnb-zsm-1-n-w1", "synset": "wnb-zsm-1-n"}]}],
        "synsets": [{"id": "wnb-zsm-1-n", "partOfSpeech": "n", "members": ["wnb-zsm-1-n-w1"]},
                    {"id": "wnb-zsm-2-v", "partOfSpeech": "v", "members": []}],
    }


def test_rows_for_other_lexicon_are_ignored(tmp_path: Path) -> None:
    tsv = tmp_path / "senses.tsv"
    tsv.write_text(HEAD + "wnb-id-1-n\tsoalan\tremove\t\tMalaysian\tt\td\n", encoding="utf-8")
    lex = lexicon()
    done = apply_corrections(lex, tsv, "wnb-zsm")
    assert done["removed"] == 0
    assert len(lex["entries"][0]["senses"]) == 1


def test_add_creates_entry_and_member_and_skips_missing_synset(tmp_path: Path) -> None:
    # Arrange
    tsv = tmp_path / "senses.tsv"
    tsv.write_text(HEAD + "wnb-zsm-2-v\tmereka bentuk\tadd\t\tmoved\tt\td\n"
                   "wnb-zsm-1-n\tsoalan\tadd\t\tmoved\tt\td\n"
                   "wnb-zsm-9-n\tlongkang\tadd\t\tmoved\tt\td\n", encoding="utf-8")
    lex = lexicon()

    # Act
    done = apply_corrections(lex, tsv, "wnb-zsm")

    # Assert
    assert (done["added"], done["add: already there"], done["add: no synset"]) == (1, 1, 1)
    new = lex["entries"][-1]
    assert new["lemma"] == {"writtenForm": "mereka bentuk", "partOfSpeech": "v"}
    assert lex["synsets"][1]["members"] == [new["senses"][0]["id"]]


def test_remove_and_lower(tmp_path: Path) -> None:
    tsv = tmp_path / "senses.tsv"
    tsv.write_text(HEAD + "wnb-zsm-1-n\tsoalan\tlower\t0.5\tunsure\tt\td\n", encoding="utf-8")
    lex = lexicon()
    done = apply_corrections(lex, tsv, "wnb-zsm")
    assert done["lowered"] == 1
    assert lex["entries"][0]["senses"][0]["meta"] == {"confidenceScore": 0.5}
