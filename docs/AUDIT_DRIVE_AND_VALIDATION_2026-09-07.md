# Full Audit — Drive, Validation, Timeline, Decision Graph
**Date:** 2026-09-07 · **Type:** disk+Drive+session-transcript verified audit · **Supersedes:** none (extends DECISION_GRAPH.md + PROJECT_REVIEW_AND_SCALEUP.md)

> Rule: every claim below was checked against actual artifacts (local disk, gdrive via rclone,
> GitHub API, PI session transcripts, memory store). Items that could not be verified are
> marked UNVERIFIED, not silently dropped. Nothing was deleted in this audit; corrections
> are additive.

---

## 1. Executive verdict

The project has one honest headline: **IoU-F1@0.2 = 0.310** (118 held-out videos, 5-fold
GroupKFold, real VTT labels) — below the StandUp4AI baseline 0.51. That gap is the project.
The fusion architecture (WavLM+prosody → MLP) is confirmed the best model and the scaling
target. The Gillick real-label claim — previously flagged "missing validation" — is now
**REVALIDATED with a saved result JSON** (see §3). The 1000-video corpus on Drive is far
larger than docs believed (621 audio / 628 VTT, not 180). The only large extraction run
(Sep 5) produced real features but **broken labels** (see §4). The HuggingFace model card
has **regressed to false claims a second time** (see §6).

---

## 2. Verified timeline (March → September 2026)

| Era | Work done | Surviving evidence |
|---|---|---|
| Mar 2026 | Text-humor origin: XLM-R, 102 transcripts, ToM/GCACU, cross-domain eval | `ChuckleNet/cross_domain_results/cross_domain_report_20260329_131726.md` (internal scores self-flagged inflated) |
| May 2026 | 15K-utterance YouTube dataset; XLM-R word-level baseline (`experiments/xlmr_standup_baseline`), WESR splits; Kaggle 48v word model (cv-F1 0.238±0.029); "canonical test F1 0.5417" (per-laughter-type, XLM-R — NOT Gillick) | `utterances_15k.jsonl` (still primary local data); Kaggle_Training_48v_results.json; May session transcripts |
| Jun 2026 | Mostly unrelated A3M work; project quiet | little |
| Jul 2026 | WavLM era: 660+646 embeddings extracted; v15 notebooks; 555-video train (honest word-F1 test 0.121 / val 0.218 — worst honest result, undocumented until this audit); prosody training runs | gdrive wavlm_* dirs; `gdrive:wavlm_training_results/results.json` |
| Aug 2026 | Gillick fresh 162v + fusion experiment (claimed 0.541 — revalidated Sep 7, see §3); AST labeling dead end; cascade_data (unlogged, 141MB); scale221 (OOF F1 0.206); **honest pivot: 118v IoU-F1@0.2 = 0.310** (JSONs dated Aug 25–26) | `docs/FULL_FUSIONMLP_118V_RESULTS.json`, `HYPOTHESIS_TEST_RESULTS.json`, `FUSIONMLP_40V_RESULTS.json`; gdrive `chuckle_net/gillick_data/` |
| Sep 2026 | v17→v18→v19 notebook repair (v19 = execution-simulation validated); HF card honest fix (Sep 4 14:25) then REGRESSION same day (6 README overwrites 19:02–20:37 → false F1=0.960); PNG spam Sep 5; this audit | gist `188a3bc5...` (v19, canonical); HF commit history |

## 3. Gillick fusion claim — RESOLVED (was: "missing validation")

**Before this audit:** docs cited "Gillick AudioSet REAL labels (162v) F1 fusion 0.541 ± 0.030
(WavLM-only 0.505, prosody-only 0.504)" with NO result JSON anywhere (checked local disk,
Drive, GitHub, gists, notebook outputs — the Drive `fusion_results.json` belongs to a
DIFFERENT experiment: 87v/21,468-sample random-split run, val 0.9595/test 0.9729 — do not cite).

**Resolution:** the experiment's artifacts survived at `gdrive:chuckle_net/gillick_data/`:
- `fusion_features.npz` — 1,581 segments × 791-dim (768 WavLM + 23 prosody), 162 videos,
  51.5% positive, REAL AudioSet labels, video IDs included
- `fusion_best.pt` — the trained model (2.2MB)

**Revalidation run (2026-09-07, this audit):** 5-fold GroupKFold by video, OOF predictions,
fresh MLP (791→512→256→64→1, BN+dropout, AdamW 1e-3, 30 epochs):

| Model | Segment-F1@0.5 |
|---|---|
| **FUSION 791** | **0.5590** |
| WavLM-only 768 | 0.5478 |
| Prosody-only 23 | 0.5374 |

Ordering reproduced (fusion wins on real labels); fusion gain +2.0% over WavLM-only
(original claimed +7% from a single cross-video split — protocol difference, both honest).
**Saved result JSON: `docs/GILLICK_REVALIDATION_RESULTS.json`.**
Citable form: *Gillick-162v real-label ablation, fusion 0.559 / WavLM-only 0.548 /
prosody-only 0.537 (revalidated 2026-09-07, OOF GroupKFold).*

Side finding: the prosody 23-dim block in THIS dataset has NO dead dims (unlike the
87v-era `wavlm_training_data_expanded` prosody dims 10–22 = zeros). The dead-dim defect
was in the old extraction, not in prosody features generally.

