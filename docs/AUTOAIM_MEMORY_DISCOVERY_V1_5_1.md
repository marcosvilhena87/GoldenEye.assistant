# v1.5.1 — Intervention Timing Audit

Read-only offline audit of existing Auto-Aim v1.5 CSVs. No new BizHawk capture required.

Run:
```powershell
git pull --ff-only origin main
python -m unittest discover -s tests -v
python .\tools\analyze_autoaim_mem_v1_5_1.py 20261023T212013Z_191808
```

Outputs, created without overwrite:
- `*_timing_audit_v1_5_1.csv`: latest preceding transition per primary candidate and BEGIN frame, distance from BEGIN, count of changes inside brackets, first later change.
- `*_lag_audit_v1_5_1.csv`: pairwise lag for matching ON/OFF byte transitions within ±30 frames for the two secondary candidates relative to `0x040A93`.

In the provided session, transitions 197159/197161 preceded BEGIN 197539, and 203527/203529 preceded BEGIN 204224. The candidate lead of 2 frames in both directions is **observational**, not a validated source-to-copy relationship. Closest preceding transitions can belong to unrelated actions. Follow-up experiment: confirm BEGIN in Lua **before** touching Auto-Aim settings, and confirm END after; observe only one variable per interval. Existing datasets and GoldenEye.mapping remain unchanged.
