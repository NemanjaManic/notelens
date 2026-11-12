# MTSamples local dataset

Owner: C. C-001 audit completed on 2026-11-11. This is an educational demonstration;
it does not replace a doctor. Do not add real personal medical reports.

The user-supplied CSV is at `raw/mtsamples.csv`. Its unmodified bytes are identified in
[the source manifest](manifests/source.json). `raw/targets-nonempty.csv` is a generated
local inspection subset, not a deduplicated benchmark or a train/validation/test split.
Both files are covered by the existing root Git ignore rule. Do not force-add them.
Only scripts, aggregate manifests and documentation are intended for later review/publication.

From the repository root, using Python's standard library (verified with Python 3.11.9):

```powershell
python -B data/mtsamples/audit.py
python -B data/mtsamples/audit.py --check
python -B -m unittest discover -s data/mtsamples/tests -v
python -B -m json.tool data/mtsamples/manifests/source.json
git check-ignore data/mtsamples/raw/mtsamples.csv data/mtsamples/raw/targets-nonempty.csv
```

The first command regenerates the manifest and local subset. `--check` compares their
exact bytes to a fresh audit without writing. Run it after receiving data on another machine.
For a manually supplied CSV, `--source 'C:\path\mtsamples.csv'` is supported; never paste
credentials into chat. Review changed checksums/counts before accepting a new source.
No packages, model downloads, credentials or paid calls are needed.

Retained transcription text is unchanged, including whitespace and Unicode. Source labels
are stripped only for exact target membership. Only transcription may become a future
predictor; IDs, description, title, keywords and specialty labels must not become features.
Generated IDs are bound to the source checksum and original row ID; they are not the
application's per-session `PreparedDocument.doc_id` values.

See [data audit and attribution](../../docs/ml/data-audit.md) for measured results,
reuse limitations, checks and remaining gates. Do not train on this inspection subset:
duplicate/conflict exclusions, grouped splits, language review and the shared foundation
are still pending.
