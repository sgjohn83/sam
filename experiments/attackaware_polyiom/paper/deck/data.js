// Every number on a slide comes from here, and here reads only the stored
// result files. Nothing numeric is typed into build_deck.js.
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const R = (...p) => JSON.parse(fs.readFileSync(path.join(ROOT, "reproducibility", "results", ...p), "utf8"));

const voice = R("heldout", "voice_heldout_result.json");
const face = R("heldout", "face_heldout_result.json");
const ext = R("external", "voice_external_result.json");
const abl = R("ablation", "ablation_result.json");
const inv = R("inversion", "inversion_result.json");
const rev = R("revocation", "revocation_result.json");
const cfg = R("environment", "config_v1_1_4.json");
const env = R("environment", "runtime_environment.json");
const envCpu = R("environment", "environment_extraction_cpu.json");
const ecapa = R("environment", "ecapa_checkpoints.json");
const base = R("scores", "unprotected_baseline.json");
const vctk = R("environment", "stage_vctk_manifest.done.json");
const lfwEmb = R("environment", "stage_lfw_embeddings.done.json");
const lfwRaw = R("environment", "stage_lfw_raw.done.json");
const lfwSplit = R("environment", "lfw_split.json");
const libri = R("environment", "stage_libri_internal.done.json");

const pct = (x, d = 2) => (x * 100).toFixed(d);
const f = (x, d = 3) => Number(x).toFixed(d);
const ci = (arr, d = 2, scale = 100) => `[${(arr[0] * scale).toFixed(d)}, ${(arr[1] * scale).toFixed(d)}]`;

// Sealed operating points and development reference
const op = {
  voice: { M: voice.M, q: voice.q, o: voice.o, tau: voice.c_tau_carried_from_DEV,
    devEER: pct(voice.development_reference.EER, 3), devTAR: pct(voice.development_reference.TAR_DEV, 3),
    devD: f(voice.development_reference.Dsys_DEV, 6) },
  face: { M: face.M, q: face.q, o: face.o, tau: face.c_tau_carried_from_DEV,
    devEER: pct(face.development_reference.EER, 3), devTAR: pct(face.development_reference.TAR_DEV, 3),
    devD: f(face.development_reference.Dsys_DEV, 6) },
};

// Held-out and external, with the carried bootstrap intervals from the ablation file
const av = abl.modalities.voice.arms, af = abl.modalities.face.arms;
const heldout = {
  voice: { EER: pct(voice.EER_HOLDOUT, 3), EERci: ci(av.polyiom.EER_CI, 2),
    TAR: pct(voice.TAR_HOLDOUT_at_dev_threshold, 3), FMR: pct(voice.FMR_HOLDOUT_at_dev_threshold, 3),
    D: f(voice.Dsys_HOLDOUT, 4), Dci: ci(av.polyiom.Dsys_CI, 4, 1),
    nGen: voice.n_genuine, nImp: voice.n_impostor, nSub: voice.n_subjects },
  face: { EER: pct(face.EER_HOLDOUT, 3), EERci: ci(af.polyiom.EER_CI, 2),
    TAR: pct(face.TAR_HOLDOUT_at_dev_threshold, 3), FMR: pct(face.FMR_HOLDOUT_at_dev_threshold, 3),
    D: f(face.Dsys_HOLDOUT, 4), Dci: ci(af.polyiom.Dsys_CI, 4, 1),
    nGen: face.n_genuine, nImp: face.n_impostor, nSub: face.n_subjects },
};
const external = { EER: pct(ext.EER_EXT, 3), TAR: pct(ext.TAR_EXT_at_dev_threshold, 3),
  FMR: pct(ext.FMR_EXT_at_dev_threshold, 3), D: f(ext.Dsys_EXT, 4), nSub: ext.n_subjects,
  nGen: ext.n_genuine, nImp: ext.n_impostor, corpus: ext.corpus,
  fmrAboveTarget: ext.FMR_EXT_at_dev_threshold > cfg.target_fmr };

// Ablation
const ARMS = ["polyiom", "iom_only", "randproj_iom"];
const ablation = {
  voice: ARMS.map(a => ({ arm: a, EER: pct(av[a].EER, 3), EERci: ci(av[a].EER_CI, 3),
    EERnum: av[a].EER * 100, D: f(av[a].Dsys, 4), TAR: pct(av[a].TAR_at_matched_FMR_descriptive, 2) })),
  face: ARMS.map(a => ({ arm: a, EER: pct(af[a].EER, 3), EERnum: af[a].EER * 100, D: f(af[a].Dsys, 4) })),
  costVsRandproj: pct(-abl.modalities.voice.contrasts_vs_polyiom.randproj_iom.delta_EER, 3),
  costVsRandprojCI: ci(abl.modalities.voice.contrasts_vs_polyiom.randproj_iom.delta_EER_CI.map(x => -x).reverse(), 2),
  costVsIom: pct(-abl.modalities.voice.contrasts_vs_polyiom.iom_only.delta_EER, 3),
  dimensionCost: pct(av.randproj_iom.EER - av.iom_only.EER, 3),
  polynomialCost: pct(av.polyiom.EER - av.randproj_iom.EER, 3),
  d: abl.modalities.voice.d, k: abl.modalities.voice.k,
  reproducesSeal: abl.modalities.voice.polyiom_reproduces_sealed_heldout,
};

