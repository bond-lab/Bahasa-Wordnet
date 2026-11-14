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
* A synset left with no sense and nothing of its own (definition,
  example) is dropped by `release.py`, as the old build did: omw-en has
  the concept through the ILI.  No record is needed.

The actions (`add_sense`, `remove_sense`, `set_confidence`,
`set_definition`, `add_form`, ...) and the fields each needs are in
NTU-MC `docs/wordnet-model.md`.

## The first logs

Both logs start empty: the repository had not changed since 1.5.
Building once more the old way on 2026-11-13 and comparing with the
release gave no difference for either lexicon.

## Senses the corpus uses (2026-11-13)

The Indonesian release leaves out senses the NTU-MC wordnet marks as
coming from the Malay data or added in NTU-MC.  The NTU-MC Indonesian
corpus has 2,139 concepts tagged with 777 such senses: a tagger chose
each one.  They are added to `wnb-id` (`scripts/add_back_corpus.py`),
after 175 `add_synset` records for synsets it did not have (ILI only, no
relations: omw-en has the concept).  The first-logs note above is about
the state before this.

The 230 corpus-tagged senses that the review removed are not added:
they wait for a ruling in NTU-MC
`docs/quality-sample/removed-but-tagged/ind.tsv`.

## Instance relations turned round (2026-11-13)

In the Princeton data an instance points to its class
(`instance_hypernym`), but the instance links NTU-MC annotators made
from new synsets were entered the other way, so the export wrote them
backwards (AirAsia had airline as its *instance*).  All 447 such links
were read; 437 are wrong and are listed in omw-ntumc
`instance-links-turned.tsv`.  Each one in this lexicon is fixed by a
`remove_relation` and an `add_relation` record, in both directions.

## Linked to omw-ntumc (2026-11-14)

Each synset for a concept that Princeton WordNet does not have now
carries the concept's identifier from the omw-ntumc registry
(`dc:identifier="ntumc00392"`), set by a `set_identifier` record.  The
same concept has the same identifier in every lexicon.  This is the
first step towards a minimal lexicon whose new concepts keep their
definition and relations only in omw-ntumc.  The pronoun synsets (ids
beginning 77) are not linked here: they belong to omw-pronoun.

The pronoun synsets carry omw-pronoun's identifiers instead
(`dc:identifier="pronoun:1;Sg"`), from its table of NTU-MC synsets.
