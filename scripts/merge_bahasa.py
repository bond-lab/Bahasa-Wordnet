#!/usr/bin/env python3
"""Merge NTU-MC wordnet XML with Bahasa Wordnet tab data.

Usage:
    merge_bahasa.py NTUMC_XML TAB_DIR [-o OUTPUT]

Takes a WN-LMF XML file produced by getwn.py (for ind or zsm) and merges
it with data from the Bahasa Wordnet tab files:

  - wn-msa-all.tab: confidence scores used to filter senses
    (keep only confidence > 0.85 or senses not in tab data)
  - wn-ind-def.tab: Indonesian definitions added to synsets; synsets
    not in the NTU-MC export are created, with their ILI from
    ili-map-pwn30.tab (from CILI)
  - corrections/senses.tsv: senses to remove, lower or add (see
    corrections/README.md)

The tab data is from https://github.com/bond-lab/Bahasa-Wordnet
"""

import argparse
import csv
import datetime
import sys
from collections import Counter
from pathlib import Path

from wn import lmf

# Confidence map for status codes in wn-msa-all.tab
STATUS_CONF = {"Y": 1.0, "O": 0.9, "M": 0.6, "L": 0.4, "X": 0}
MIN_CONFIDENCE = 0.85

CITATION = (
    "Nurril Hirfana Mohamed Noor, Suerya Sapuan and Francis Bond. 2011."
    " Creating the open Wordnet Bahasa."
    " In Proceedings of the 25th Pacific Asia Conference on Language,"
    " Information and Computation (PACLIC 25). pp 258\u2013267. Singapore."
)

URL = "https://bond-lab.github.io/Bahasa-Wordnet/"

# Per-language output metadata (keyed by WN-LMF language code)
LANG_META = {
    "id": {
        "id": "wnb-id",
        "label": "Wordnet Bahasa (Indonesian)",
        "license": "https://opensource.org/licenses/MIT/",
        "filename": "wn-bahasa-id.xml",
    },
    "zsm": {
        "id": "wnb-zsm",
        "label": "Wordnet Bahasa (Malay)",
        "license": "https://opensource.org/licenses/MIT/",
        "filename": "wn-bahasa-zsm.xml",
    },
}


def load_tab_senses(tab_dir, lang):
    """Load wn-msa-all.tab and return {(synset, lemma): confidence} for lang.

    Tab file language codes: B=both ind+zsm, I=ind only, M=zsm only.
    """
    path = Path(tab_dir) / "wn-msa-all.tab"
    if lang == "id":
        accept = ("B", "I")
    elif lang == "zsm":
        accept = ("B", "M")
    else:
        print(f"  WARNING: unsupported language {lang}, skipping tab filter",
              file=sys.stderr)
        return {}

    conf = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 4:
                continue
            ss, lng, status, lemma = parts
            if lng in accept:
                c = STATUS_CONF.get(status, 0.1)
                # Keep highest confidence if same pair appears multiple times
                key = (ss, lemma)
                if key not in conf or c > conf[key]:
                    conf[key] = c
            elif lng == "B":
                # B applies to both languages
                pass  # already handled above
    return conf


def load_tab_defs(tab_dir):
    """Load wn-ind-def.tab and return {synset: definition}."""
    path = Path(tab_dir) / "wn-ind-def.tab"
    if not path.exists():
        return {}
    defs = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            ss, typ, dfn = parts
            if typ == "ind:def":
                defs[ss] = dfn.strip().strip(";")
    return defs


