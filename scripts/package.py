#!/usr/bin/env python3
"""Package a Wordnet Bahasa WN-LMF file for the wn module.

Writes OUTDIR/ID/ID-VERSION.xml with README.md, LICENSE and citation.bib,
and OUTDIR/ID-VERSION.tar.xz.  ID and VERSION are read from the XML.

Usage:
    scripts/package.py release/wnb-id-1.3.xml [-o release]
"""

import argparse
import re
import shutil
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def lexicon_id_version(xml: Path) -> tuple[str, str]:
    """Read the lexicon id and version from the start of a WN-LMF file."""
    with open(xml, encoding="utf-8") as fh:
        head = fh.read(4000)
    lex = re.search(r"<Lexicon\b[^>]*>", head, re.DOTALL).group(0)
    return (re.search(r'\bid="([^"]+)"', lex).group(1),
            re.search(r'\bversion="([^"]+)"', lex).group(1))


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("xml", help="WN-LMF file from merge_bahasa.py")
    parser.add_argument("-o", "--outdir", default=str(ROOT / "release"))
    args = parser.parse_args()

    xml = Path(args.xml)
    wn_id, version = lexicon_id_version(xml)
    outdir = Path(args.outdir)
    pkg = outdir / wn_id
    pkg.mkdir(parents=True, exist_ok=True)
    shutil.copy(xml, pkg / f"{wn_id}-{version}.xml")
    for name in ("README.md", "LICENSE", "citation.bib"):
        shutil.copy(ROOT / name, pkg / name)
    tar = outdir / f"{wn_id}-{version}.tar.xz"
    with tarfile.open(tar, "w:xz") as tf:
        tf.add(pkg, arcname=wn_id)
    print(f"  wrote {tar}")


if __name__ == "__main__":
    main()
