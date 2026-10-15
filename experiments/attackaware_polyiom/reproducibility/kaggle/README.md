# Running the whole experiment freshly on Kaggle

`AttackAware_PolyIoM_KAGGLE_FRESH.ipynb` reruns the AttackAware PolyIoM
v1.1.4 study from the public datasets. You upload one file, and it does
everything else. It downloads the data, builds the face and voice
embeddings, splits the people, searches for the polynomial key, selects the
operating point, evaluates, runs the ablation, attack and revocation tests,
draws all 12 figures, and compares every result with the paper.

The notebook runs the study's own code, ported from the original Colab
notebook (`AttackAware_PolyIoM_v1_1_4_PublicData_15GB_Resumable_CHECKPOINT_FIX`).
After every stage it checks its output against the study's record and prints
**identical** or **DIFFERENT**.

## What you need

- A Kaggle account that is phone-verified. Without phone verification,
  Internet stays off and the downloads cannot run.
- About three Kaggle sessions. One session lasts at most 12 hours.

## Steps

1. On Kaggle, choose **Create → New Notebook**, then **File → Import
   Notebook**, and upload `AttackAware_PolyIoM_KAGGLE_FRESH.ipynb`.
2. In the right-hand panel (**Settings**):
   - **Internet: On**
   - **Accelerator: GPU T4 x2** (or P100)
3. Choose **Add Input → Datasets**, search for `chinafax/cfpw-dataset`, and
   add it. This is the CFP name list the study used to remove people who also
   appear in CFP.
4. Click **Save Version → Save & Run All (Commit)**, then close the tab. The
   run continues on Kaggle's computers.

## Continuing in the next session

When a session ends, the work so far is saved in that version's output.

1. Open the notebook again (**Edit**).
2. Choose **Add Input → Your Work → Notebooks**, pick this notebook, and add
   its latest version's output.
3. Click **Save Version → Save & Run All** again.

The first cell finds the earlier work and copies it back. Every finished
stage is skipped, and the key search continues from the last saved
candidate. Repeat until the last cell prints a zip path.

| Session | What usually happens |
|---|---|
| 1 | downloads LFW and LibriSpeech, face and voice embeddings, the split, the IoM tensors; the key search starts |
| 2 | the key search finishes |
| 3 | selection, held-out evaluation, VCTK (downloaded only now), analyses, figures and report |

## What you get

The output folder `AttackAware_PolyIoM_fresh/` contains:

- `REPLICATION_REPORT.md`, which has three parts:
  1. **Stage by stage.** For each stage, whether the fresh output is identical
     to the study's (dataset hashes, image and speaker counts, the ECAPA
     checkpoints, the split, the manifests, the selected setting, and the
     held-out numbers).
  2. **Results against the paper.** Every paper number beside the fresh number
     and its 95% interval.
  3. **The paper's findings.** Whether each main finding still holds.
- `figures/`: all 12 figures, as PNG and PDF.
- `AttackAware_PolyIoM_fresh_results.zip`: the report, the figures and every
  result file, ready to download.

## How to read the report

- **All identical.** The paper is reproduced exactly.
- **Some DIFFERENT.** Usually a newer library version changed a number in its
  last digits, and the change carried forward. Look at the first stage marked
  DIFFERENT, because later stages inherit its change. Then read part 2: if the
  paper's values sit inside the fresh 95% intervals and the findings in part 3
  hold, the results are replicated, though not bit for bit.

## Two notes on the ported code

- **ECAPA normalisation checkpoint.** The original notebook's constant for
  `mean_var_norm_emb.ckpt` (`0eb77a0b…`) is not the file the study actually
  used. The notebook checks against the study's sealed record instead
  (`cd70225b…`).
- **Batched key search.** The original notebook evaluates 32 candidate keys
  at once, but it shaped the keys in a way that only works for a batch of
  one. The study's own key search (7 September) used an earlier version of
  the code. Here each candidate in a batch uses its own key, as intended. The
  candidates do not affect each other, so the result is the same as
  evaluating them one at a time.

## Checking the notebook without Kaggle

`check_kaggle_notebook.py` runs the real notebook four times on tiny
stand-in datasets, with stand-in face and voice models:

1. A session that stops at the key search.
2. A resumed session that finishes.
3. A rerun that must change nothing.
4. A run from scratch whose results must be identical to run 2.

```
pip install nbformat nbclient ipykernel soundfile pillow scipy matplotlib
python3 kaggle/build_kaggle_notebook.py
python3 kaggle/check_kaggle_notebook.py
```

This tests the plumbing, the resuming and the determinism. Only the real
data on Kaggle can produce the real results.
