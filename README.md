# Wordnet Bahasa

A wordnet for the Malay languages: Indonesian (`wnb-id`) and Malaysian
Malay (`wnb-zsm`), linked to the Princeton WordNet and the Collaborative
Interlingual Index (CILI).

Web page: <https://bond-lab.github.io/Bahasa-Wordnet/>
(formerly <https://wn-msa.sourceforge.net/>)

## Version 1.4 (2026-10)

| | Indonesian (`wnb-id`) | Malay (`wnb-zsm`) |
|---|---|---|
| Synsets | 39,835 | 34,365 |
| Words (lexical entries) | 39,398 | 35,913 |
| Senses | 87,358 | 79,862 |
| Definitions | 7,322 | – |

Release 1.4 removes senses found wrong in a review of every sense not
marked hand-checked (Claude Haiku flagged suspects, two blind Claude Opus
runs judged them, an Opus adjudicator decided disagreements): 19,335 from
Indonesian (2,551 of them Malaysian words) and 14,348 from Malay (413 of
them Indonesian words), lowers the confidence of 816 and 101 undecided
ones, and moves 135 words to the right variety.  See
`corrections/README.md`.

Each language is a WN-LMF 1.4 package that extends the English
`omw-en:2.0` wordnet (`<Requires ref="omw-en" version="2.0"/>`).  They
are built from the NTU Multilingual Corpus wordnet database
(<https://github.com/bond-lab/NTUMC>), keeping senses that are hand
checked or high-quality automatic (Y, O in `data/wn-msa-all.tab`) or
that were added while sense-tagging the NTU-MC, with Indonesian
definitions from `data/wn-ind-def.tab`; see `scripts/merge_bahasa.py`.

## Using it with `wn`

```python
import wn
wn.download("omw-en:2.0")
wn.download("https://github.com/bond-lab/Bahasa-Wordnet/releases/download/v1.4/wnb-id-1.4.tar.xz")
wn.download("https://github.com/bond-lab/Bahasa-Wordnet/releases/download/v1.4/wnb-zsm-1.4.tar.xz")
wn.Wordnet("wnb-id:1.4").words("anjing")
```

## History

* 1.4 (2026-10): reviewed senses (LLM review, see `corrections/`)
* 1.3 (2026-10): moved to GitHub; WN-LMF packages
* 1.2 (2017-10): new synsets and lemmas from KBBI and KD via scientific names
* 1.1 (2015-01): new data from Ruli Manurung and Lian Tze Lim; checked against KBBI and KD
* 1.0 (2012-12): merged with the Malaysian and Indonesian Wordnets
* 0.90 (2011-10): initial public release

## License

MIT: see [LICENSE](LICENSE).

## Citation

Nurril Hirfana Mohamed Noor, Suerya Sapuan and Francis Bond (2011).
Creating the open Wordnet Bahasa.  In *Proceedings of the 25th Pacific
Asia Conference on Language, Information and Computation (PACLIC 25)*,
pp 255–264. Singapore.  See [citation.bib](citation.bib), which also
has the papers on the combined Wordnet Bahasa (Bond et al. 2014) and
its definitions (Moeljadi and Bond 2016).

## People

Francis Bond, Nurril Hirfana Mohamed Noor, Suerya Sapuan, Muhammad
Zulhelmy Mohamed Rosman, Hammam Riza, Tan Enya Kong, Ruli Manurung,
Lian Tze Lim, David Moeljadi and Hannah Yun Jung Choi.

## Raw data

`data/wn-msa-all.tab` has the format `synset\tlang\tgoodness\tlemma`:

```
synset is the offset-pos from Princeton wordnet 3.0
lang 
     B (Bahasa = msa); 
     I (Indonesian = ind); 
     M (Malay = zsm)
goodness is:
     Y = hand checked and good
     O = automatic high quality (good)
     M = automatic medium quality (ok)
     L = automatic, probably bad (low)
     X = hand checked and bad

Normal release has only Y and O.


e.g.
00015388-n	B	X	fauna
00015388-n	M	Y	haiwan
00015388-n	I	Y	hewan

Note: msa is the supertype of ind and zsm
```

## Notes

```

Apostrophe should be (’) U+2019 as in: Côte d’Ivoire.
Technically glottal stop should be (ʼ) Letter apostrophe U+02BC.
We need to make the lookup more forgiving of this.

There are some abbreviations in use:
yg = yang
sso =

========================================================================
Def:

06822958-n	DEF	tanda koma di bawah konsonan c tanda bunyi 's'
06823760-n	DEF	dua titik di atas huruf vokal
```
