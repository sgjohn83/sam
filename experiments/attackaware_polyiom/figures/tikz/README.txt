Academic split figures - updated source
=======================================

Figure1_TemplateGeneration.tex   building a protected template
Figure2_ProtectedMatching.tex    comparing two protected templates
assets/imagegen_verified/        the biometric sample mark used by both

Build
-----
    pdflatex Figure1_TemplateGeneration.tex
    pdflatex Figure2_ProtectedMatching.tex

Needs: texlive-latex-base, texlive-pictures, texlive-fonts-recommended,
texlive-latex-extra (for standalone.cls). Run pdflatex from this folder so
the relative path to assets/ resolves.

Place in the paper
------------------
Both canvases are 18.0cm = 7.09in wide, so they drop in at \textwidth with
no scaling and every type size is the size it prints at:

    \includegraphics[width=\textwidth]{Figure1_TemplateGeneration.pdf}

Do not scale them down - the smallest type is already at its floor.

Notes on this revision
----------------------
- Cells outside the current window are ghosted, so the arrow leaving a
  window carries five values rather than the whole embedding.
- The step between window positions is a measured arrow labelled 5 - o*,
  so the overlap is read off the drawing instead of stated.
- Every part is named (embedding z, hardened vector y, q* projections per
  group, M* groups, protected template h) and every arrow says what flows.
- In Figure 2 the threshold is a position on a scale with reject and
  accept as regions, so the decision rule is visible; the padlock marks
  tau* as frozen.
- Colour names do not shadow xcolor's built-in blue/green/red.