// Inversion
const iv = inv.modalities.voice.arms, ifc = inv.modalities.face.arms;
const inversion = {
  budget: inv.budget, adversary: inv.adversary,
  voice: ARMS.map(a => ({ arm: a, SAR: pct(iv[a].SAR, 0), cos: f(iv[a].cos_to_true, 3), cosNum: iv[a].cos_to_true })),
  face: ARMS.map(a => ({ arm: a, SAR: pct(ifc[a].SAR, 0), cos: f(ifc[a].cos_to_true, 3), cosNum: ifc[a].cos_to_true })),
  chanceVoice: f(iv.polyiom.cos_chance, 3), chanceFace: f(ifc.polyiom.cos_chance, 3),
  chanceVoiceNum: iv.polyiom.cos_chance, chanceFaceNum: ifc.polyiom.cos_chance,
};

// Revocation
const rv = rev.modalities.voice.arms, rf = rev.modalities.face.arms;
const countKeys = (arms, pred) => ARMS.reduce((o, a) => (o[a] = arms[a].per_key_PRAR.filter(pred).length, o), {});
const halfV = countKeys(rv, x => x >= 0.5), halfF = countKeys(rf, x => x >= 0.5);
const allV = countKeys(rv, x => x === 1.0), allF = countKeys(rf, x => x === 1.0);
const revocation = {
  nKeys: rev.n_fresh_keys,
  voice: ARMS.map(a => ({ arm: a, PRAR: pct(rv[a].PRAR, 2), PRARnum: rv[a].PRAR * 100, ci: ci(rv[a].PRAR_CI, 2),
    median: pct(rv[a].per_key_median, 2), max: pct(rv[a].per_key_max, 2), cos: f(rv[a].cos_to_true, 3) })),
  face: ARMS.map(a => ({ arm: a, PRAR: pct(rf[a].PRAR, 2), PRARnum: rf[a].PRAR * 100, ci: ci(rf[a].PRAR_CI, 2),
    median: pct(rf[a].per_key_median, 2), max: pct(rf[a].per_key_max, 2), cos: f(rf[a].cos_to_true, 3) })),
  halfOrMore: ARMS.reduce((o, a) => (o[a] = halfV[a] + halfF[a], o), {}),
  everySubject: ARMS.reduce((o, a) => (o[a] = allV[a] + allF[a], o), {}),
  totalKeySets: rev.n_fresh_keys * 2,
  deltaVsRandprojVoice: pct(rev.modalities.voice.contrasts_vs_polyiom.randproj_iom.delta_PRAR, 3),
  deltaVsRandprojVoiceCI: ci(rev.modalities.voice.contrasts_vs_polyiom.randproj_iom.delta_PRAR_CI, 3),
  deltaVsIomVoice: pct(rev.modalities.voice.contrasts_vs_polyiom.iom_only.delta_PRAR, 2),
  deltaVsIomVoiceCI: ci(rev.modalities.voice.contrasts_vs_polyiom.iom_only.delta_PRAR_CI, 2),
  cosGapVoice: f(rev.modalities.voice.contrasts_vs_polyiom.randproj_iom.delta_cos, 3),
  cosGapVoiceCI: ci(rev.modalities.voice.contrasts_vs_polyiom.randproj_iom.delta_cos_CI, 3, 1),
  cosGapFace: f(rev.modalities.face.contrasts_vs_polyiom.randproj_iom.delta_cos, 3),
  cosGapFaceCI: ci(rev.modalities.face.contrasts_vs_polyiom.randproj_iom.delta_cos_CI, 3, 1),
  bootstrapAxes: rev.modalities.voice.bootstrap_axes,
};

// Performance preservation (unprotected baseline)
const preservation = base.partitions.map(p => ({
  modality: p.modality, partition: p.partition, protected: p.protected_eer.toFixed(3),
  unprotected: p.unprotected_eer.toFixed(4), ub: p.unprotected_upper_bound_95.toFixed(3),
  cost: p.cost_pp.toFixed(2), resolved: p.baseline_resolved, nGen: p.n_genuine,
  oneError: p.one_genuine_error_pct.toFixed(3),
  protectedNum: p.protected_eer, unprotectedNum: p.unprotected_eer,
}));

// Protocol / frameworks
const protocol = {
  seed: cfg.master_seed, version: cfg.protocol_version, split: cfg.internal_split_counts,
  G: cfg.g, Mgrid: cfg.M_grid, qgrid: cfg.q_grid, ogrid: cfg.overlaps, targetFMR: cfg.target_fmr,
  nConfigs: cfg.M_grid.length * cfg.q_grid.length * cfg.overlaps.length,
  stageA: cfg.attack, stage1: cfg.stage1, stage2: cfg.stage2, budget: cfg.candidate_budget,
  lfw: { raw: lfwRaw.raw_images, valid: lfwEmb.valid_embeddings, eligible: lfwEmb.identities_with_at_least_3_valid,
    excluded: lfwSplit.excluded_exact_overlap_count },
  libri: { speakers: libri.selected_speakers }, vctk: { speakers: vctk.n_speakers, utt: vctk.n_utterances,
    perSpeaker: vctk.utterances_per_speaker, mic: vctk.mic, sr: vctk.target_sample_rate, corpus: vctk.corpus,
    resampler: vctk.resampler },
  torch: env.torch, torchCpu: envCpu.torch, python: env.python.split(" ")[0], gpu: env.gpu, cuda: env.cuda_version,
  speechbrain: env.speechbrain, facenet: env["facenet-pytorch"], numpy: env.numpy, pandas: env.pandas,
  ecapaRepo: ecapa.repo_id, ecapaRev: ecapa.revision.slice(0, 12),
  nBootstrap: abl.n_bootstrap, confidence: abl.confidence,
};

module.exports = { op, heldout, external, ablation, inversion, revocation, preservation, protocol, ARMS };