def apply_corrections(lex, tsv, prefix):
    """Apply corrections/senses.tsv rows for this lexicon (synset_id starts with prefix).

    remove deletes the sense, lower sets its confidenceScore (unless already
    lower), rename moves the sense to the entry for new_lemma (same part of
    speech; dropped if that entry already has the synset), add creates the
    sense (and the entry if the lemma has none with that part of speech; a
    sense already there is kept).  Must run before the synset clean-up, so
    that a synset that gains a sense is kept.  Returns a Counter of what was
    done and the ids of the added senses (which the confidence filter keeps).
    """
    done = Counter()
    added = set()
    if not Path(tsv).exists():
        return done, added
    with open(tsv, encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)
                if r["synset_id"].startswith(prefix + "-")]
    edit = {(r["synset_id"], r["lemma"]): r for r in rows if r["action"] != "add"}
    moved = []  # (sense, new lemma, part of speech)
    for entry in lex["entries"]:
        lemma = entry["lemma"]["writtenForm"]
        kept = []
        for sense in entry.get("senses", []):
            row = edit.get((sense["synset"], lemma))
            if row is None:
                kept.append(sense)
                continue
            done["matched"] += 1
            if row["action"] == "remove":
                done["removed"] += 1
                continue
            if row["action"] == "rename":
                moved.append((sense, row["new_lemma"], entry["lemma"]["partOfSpeech"]))
                continue
            meta = sense.get("meta") or {}
            if float(meta.get("confidenceScore", 1.0)) > float(row["confidence"]):
                meta["confidenceScore"] = float(row["confidence"])
                sense["meta"] = meta
                done["lowered"] += 1
            kept.append(sense)
        entry["senses"] = kept
    done["unmatched"] = len(edit) - done.pop("matched", 0)

    synsets = {ss["id"]: ss for ss in lex["synsets"]}
    by_lemma = {(e["lemma"]["writtenForm"], e["lemma"]["partOfSpeech"]): e
                for e in lex["entries"]}
    for n, (sense, new, pos) in enumerate(moved):
        target = by_lemma.get((new, pos))
        if target is None:
            target = {"id": f"wrename{n}", "senses": [],
                      "lemma": {"writtenForm": new, "partOfSpeech": pos}}
            lex["entries"].append(target)
            by_lemma[(new, pos)] = target
        if any(se["synset"] == sense["synset"] for se in target["senses"]):
            done["rename: already there"] += 1  # members are cleaned up later
        else:
            target["senses"].append(sense)
            done["renamed"] += 1
    for n, r in enumerate(r for r in rows if r["action"] == "add"):
        ss = synsets.get(r["synset_id"])
        if ss is None:
            done["add: no synset"] += 1
            continue
        entry = by_lemma.get((r["lemma"], ss["partOfSpeech"]))
        if entry is None:
            entry = {"id": f"wadd{n}", "senses": [],
                     "lemma": {"writtenForm": r["lemma"], "partOfSpeech": ss["partOfSpeech"]}}
            lex["entries"].append(entry)
            by_lemma[(r["lemma"], ss["partOfSpeech"])] = entry
        there = [se for se in entry["senses"] if se["synset"] == ss["id"]]
        if there:
            # e.g. an M or L sense from the database: keep it
            added.update(se["id"] for se in there)
            done["add: already there"] += 1
            continue
        sid = f"{ss['id']}-{entry['id']}"
        entry["senses"].append({"id": sid, "synset": ss["id"]})
        ss["members"] = ss.get("members", []) + [sid]
        added.add(sid)
        done["added"] += 1
    return done, added


def load_ili_map(tab_dir):
    """Load ili-map-pwn30.tab and return {pwn30 synset: ili}.

    Satellites are '-s' in the map but '-a' in NTU-MC, so both are kept.
    """
    path = Path(tab_dir) / "ili-map-pwn30.tab"
    ili = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 2:
                ili[parts[1]] = parts[0]
                if parts[1].endswith("-s"):
                    ili[parts[1][:-1] + "a"] = parts[0]
    return ili


