# V8.1 BIOSEMOTIC ABLATION STUDY - CURRENT STATUS

## 🎯 Live Training Status (2026-04-27)

### ✅ EXPERIMENT 1/14: A1_baseline_pw5 - RUNNING
- **Current Epoch:** 1/10 completed
- **Train Loss:** 0.0837
- **Val Loss:** 0.0339
- **F1 Score:** 0.5304
- **Precision:** 0.428
- **Recall:** 0.697
- **Time per epoch:** ~29 minutes (1746.0s)
- **Started:** Experiment 1/14
- **Expected completion:** ~4.8 hours for Experiment 1

## 🔧 Critical Issues Resolved

### ✅ FOCAL LOSS TENSOR SIZE MISMATCH - FIXED
**Original Error:** `RuntimeError: The size of tensor a (810) must match the size of tensor b (2)`

**Root Cause:** Focal loss code in compute_loss function causing tensor dimension mismatches
**Solution:** Complete removal of ALL focal loss code, use only simple CrossEntropyLoss

**Success Confirmed:** Training now progressing normally through epochs

### 🛠️ Final Clean Version Applied
- **File:** `/tmp/v81_final_clean_version.py`
- **Key Changes:**
  - Complete removal of focal loss calculations
  - Simple cross entropy loss only: `nn.CrossEntropyLoss(weight=weights, ignore_index=-100)`
  - Proper tensor dimension handling: `flat_logits = laughter_logits.view(-1, laughter_logits.size(-1))`
  - Use `ignore_index=-100` to skip padding tokens

## 📊 Data Configuration
- **Training:** 32,992 examples
- **Validation:** 4,124 examples
- **Test:** 4,124 examples
- **Biosemotic dimensions:** 32
- **Model:** FacebookAI/xlm-roberta-base
- **GPU:** Tesla T4 (compute 7.5) - Working perfectly

## 🚀 Training Parameters (V7 Hyperparameters)
- **Batch Size:** 12
- **Dropout:** 0.2
- **Weight Decay:** 0.02
- **Positive Weight:** 5.0
- **Epochs:** 10 per experiment

## 📈 Experiment List
1. **A1_baseline_pw5** - Current (pos_weight=5.0, disable_all_aux=True)
2. A2_baseline_pw3 - Pending
3. B1_full32dim - Pending
4. B2_full32dim - Pending
5. C1_no_duchenne - Pending
6. C2_no_incongruity - Pending
7. C3_no_tom - Pending
8. C4_no_cue - Pending
9. C5_no_structural - Pending
10. C6_no_linguistic - Pending
11. C7_no_metadata - Pending
12. D1_core_cognitive - Pending
13. D2_no_cognitive - Pending
14. D3_surface_only - Pending

## 🎯 Next Steps
- **Continue monitoring** Experiment 1/14 through all 10 epochs
- **Collect results** after each experiment completion
- **Update this file** with progress as training continues
- **Analyze biosemotic dimension importance** once all experiments complete

## 📁 Related Files
- `/tmp/v81_final_clean_version.py` - Working training script
- `/tmp/v81_results.json` - Incremental results (will be created)
- `/tmp/v81_final_results.json` - Final results (will be created)
- `https://colab.research.google.com/drive/1t4vX2kalq1JsfC2M3u9rXyrv-jDWG5iL?authuser=1` - Live training notebook