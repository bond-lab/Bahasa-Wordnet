# Changes

From 1.5 on, the master copy of each lexicon (Indonesian `wnb-id`, Malay
`wnb-zsm`) is

* its last release, `wnb-id-1.5.xml` or `wnb-zsm-1.5.xml` (fetched from
  the GitHub release and checked against its checksum by `release.py`),
  and
* `wnb-id-1.5.jsonl` or `wnb-zsm-1.5.jsonl`: every change made since,
  one per line, in order.

`../NTUMC/.venv/bin/python release.py 1.6` applies the changes to each
base and writes `release/wnb-id-1.6.xml` and `release/wnb-zsm-1.6.xml`;
`scripts/package.py` packages them.  After a release, the new XML is the
base and new, empty logs are started; the old files stay as the history.

Nothing is rebuilt from the NTU-MC exports any more:
`scripts/merge_bahasa.py` and `corrections/` are how 1.5 was made, and
are kept for the record.

## A change record

```json
{"id": "wnb-id-1.5-1", "action": "remove_sense", "lexicon": "wnb-id",
 "synset": "wnb-id-02084071-n", "lemma": "anjing", "pos": "n",
 "user": "fcbond", "date": "2026-11-13", "source": "native check",
 "reason": "...", "base": "wnb-id-1.5"}
```

To make a change, add a line at the end of the lexicon's file.  Never
edit or delete an earlier line: to undo a change, add the opposite one.

* `id` is unique; `user`, `source` (the evidence: a person, a
  dictionary, a corpus) and `reason` are required.
* A model alone is not a source for an addition.
* A change to a word in both varieties is two records, one in each file.
* A synset whose last sense is removed stays unless a `remove_synset`
  record drops it.  The old build dropped every synset left with no
  sense and no definition.

The actions (`add_sense`, `remove_sense`, `set_confidence`,
`set_definition`, `add_form`, ...) and the fields each needs are in
NTU-MC `docs/wordnet-model.md`.

## The first logs

Both logs start empty: the repository had not changed since 1.5.
Building once more the old way on 2026-11-13 and comparing with the
release gave no difference for either lexicon.
