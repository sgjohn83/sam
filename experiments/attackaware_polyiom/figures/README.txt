AttackAware PolyIoM: Figures
============================

Each figure is provided in two formats. The PDF version is a vector file,
which is suitable for journal submission because it remains sharp at any
size. The PNG version is suitable for slides and documents.

Every value in these figures is read from the stored results of the study.
No number was entered by hand.


Figure 1. How a protected template is built
   File: Figure1_TemplateGeneration
   This diagram shows the two protection steps. First, a secret polynomial
   mixes small, overlapping windows of the face or voice embedding into a
   shorter "hardened" vector. Second, IoM-GRP hashing projects this vector
   in many random ways and keeps only the position of the largest value in
   each group. The stored template is this list of positions.

Figure 2. How two protected templates are compared
   File: Figure2_ProtectedMatching
   The stored template and a new template are placed side by side, and the
   system counts how many positions agree. If the count reaches the fixed
   threshold, the person is accepted; otherwise, the person is rejected.

Figure 3. Unlinkability across the design space
   File: Figure3_DesignSpace
   Each cell is one of the 80 settings tested on the development group.
   The colour shows linkability (Dsys); lighter cells are better. The cell
   with a coloured border is the setting that was finally selected and
   sealed, for face and for voice.

Figure 4. The trade-off between recognition and unlinkability
   File: Figure4_Frontier
   Each point is one setting. The horizontal axis shows the error rate and
   the vertical axis shows linkability; points near the lower left are
   best on both. The stepped line marks the best available compromise, and
   the large points are the sealed settings.

Figure 5. Results on development, new and external people
   File: Figure5_Generalisation
   For each group of people, the figure shows the error rate (EER), the
   acceptance rate of genuine users (TAR), the false match rate (FMR) and
   linkability (Dsys). The bars show the 95 percent uncertainty range. The
   development results have no range because they were used for
   selection, not for evaluation.

Figure 6. Ablation: what each step contributes
   File: Figure6_Ablation
   The three versions of the system (with the polynomial, with a simple
   linear map, and with hashing only) are compared on error rate and on
   linkability. On voice, the figure divides the extra error into the part
   caused by reducing the size of the data and the part caused by the
   polynomial itself.

Figure 7. Cancellation of stolen templates, key by key
   File: Figure7_RevocationPerKey
   Each dot is one new key. The horizontal position shows how often an
   attacker's old forged input was still accepted after the key change.
   With hashing only, every key fails completely. With the linear map,
   every key succeeds. With the polynomial, most keys succeed completely,
   but a small number fail, which is why the dots form two separate
   clusters.

Figure 8. What the attack achieves
   File: Figure8_Inversion
   The left panels show that the attack reaches the acceptance threshold
   for every version of the system. The right panels show how closely the
   attacker's reconstruction resembles the real embedding. The polynomial
   gives the lowest similarity, which means it conceals the real
   biometric most effectively.

Supplementary Figure S1. Method and protocol overview
   File: FigureS1_MethodProtocol
   Panel (a) summarises the whole pipeline and the role of the secret key.
   Panel (b) shows how the people were divided into groups, and the point
   at which all settings were sealed before evaluation.

Supplementary Figure S2. Selection of the operating point
   File: FigureS2_OperatingPointSelection
   Panel (a) shows that no face setting reaches the target set for voice,
   which is why the face target was relaxed before testing. Panel (b)
   shows, for each setting that meets its target, the linkability, and
   marks the setting that was selected.


Not included
------------
Figures A to D (detection error curves, score distributions, unlinkability
curves and the revocation score distributions) require the file
score_histograms.json, which is stored on the authors' Google Drive and not
in the repository. They can be produced by running notebooks/figures_only.py
with that file:

    make_figures("path/to/score_histograms.json", "figures/results")

Rebuilding these figures
------------------------
Figures 3 to 8, S1 and S2 are produced by the Python scripts in the
figures/ folder of the repository, and Figures 1 and 2 by the LaTeX (TikZ)
files in reproducibility/code/figures/.
