# AttackAware_PolyIoM v1.1.4 - Colab cell updates

Source of truth for these files is Google Drive:
`MyDrive/AttackAware_PolyIoM_v1_1_4/`. They are Colab cells, `exec()`'d
into the v1.1.4 consolidated notebook's namespace, so they are not
importable modules and reference notebook globals (`DIR`, `atomic_json`,
`mark_stage`, `verified_stage`, `sha256_file`, ...). Kept here for version
history only; this is not part of the `sam` application.

| file | role |
|---|---|
| `external_eval_cells.py` | cells 26-29: operating-point selection, VCTK embedding cache, locked external evaluation |
| `heldout_eval_cells.py` | held-out evaluation on the sealed 58-identity partition, and the face floor decision |
| `vctk_prepare_cells.py` | builds the VCTK manifest and 16 kHz audio from the archive already in Drive |
| `runtime_deps_cells.py` | installs and re-records speechbrain / facenet-pytorch / av |
| `_harness.py` | off-Colab test harness: stubs the notebook globals and checks the selection and VCTK logic |
| `sweep_80_face.csv` | the sealed face sweep, fixture for the harness |

Run the harness with `python _harness.py /tmp/polyiom_test` (needs pandas,
numpy, scipy). It does not touch Drive. See
`README_UPDATES_2026-09-17.md` in the Drive folder for what changed and why.
