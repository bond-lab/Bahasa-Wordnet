# Wordnet Bahasa corrections

Corrections to the Indonesian and Malay exports of the NTU-MC wordnet,
applied by `scripts/merge_bahasa.py` before its synset clean-up.  The exports
are build artefacts, so fixes are kept here as data: auditable, reviewable as
diffs and reapplied on every rebuild.

## `senses.tsv`

Tab-separated, UTF-8, with a header row:

```
synset_id	lemma	action	confidence	reason	source	date	new_lemma
```

A sense is named by its synset ID, whose prefix gives the lexicon
(`wnb-id-...` or `wnb-zsm-...`), and the entry's lemma (written form).
`action` is

* `remove`: delete the sense, and the entry if it has no senses left;
* `lower`: set `confidenceScore` to `confidence` unless it is already lower;
* `rename`: move the sense to the entry for `new_lemma` (same part of
  speech), creating it if needed, or drop the sense if that entry already
  has the synset;
* `add`: add the sense, creating the entry if the lemma has none with the
  synset's part of speech (used to move a word to the right variety).

`merge_bahasa.py` reports what it did and how many rows matched no sense.

The first 34,744 rows (2026-10-24) come from a review of every sense not
marked hand-checked (`Y`) in `data/wn-msa-all.tab`: Claude Haiku flagged
26,165 of 94,528 Indonesian and 19,053 of 81,757 Malay senses as suspect;
two blind Claude Opus runs judged each flagged sense, and an Opus
adjudicator decided where they disagreed.  Each run also noted words of
the other variety and malformed lemmas; a note counts when both runs gave
it.

| | wnb-id | wnb-zsm |
|---|---|---|
| `remove`, wrong sense | 16,159 | 13,727 |
| `remove`, Malaysian word in wnb-id / Indonesian word in wnb-zsm | 2,551 | 413 |
| `remove`, malformed or not a word (one also Malaysian) | 627 | 208 |
| `lower` to 0.5, undecided | 817 | 101 |
| `add`, moved from the other variety | 5 | 136 |

A word of the other variety is only added to the right lexicon when its
meaning was not judged wrong and that lexicon does not have it already
(most do: 1,835 of the Malaysian words in wnb-id are also in wnb-zsm).
Six of the 136 moves into wnb-zsm (*melocot*, *jubin*, *pusingan*,
*Orang Cili*, *labuh*, *otah*) are skipped because their synset is not in the
Malay export; `merge_bahasa.py` reports them as `add: no synset`.

Two `rename` rows with source `form: mechanical` (made by NTU-MC's
`scripts/form_fixes.py`) strip a trailing space (`banjir ` → `banjir`).

The reviews, reasons and scripts are in the NTU-MC repository
(`scripts/triage_review.py`; the run files are in `build/triage*/`).

### Words for synsets that only have a definition (1.5)

Release 1.5 keeps every Indonesian definition of `data/wn-ind-def.tab`,
which leaves 9,209 wnb-id synsets with a definition but no word.  Their
candidates from `wn-msa-all.tab` (automatic O, M and L senses; not X,
and not ones reviewed above) were reviewed blind by two Claude Opus runs
and an adjudicator, as above.  The 2,394 judged OK with no malformed or
Malaysian note from both runs are `add` rows with source `lemma rescue`
(the reason says which status they had: OK for 519 of 622 O, 421 of 687
M and 1,985 of 9,954 L candidates).  An `add` row also keeps a sense the
confidence filter would drop.

Claude Opus also proposed words for these synsets; those are left out
until a person has checked them (NTU-MC
`docs/quality-sample/full-review/id-rescue-proposed-pending.tsv`).
The scripts are NTU-MC's `scripts/bahasa_rescue.py` and
`scripts/triage_review.py`.

## `definitions.tsv`

Tab-separated, UTF-8, with a header row (the format of wnja's
`corrections/definitions.tsv`, plus `confidence`):

```
synset_id	old_value	new_value	reason	source	date	confidence
```

`old_value` must be the synset's current definition, or the row is
skipped as stale.  An empty `new_value` removes the definition; a
`new_value` equal to `old_value` keeps it.  With a `confidence`, the
definition gets that `confidenceScore` and the reason as its `note`.

The rows from 2026-10-25 come from a review of all 13,101 Indonesian
definitions: two blind Claude Opus runs judged each OK, PARTIAL (the
right concept, but vague, truncated, clumsy or with English words) or
WRONG (another concept, garbled, or not a definition) against the
English synset, and an Opus adjudicator decided the 1,358 where they
disagreed.

| Verdict | Definitions | Row |
|---|---|---|
| OK | 7,913 | – |
| PARTIAL | 4,426 | kept, `confidence` 0.5 |
| WRONG | 761 | removed |
| UNSURE | 1 | – |

A synset that loses its definition and has no word is dropped.  The
reviewers' suggested rewrites are not applied: they wait for a human
check (NTU-MC `build/def-review/id/suggestions-pending.tsv`, and
`docs/quality-sample/def-review/`).  The script is NTU-MC's
`scripts/def_review.py`.
