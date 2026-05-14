# V8.1 BIOSEMOTIC ABLATION STUDY - LAUNCH INSTRUCTIONS

## 🚀 EXECUTE ON COLAB (authuser=1 account)

### Step 1: Navigate to Colab
Go to: https://colab.research.google.com/drive/1t4vX2kalq1JsfC2M3u9rXyrv-jDWG5iL?authuser=1

### Step 2: Copy & Paste Commands

#### **Option A: Quick Execution**
```python
# Download and run V8.1 script directly
!curl -sL "https://github.com/Das-rebel/ChuckleNet/releases/download/v0.1-data/colab_biosemotic_ablation_v8.py" -o /tmp/v81.py && python3 /tmp/v81.py
```

#### **Option B: Step-by-Step (for monitoring)**
```python
# 1. Check GPU compatibility
!nvidia-smi

# 2. Download script
!curl -sL "https://github.com/Das-rebel/ChuckleNet/releases/download/v0.1-data/colab_biosemotic_ablation_v8.py" -o /tmp/v81.py

# 3. Verify script
!ls -la /tmp/v81.py
!head -20 /tmp/v81.py

# 4. Run ablation study
!python3 /tmp/v81.py
```

## 📊 V8.1 EXPERIMENT CONFIGURATION

| Phase | Experiments | Purpose |
|-------|-------------|---------|
| **A** | A1, A2 | Baselines (no biosemotic features) |
| **B** | B1, B2 | Full 27-dim biosemotic model |
| **C** | C1-C7 | Single dimension ablation |
| **D** | D1-D3 | Group ablation |

### **Key Parameters from V7:**
- Dropout: 0.2 (improved from V8's 0.1)
- Batch Size: 12 (improved from V8's 16)  
- Label Smoothing: 0.1 (new)
- Weight Decay: 0.02 (improved from V8's 0.01)
- Positive Weight: 5.0, 3.0

## ⚡ EXPECTED DURATION
- **14 experiments × 10 epochs** = ~140 epochs total
- **Expected time**: 2-4 hours on T4 GPU
- **Progress saved incrementally** every experiment

## 📁 OUTPUT FILES
- `/tmp/v81_results.json` - All experiment results
- `/tmp/v81_best_model.pt` - Best performing model
- Local saves after each experiment

## 🔍 MONITOR PROGRESS

Track progress with:
```python
# Check current results
import json
with open('/tmp/v81_results.json') as f:
    results = json.load(f)
    
print(f"Completed: {len(results)}/14 experiments")
for r in results:
    print(f"{r['name']}: ValF1={r['val_f1']:.4f}")
```

## 🎯 NEXT STEPS AFTER COMPLETION

1. **Analyze Results**: Identify which biosemotic dimensions are most important
2. **Compare V7 vs V8.1**: Check if V7 hyperparameters improved performance  
3. **V9 Audio Fusion**: Begin multimodal integration with audio features

## ⚠️ TROUBLESHOOTING

If GPU fails:
- Change runtime: Runtime → Change runtime type → T4 GPU
- Clear runtime: Runtime → Factory reset runtime
- Restart cell after GPU change