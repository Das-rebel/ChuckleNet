# ChuckleNet Master Location Map (Sep 8, 2026) — single source of truth

## CANONICAL
| Asset | Location |
|---|---|
| Project dir (canonical) | `~/autonomous_laughter_prediction_essential/` |
| **RUN THIS** Colab notebook | repo: `ChuckleNet_Final_Colab_v20.ipynb` · Drive: `gdrive:chuckle_net_1000/ChuckleNet_Final_Colab_v20.ipynb` |
| Colab data (ready, 621 m4a + VTTs) | `gdrive:chuckle_net_1000/audio/*.m4a` + `gdrive:chuckle_net_1000/vtt/*.vtt` |
| Results output dir (Colab writes here) | `gdrive:chuckle_net_1000` → `MyDrive/chuckle_net_results/` (`*_v20` namespace) |
| Decision graph | `docs/DECISION_GRAPH.md` (GitHub synced) |
| Label hierarchy | `docs/LABEL_HIERARCHY.md` |
| Research+Monetization status | `docs/RESEARCH_AND_MONETIZATION_STATUS.md` |
| Master plans | `docs/CLEAN_PROJECT_PLAN.md`, `docs/recovered/DEFINITIVE_PLAN.md` |

## RECOVERED DOCS (lost Jun→Sep, restored from session transcripts)
`docs/recovered/`: PRD_V6_MULTI_PRODUCT_LAUGHTER_PLATFORM.md · LAUGHTER_PREDICTION_RESEARCH_VISION.md · DEFINITIVE_PLAN.md · PRIORITY_EXECUTION_PLAN.md (+ `gdrive:chuckle_net_backups/recovered_prd_vision_docs/`)

## DATA
| Asset | Location |
|---|---|
| 621 audio m4a | local `~/data/utterances/vtt_audio_local/` + `gdrive:chuckle_net_1000/audio/` |
| 628 VTT | local `~/data/chuckle_vtt_labels/` + `gdrive:chuckle_net_1000/vtt/` |
| Gillick gold features (162v) | cached `/tmp/gillick_reval/fusion_features.npz` (FRAGILE — re-extract from Drive if tmp cleared) |
| Gillick audio pool (271 mp3) | `~/data/gillick_audio/` |
| July-16 lexicon npz (RETIRED labels) | local `data/july16_recovered/` + `gdrive:subhajit-comedy-data/` + `gdrive:chuckle_net_backups/july16_dataset_recovered/` |
| Label source files | GitHub `Das-rebel/chuckle_data/aligned_utterances.jsonl` (lexicon, npz labels) · `Das-rebel/chuck-audio-notebooks/utterances_clean.jsonl.gz` (caption markers, 239K rows) |
| 634-video comedy ID list | repo `docs/all_comedy_ids.txt` |
| Kaggle frame dataset (626v) | `~/ChuckleNet/kaggle_frame_dataset/` |

## GISTS (provenance)
v20 (current) → gist `<see repo notebook>` · v19 `188a3bc5d4346c8189372f00c8bc2d39` (superseded by v20) · v18 `7033657a` (broken)

## REPOS
`Das-rebel/ChuckleNet` (canonical) · `Chucklenet_predictor` (SDK skeleton, aspirational README) · `chuckle_data` · `chuck-audio-notebooks` (correct spelling)

## BACKUPS (NO-DELETES policy)
- Local: `~/backups/` (essential_full_20260907_*.tar.gz, essential_docs_*)
- Drive: `gdrive:chuckle_net_backups/` (92+ objects incl. recovered_prd_vision_docs/, july16_dataset_recovered/)
- Post-run v20: copy `chuckle_net_results/` JSONs into `gdrive:chuckle_net_backups/v20_results/`

## HISTORIC ARCHIVE (don't reference for current work)
`~/ChuckleNet/` + mirror `~/chucklenet-local/` (300+ April-era docs, context.db) · `docs/archive/` (6 PRDs) · memory keys `chucklenet.*` in pi memory store
