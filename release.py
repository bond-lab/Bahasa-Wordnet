#!/usr/bin/env python3
"""Make the next Wordnet Bahasa release: the last release plus the change records.

    ../NTUMC/.venv/bin/python release.py VERSION [wnb-id] [wnb-zsm]   # e.g. 1.6
    scripts/package.py release/wnb-id-VERSION.xml
    scripts/package.py release/wnb-zsm-VERSION.xml

Indonesian (wnb-id) and Malay (wnb-zsm) are two lexicons, each with its
own base and change log.  The base is the released ID-BASE_VERSION.xml,
downloaded once to build/base/ and checked against its checksum.  The
changes are changes/ID-BASE_VERSION.jsonl (see changes/README.md).  A
change that does not fit the base is a conflict: they are listed, and
nothing is written for that lexicon until they are settled.  Synsets left
with no sense and nothing of their own (definition, example) are then
dropped: omw-en has the concept through the ILI.

Two lexicons are written: ID-min-VERSION.xml, the minimal lexicon (the
master), which leaves the English definition and the relations of the
concepts CILI does not have yet to the shared lexicon omw-ntumc; and
ID-VERSION.xml, the export, with those put back.  omw-ntumc is read
from a checkout beside this one, built at its tag
(uv run build.py SHARED_VERSION).

Uses ntumc.wordnet from a checkout of NTU-MC beside this one (../NTUMC).
"""

import argparse
import hashlib
import io
import logging
import sys
import tarfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "NTUMC"))

from ntumc.wordnet import changes, lmf, shared  # noqa: E402
from ntumc.wordnet.model import Lexicon  # noqa: E402

BASE_VERSION = "1.5"
SHARED_VERSION = "0.1"
SHARED = ROOT.parent / "omw-ntumc" / "build" / f"omw-ntumc-{SHARED_VERSION}.xml"
SHARED_SHA256 = "6ee5f6a254907d4fbdaa0e4238dddf0c3012ee92ef27fdd7d79815c46ff7c3f0"
RELEASES = "https://github.com/bond-lab/Bahasa-Wordnet/releases/download"

log = logging.getLogger("release")


@dataclass(frozen=True)
class Base:
    """The last release of one lexicon.

    Attributes:
        id: the lexicon id, wnb-id or wnb-zsm
        xz_sha256: checksum of the released package
        xml_sha256: checksum of the XML inside it
    """

    id: str
    xz_sha256: str
    xml_sha256: str

    @property
    def name(self) -> str:
        """The file stem, e.g. wnb-id-1.5."""
        return f"{self.id}-{BASE_VERSION}"

    @property
    def url(self) -> str:
        """Where the released package is."""
        return f"{RELEASES}/v{BASE_VERSION}/{self.name}.tar.xz"

    @property
    def xml(self) -> Path:
        """The local copy of the base XML."""
        return ROOT / "build" / "base" / f"{self.name}.xml"

    @property
    def changes(self) -> Path:
        """The change log made against this base."""
        return ROOT / "changes" / f"{self.name}.jsonl"


BASES = {b.id: b for b in (
    Base("wnb-id",
         "8e374000d1b8265a9c535af966f0b8d761001c72705ea3742725035b8944f679",
         "9d794f11e48117373abb38f3072a76460d99b67cd907d21bf91415439b7af05b"),
    Base("wnb-zsm",
         "a5356845d53ff4eef7cb513b0d65309d1a038d5d6d8bb492f820d1761497bc2f",
         "882349172bd39e0899bc3fb642d103d6e729eb938ff637eef64f788ad432569f"),
)}


def fetch_base(base: Base) -> None:
    """Download a base release, unless it is there; check it.

    Args:
        base: the lexicon's last release

    Raises:
        ValueError: if the download or the file does not match its checksum.
    """
    if not base.xml.exists():
        log.info("Downloading %s", base.url)
        with urllib.request.urlopen(base.url) as resp:
            data = resp.read()
        if hashlib.sha256(data).hexdigest() != base.xz_sha256:
            raise ValueError(f"{base.url}: checksum mismatch")
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:xz") as tf:
            member = tf.extractfile(f"{base.id}/{base.name}.xml")
            if member is None:
                raise ValueError(f"{base.url}: no {base.name}.xml inside")
            base.xml.parent.mkdir(parents=True, exist_ok=True)
            base.xml.write_bytes(member.read())
    if hashlib.sha256(base.xml.read_bytes()).hexdigest() != base.xml_sha256:
        raise ValueError(f"{base.xml} is not the released {base.name}")


def release(base: Base, version: str, out: Path) -> list[str]:
    """Apply a lexicon's change records to its base and write the new release.

    Args:
        base: the lexicon's last release
        version: the version of the new release
        out: the export's XML file; the minimal lexicon goes beside it.
            Neither is written if there are conflicts

    Returns:
        The conflicts, one line each.

    Raises:
        ValueError: if the export lacks something the lexicon said before
            it was split.
    """
    fetch_base(base)
    items, conflicts = changes.apply(lmf.read(base.xml), changes.read(base.changes))
    if conflicts:
        return conflicts
    items, dropped = changes.drop_empty_synsets(items)
    log.info("Dropped %d synsets with no sense and nothing of their own", len(dropped))
    next(i for i in items if isinstance(i, Lexicon)).version = version
    out.parent.mkdir(parents=True, exist_ok=True)
    shared.write_release(items, shared.load(SHARED, SHARED_SHA256), out)
    return []


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version", help="version of the new release, e.g. 1.6")
    parser.add_argument("lexicons", nargs="*", metavar="LEXICON",
                        help=f"which of {', '.join(BASES)} (default: both)")
    parser.add_argument("-o", "--outdir", default=str(ROOT / "release"),
                        help="output directory (default: release/)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    unknown = set(args.lexicons) - set(BASES)
    if unknown:
        parser.error(f"unknown lexicon(s): {', '.join(sorted(unknown))}")
    failed = False
    for name in args.lexicons or BASES:
        out = Path(args.outdir) / f"{name}-{args.version}.xml"
        conflicts = release(BASES[name], args.version, out)
        for line in conflicts:
            log.error("%s: %s", name, line)
        if conflicts:
            failed = True
        else:
            log.info("Wrote %s", out)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