## 4. Google Drive audit (2026-09-07, rclone, 81 top-level entries)

| Asset | Verified state | Action taken |
|---|---|---|
| `chuckle_net_1000/{audio,vtt}/` | **621 audio + 628 VTT** (docs previously said 180) | docs updated |
| `chuckle_net_output/extraction_checkpoint.npz` | 134MB, **45,192×795 features, 279 videos, pos_rate=1.6%** → labels are broken (sparse-label join, NOT VTT-utterance labels). No per-row timestamps stored → labels not re-derivable. NaN-free, loader proven at scale | documented as write-off; do NOT resume its labels; v19 must log per-video pos-rate during extraction |
| `chuckle_net_output/utterance_features.npz` | 0 samples (failed v18-era run, Sep 3) | left in place, marked junk |
| `chuckle_net/gillick_data/` | fusion_features.npz (Gillick 1581×791) + fusion_best.pt + MISMATCHED fusion_results.json (87v random-split) | features+model = the revalidation source |
| `chuckle_net/` (AST era, Aug 7–8) | ast_labeled_clips.csv, ast_prosody_model.pkl — AST labeling dead end (1–3% pos) | no action, documented |
| `cascade_data/stage1_{train,val,held_out}.jsonl` | 141MB, Aug 6, provenance UNKNOWN (no producing script found locally) | flagged UNVERIFIED — identify or ignore |
| `wavlm_training_results/results.json` | 555 videos (445/55/55), val F1 0.218 / test 0.121 | now documented (honest scale datapoint) |
| `standup4ai/experiments/best_fusion_model.pt` | 2.2MB, Aug 2 — matches 791-dim era | dead checkpoint (dead dims), artifact only |
| `standup4ai/models/top200_prosody_model.pt` | pseudo-label circular model | do not cite |
| `data/.../eval_youtube_labeled.jsonl` (121,167 utts) | **labels INVALID**: 0.1% positive on 100% empty-text utterances — not VTT laughter labels | dataset_summary "labels unknown" was closer to truth; do not train on it |
| backups | `gdrive:chuckle_net_backups/essential_full_20260907_171110.tar.gz` (+ earlier partial dir copy) | failsafe snapshots |

## 5. Model/feature-count facts (re-confirmed)

- `models/` local dir is EMPTY. Neither `models/fusion_mlp_v2.pt` nor `models/energy_model/*`
  exists on local disk. Only real local .pt files: `training/prosody_fusion_embeddings/fusion_mlp_model.pt`
  (405-dim lineage), `training/prosody_fusion_results/best_model.pt`, `scale221/*` (2),
  `Kaggle_48v_word_level_model.pt`.
- Feature dims: 789 = 768+21, 791 = 768+23 (old extraction, dead dims there), 795 = 768+27
  (v19/GitHub Colab extraction). Resolution unchanged: **train fresh, auto-size `dim=X_s.shape[1]`,
  never resume old checkpoints.**

## 6. Publication state

- **HF `Hayasuki/chuckleNet-v2` REGRESSED (2nd incident):** honest fix Sep 4 14:25 → six
  README overwrites Sep 4 19:02–20:37 → live card claims F1=0.960 "production-ready" with NO
  source JSON anywhere; claims prosody>fusion (contradicts honest ablation). 231 downloads.
  Root pattern: promo/marketing sessions overwrite honest artifacts. **Required fix:**
  re-fix card with JSON-verified numbers + provenance links to result JSONs; add post-session
  card verification to workflow. (Status: PENDING)
- **GitHub `Das-rebel/autonomous_laughter_prediction`:** this audit + updated DECISION_GRAPH,
  PROJECT_REVIEW_AND_SCALEUP, GILLICK_REVALIDATION_RESULTS.json pushed via Contents API
  (local git tree remains home-dir-broken; API push is the proven path).
- **Gists:** v19 `188a3bc5...` = canonical (verified live). v8–v18 = superseded.

## 7. Corrections applied to DECISION_GRAPH.md (this audit)

1. G2 + PRIORITY STACK: v18 → **v19 canonical**
2. METRICS honest table: Gillick row updated to revalidated numbers + JSON citation
3. SUSPECT table: + HF card 0.960 (regressed), + Drive fusion_results.json 0.973 random-split,
   + scale221 results.json 0.879 teacher-circularity, + YouTube 121K labels invalid
4. MODEL LAYER: marked nonexistent files as lost (`models/fusion_mlp_v2.pt`,
   `models/energy_model/*`); kept as historical description only
5. DATA LAYER: 180 → 621 files; + Sep-5 checkpoint postmortem; + Gillick revalidation artifacts
6. DEAD ENDS: + AST labeling at scale, + YouTube-label packaging, + cascade_data unlogged

## 8. Standing rules (unchanged + reinforced)

- Honest metrics: claims must match result JSONs. F1>0.7 needs real labels + video-level
  held-out split + no circularity.
- Notebooks: no ship without per-cell compile + execution simulation of critical loops +
  independent reviewer (v19 standard).
- **Persist `(vid, utt_start, utt_end)` alongside every feature checkpoint** so labels are
  always re-derivable (lesson from the Sep 5 write-off).
- No deletes without backup; backups to local `~/backups/` AND `gdrive:chuckle_net_backups/`.
