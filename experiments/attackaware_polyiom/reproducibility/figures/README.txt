AttackAware PolyIoM: results figures
====================================

These eight figures are drawn by figures.py directly from the files in
results/. No number is entered by hand. To redraw them:

    python3 run.py figures

Before drawing, figures.py checks its inputs and stops if any check fails:
- the two sweep files must match their sealed SHA-256 hashes;
- re-running the selection rule on the sweeps must choose exactly the
  sealed settings (voice M=128 q=32 o=1; face M=256 q=32 o=1);
- every carried confidence interval must contain, and agree with, the
  sealed point estimate;
- every unprotected upper bound is recomputed (one-sided 95 percent
  Clopper-Pearson) and must match the stored value.

Each figure is provided as PDF (vector, for the journal) and PNG (slides).


Figure 3. Unlinkability across the design space
   Source: results/sweep/
   Each cell is one of the 80 settings tested on the development group.
   The colour shows linkability (Dsys); lighter cells are better. The
   ringed cell is the setting that was selected and sealed.

Figure 4. Trade-off between recognition and unlinkability
   Source: results/sweep/
   Each point is one setting. Points near the lower left have both a low
   error rate and low linkability. The stepped line marks the best
   available compromise, and the large points are the sealed settings.

Figure 5. Development, held-out and external results
   Source: results/heldout/, results/external/, results/sweep/
   For each group of people, the figure shows EER, TAR, FMR and Dsys with
   their 95 percent intervals. Development results have no interval,
   because they were used for selection, not for evaluation.

Figure 6. Ablation: what each stage costs
   Source: results/ablation/
   The three versions of the system are compared on error rate and on
   linkability. On voice, the extra error is divided into the part caused
   by reducing the size of the data and the part caused by the
   polynomial itself.

Figure 7. Cancellation of stolen templates, key by key
   Source: results/revocation/
   Each dot is one new key. Its position shows how often an attacker's
   old forged input was still accepted after the key change. Hashing alone
   fails for every key; the linear map succeeds for every key; most
   polynomial keys succeed completely, but a minority do not.

Figure 8. What the attack achieves
   Source: results/inversion/, results/revocation/
   The left panels show that the attack reaches the acceptance threshold
   for every version. The right panels show how closely the attacker's
   reconstruction resembles the real embedding; the polynomial gives the
   lowest similarity.

Figure S2. Selection of the operating point
   Source: results/sweep/
   Panel (a) shows that no face setting reaches the voice target, which is
   why the face target was relaxed before testing. Panel (b) shows
   linkability for the settings that meet each target, and marks the
   selected setting.

Figure P. Protection cost against the unprotected system
   Source: results/scores/unprotected_baseline.json, results/heldout/
   For each group of people, the protected error rate (with its interval)
   is shown above the unprotected error rate. Where the unprotected system
   made fewer than one error, only an upper bound can be given, drawn as
   an arrow. A cost is called firm when the protected interval lies
   entirely above that bound.


Note on two input files
-----------------------
results/heldout/confidence_intervals.json and
results/scores/unprotected_baseline.json were transcribed from console
output of the study's runs, because the raw output is not part of this
package. figures.py checks both against the sealed results before use.

Not drawn here
--------------
The detection-error curves and score distributions (paper Figures A to D)
need the per-comparison score histograms (score_histograms.json), which
are not part of this package. code/runtime/figures_only.py draws them when
that file is available.