def strip_prefix(synset_id, prefix):
    """Strip lexicon prefix from synset ID: 'ntumc-id-00001740-a' -> '00001740-a'."""
    if synset_id.startswith(prefix + "-"):
        return synset_id[len(prefix) + 1:]
    return synset_id


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("xml", help="WN-LMF XML file from getwn.py")
    parser.add_argument("tab_dir", help="Directory with wn-msa-all.tab and wn-ind-def.tab")
    parser.add_argument("-o", "--output", help="Output XML file (default: auto from language)")
    parser.add_argument("--corrections",
                        default=str(Path(__file__).resolve().parents[1] / "corrections"
                                    / "senses.tsv"),
                        help="Sense corrections (default: corrections/senses.tsv)")
    parser.add_argument("--version", default=None,
                        help="Release version (default: today's date)")
    args = parser.parse_args()

    # Load XML
    print(f"  Loading {args.xml}")
    data = lmf.load(args.xml)
    lex = data["lexicons"][0]
    lang = lex["language"]
    old_prefix = lex["id"]  # e.g. "ntumc-id"

    if lang not in LANG_META:
        print(f"  ERROR: unsupported language {lang}", file=sys.stderr)
        sys.exit(1)
    meta = LANG_META[lang]
    new_prefix = meta["id"]  # e.g. "wnb-id"

    print(f"  Lexicon: {old_prefix} ({lang}) -> {new_prefix}")
    print(f"  Input: {len(lex['entries'])} entries, {len(lex['synsets'])} synsets")

    # Reprefix all IDs from old_prefix to new_prefix
    def reprefix(s):
        if s and s.startswith(old_prefix + "-"):
            return new_prefix + s[len(old_prefix):]
        return s

    for ss in lex["synsets"]:
        ss["id"] = reprefix(ss["id"])
        for rel in ss.get("relations", []):
            rel["target"] = reprefix(rel["target"])
        if "members" in ss:
            ss["members"] = [reprefix(m) for m in ss["members"]]
    for entry in lex.get("entries", []):
        for sense in entry.get("senses", []):
            sense["id"] = reprefix(sense["id"])
            sense["synset"] = reprefix(sense["synset"])

    # Update lexicon metadata
    lex["id"] = new_prefix
    lex["label"] = meta["label"]
    lex["license"] = meta["license"]
    lex["citation"] = CITATION
    lex["url"] = URL
    lex["version"] = args.version or datetime.date.today().isoformat()

    prefix = new_prefix  # use new prefix for the rest of the script

    # Load tab data
    tab_conf = load_tab_senses(args.tab_dir, lang)
    print(f"  Loaded {len(tab_conf)} sense confidence scores from wn-msa-all.tab")

    tab_defs = load_tab_defs(args.tab_dir) if lang == "id" else {}
    if tab_defs:
        print(f"  Loaded {len(tab_defs)} definitions from wn-ind-def.tab")

    # Add definitions from tab file
    defs_added = 0
    synsets_created = 0
    no_ili = 0
    ili_map = load_ili_map(args.tab_dir) if tab_defs else {}
    synset_by_id = {ss["id"]: ss for ss in lex["synsets"]}
    for bare_ss, dfn in sorted(tab_defs.items()):
        ss_id = f"{prefix}-{bare_ss}"
        ss = synset_by_id.get(ss_id)
        if ss is None:
            # Synset with no word in the NTU-MC database: create it so the
            # definition is kept (it extends the omw-en synset by ILI)
            if bare_ss not in ili_map:
                no_ili += 1
                continue
            ss = {"id": ss_id, "ili": ili_map[bare_ss],
                  "partOfSpeech": bare_ss[-1], "meta": None}
            lex["synsets"].append(ss)
            synset_by_id[ss_id] = ss
            synsets_created += 1
        existing = ss.get("definitions", [])
        if not existing:
            ss["definitions"] = [{"text": dfn, "meta": None}]
            defs_added += 1
    print(f"  Definitions added: {defs_added} "
          f"({synsets_created} synsets created, {no_ili} with no ILI skipped)")

    fixes, added = apply_corrections(lex, args.corrections, prefix)
    print(f"  Corrections: {dict(fixes)}")

    # Build set of synsets referenced by kept senses (for cleanup)
    kept_synsets = set()
    removed_senses = 0
    kept_senses = 0
    empty_entries = 0

    # Filter senses by confidence
    for entry in lex["entries"]:
        lemma = entry["lemma"]["writtenForm"]
        new_senses = []
        for sense in entry.get("senses", []):
            ss_id = sense["synset"]
            bare_ss = strip_prefix(ss_id, prefix)
            key = (bare_ss, lemma)
            if key in tab_conf and sense["id"] not in added:
                if tab_conf[key] >= MIN_CONFIDENCE:
                    new_senses.append(sense)
                    kept_synsets.add(ss_id)
                    kept_senses += 1
                else:
                    removed_senses += 1
            else:
                # Not in tab data (hand-made in the DB) or added — keep
                new_senses.append(sense)
                kept_synsets.add(ss_id)
                kept_senses += 1
        entry["senses"] = new_senses
        if not new_senses:
            empty_entries += 1

    # Remove entries with no senses
    orig_entries = len(lex["entries"])
    lex["entries"] = [e for e in lex["entries"] if e.get("senses")]

    print(f"  Senses: kept {kept_senses}, removed {removed_senses}")
    print(f"  Entries: {orig_entries} -> {len(lex['entries'])} "
          f"({empty_entries} empty removed)")

    # Update synset members to reflect removed senses
    kept_sense_ids = set()
    for entry in lex["entries"]:
        for sense in entry.get("senses", []):
            kept_sense_ids.add(sense["id"])
    for ss in lex["synsets"]:
        if "members" in ss:
            ss["members"] = [m for m in ss["members"] if m in kept_sense_ids]

    # Remove synsets with no senses and no definitions (they exist in the
    # base wordnet declared via <Requires>)
    has_def = {ss["id"] for ss in lex["synsets"] if ss.get("definitions")}
    needed_synsets = kept_synsets | has_def
    orig_synsets = len(lex["synsets"])
    lex["synsets"] = [ss for ss in lex["synsets"] if ss["id"] in needed_synsets]
    removed_synsets = orig_synsets - len(lex["synsets"])
    if removed_synsets:
        # Also strip relations pointing to removed synsets
        for ss in lex["synsets"]:
            if ss.get("relations"):
                ss["relations"] = [
                    r for r in ss["relations"] if r["target"] in needed_synsets
                ]
        print(f"  Synsets: {orig_synsets} -> {len(lex['synsets'])} "
              f"({removed_synsets} empty removed)")

    # Export
    if args.output:
        outpath = args.output
    else:
        outpath = str(Path(args.xml).parent / meta["filename"])
    lmf.dump(data, outpath)
    print(f"  Written to {outpath}")
    print(f"  Final: {len(lex['entries'])} entries, "
          f"{len(lex['synsets'])} synsets")


if __name__ == "__main__":
    main()
