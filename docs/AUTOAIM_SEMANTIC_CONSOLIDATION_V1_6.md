# v1.6 — Semantic Consolidation

Canonical provenance lives in [GoldenEye.mapping/experiments/autoaim_semantic_consolidation_v1_6_20261023.json](https://github.com/marcosvilhena87/GoldenEye.mapping/blob/main/experiments/autoaim_semantic_consolidation_v1_6_20261023.json).

Three candidate offsets reproduced operator-observed ON/OFF toggles over six bracketed interventions, and two negative controls showed no changes. These are experimental associations, **not validated executable symbols**. The ROM SHA-256 and N64 core are unverified, and which offset is primary is unknown.

Check the mapping checkout independently:
```powershell
python .\tools\verify_autoaim_consolidation_v1_6.py C:\path\to\GoldenEye.mapping
python -m unittest discover -s tests -v
```

The verifier reads and checks a JSON record; it deliberately does not emit a Lua snapshot or enable memory reads/writes. Existing `tools/export_mapping.py` still requires a verified ROM record and remains the only normal symbol-export route. With no validated catalog entries, all Auto-Align and Auto-Shot control remains disabled.

Raw CSV evidence stays on the operator's computer. Future work: verify ROM hash/core, independent fresh-run controls, primary/mirror distinction, and investigate horizontal correction separately.
