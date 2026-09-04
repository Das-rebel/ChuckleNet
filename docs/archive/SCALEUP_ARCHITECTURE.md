# Scaleup Architecture: 71 → 500+ Videos

**Date:** 2026-06-20
**Goal:** Scale from 71 gold-standard videos to 500+ video production pipeline
**Purpose:** Enable Paper 1 (arXiv) scale claims + Paper 2 (INTERSPEECH) WavLM fine-tuning

---

## Current State (Baseline)

### Data Assets (Validated)
| Asset | Count | Location |
|-------|-------|----------|
| WavLM Embeddings | 71 files (1 per video) | `/Users/Subho/data/chuckle-net/wavlm_embeddings/` |
| Prosody Features | 5.3MB | `/Users/Subho/data/chuckle-net/prosody_phaseD.json` |
| Aligned Utterances | 15,000 | `/Users/Subho/data/chuckle-net/aligned_utterances.jsonl` |
| Language Breakdown | EN: 80%, ZH: 17%, HI: <3% | Paper 1 claim |

### Current Pipeline (Validated)
```
71 YouTube Videos
       ↓ [Whisper Transcription]
       ↓ [VTT Alignment]
       ↓ [YouTube [laughter] Markers]
       ↓ [Manual Verification]
Gold-Standard: 71 videos (15K utterances)
       ↓ [WavLM Extraction (GPU)]
       ↓ [Prosody Extraction (CPU)]
       ↓ [Feature Storage]
Validated Features: 71 files + 15K embeddings
```

### Current Results (Paper 1 v3)
- **Ensemble F1:** 0.587 (held-out)
- **XLM-R F1:** 0.152 (held-out)  
- **WavLM F1:** 0.280 (held-out)
- **Improvement:** 3.9× over text-only

---

## Scaleup Target

### Dataset Targets
| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Videos | 71 | 500+ | +429 |
| Utterances | 15,000 | 100,000+ | +85,000 |
| Languages | 2 (EN, ZH) | 3+ (EN, ZH, HI) | HI needs expansion |
| WavLM Embeddings | 71 files | 500+ files | New extraction needed |
| Prosody Features | 15K samples | 100K+ samples | New extraction needed |

### Pipeline Stages
```
Stage 1: Raw Collection (500+ videos)
       ↓
Stage 2: Automated Curation (filter to ~300)
       ↓
Stage 3: Feature Extraction (WavLM + Prosody)
       ↓
Stage 4: Gold-Standard Subset (71 → 150 videos)
       ↓
Stage 5: Model Training (Paper 2 experiments)
```

---

## Scaleup Architecture

### Stage 1: Raw Collection Pipeline

```python
# Scaleup Collection Architecture
class YouTubeCollectionPipeline:
    """
    Scalable YouTube comedy video collection.
    Targets: 500+ raw videos → 300 curated videos
    """
    
    def __init__(self):
        self.candidates = []  # 500+ video IDs
        self.language_filter = LanguageDetector()
        self.quality_filter = QualityEstimator()
        self.laughter_marker_filter = LaughterDensityChecker()
    
    def collect_candidates(self):
        """Collect 500+ comedy video candidates"""
        # Sources:
        # - Existing 100 videos (17 with audio)
        # - StandUp4AI dataset (Barriere et al., ACL 2025)
        # - MultiLinguahah (Callejas et al., 2026)
        # - New YouTube scraping
        pass
    
    def filter_pipeline(self, video):
        """Multi-stage filtering"""
        # Stage 1: Language detection (EN/ZH/HI)
        if not self.language_filter.is_supported(video):
            return False
        
        # Stage 2: Acoustic quality (SNR, clipping)
        if not self.quality_filter.passes(video):
            return False
        
        # Stage 3: Laughter density ([laughter] markers)
        if not self.laughter_marker_filter.has_sufficient_laughter(video):
            return False
        
        # Stage 4: Duration (30s - 30min)
        if not self.duration_filter.in_range(video):
            return False
        
        return True
    
    def curate(self):
        """500 → 300 videos via filtering"""
        pass
```

### Stage 2: Feature Extraction Pipeline

```python
# Scaleup Feature Extraction
class ScaleupFeatureExtractor:
    """
    Process 300+ videos for WavLM + Prosody features.
    GPU: WavLM extraction (batch processing)
    CPU: Prosody extraction (parallel)
    """
    
    def __init__(self):
        self.wavlm_model = None  # microsoft/wavlm-base
        self.prosody_extractor = openSMILE()  # eGeMAPS config
    
    def extract_wavlm_batch(self, video_ids: List[str]):
        """GPU: Extract WavLM embeddings for batch"""
        # Batch size: 10-20 videos per GPU session
        # Storage: /data/chuckle-net/wavlm_embeddings/{video_id}.json
        pass
    
    def extract_prosody_batch(self, video_ids: List[str]):
        """CPU: Extract eGeMAPS prosody features"""
        # Parallel processing with joblib
        # Storage: prosody_phaseD.json (append mode)
        pass
    
    def run_pipeline(self):
        """Execute full extraction pipeline"""
        # 1. Load video list (300 videos)
        # 2. Extract WavLM (GPU, ~2 min per video)
        # 3. Extract Prosody (CPU, ~30 sec per video)
        # 4. Store embeddings + features
```

### Stage 3: Gold-Standard Subset Selection

```python
# Scaleup Gold-Standard Selection
class GoldStandardSelector:
    """
    From 300 curated videos → 150 high-quality gold-standard.
    Criteria:
    - Perfect [laughter] marker alignment
    - High inter-annotator agreement
    - Balanced language representation
    - Diverse comedian coverage
    """
    
    def select(self, candidates: List[Video]):
        """300 → 150 via quality scoring"""
        scores = []
        for video in candidates:
            score = (
                0.4 * video.laughter_alignment_score +
                0.3 * video.acoustic_quality +
                0.2 * video.language_balance +
                0.1 * video.diversity_score
            )
            scores.append((video, score))
        
        # Select top 150
        scores.sort(key=lambda x: x[1], reverse=True)
        return [v for v, s in scores[:150]]
```

---

## Data Storage Architecture

```
/data/chuckle-net/
├── raw/                           # Raw YouTube downloads
│   ├── videos/                    # 300+ MP4 files
│   └── transcripts/               # Whisper outputs
├── curated/                       # After filtering
│   └── 300_videos.jsonl
├── embeddings/                    # WavLM outputs
│   ├── wavlm_embeddings/          # 300+ JSON files (768-dim)
│   └── wavlm_embeddings.tar.gz    # Compressed backup
├── prosody/                       # eGeMAPS outputs
│   ├── prosody_phaseD.json        # 300 videos (appended)
│   └── prosody_features.tar.gz
├── utterances/                    # Aligned utterances
│   ├── aligned_utterances.jsonl   # 100K+ utterances
│   └── utterance_index.json       # Fast lookup
└── gold_standard/                 # High-quality subset
    ├── gold_71/                   # Original 71 (Paper 1)
    └── gold_150/                  # New 150 (Paper 2)
```

---

## Training Pipeline Architecture

### Paper 2: WavLM Fine-Tuning (INTERSPEECH 2027)

```python
# INTERSPEECH 2027: LoRA fine-tuning on gold_150
class WavLMFinetuner:
    """
    LoRA fine-tuning for WavLM on laughter detection.
    Target: 150 gold-standard videos (~30K utterances)
    """
    
    def __init__(self):
        self.base_model = "microsoft/wavlm-base"
        self.lora_config = {
            "r": 8,
            "lora_alpha": 16,
            "target_modules": ["k_proj", "v_proj"],
            "lora_dropout": 0.1
        }
    
    def train(self, train_data, val_data):
        """Fine-tune with LoRA"""
        # Expected improvement: 0.28 → 0.35-0.45 (+25-30%)
        pass
    
    def evaluate(self, held_out_comedians):
        """Standard held-out evaluation"""
        # Same comedians as Paper 1 for fair comparison
        pass
```

### Colab Setup for Scaleup

```python
# WavLM_LoRA_Finetune_Colab.ipynb (already created)
# 
# Scaleup additions needed:
# 1. Load 150 gold-standard videos (not just 71)
# 2. Increase batch size for faster processing
# 3. Add checkpointing for 100K+ utterance dataset
# 4. Multi-GPU support for production scale
```

---

## Collection Expansion Strategy

### Priority 1: English Comedy (100 → 200)
- Sources: Russell Peters, Dave Chappelle, Kevin Hart
- Method: YouTube scraping + StandUp4AI integration
- Expected: +100 videos, +20K utterances

### Priority 2: Chinese Comedy (12 → 50)
- Sources: Li Zhi, Guo Degang, crony humor
- Method: Bilibili + YouTube Chinese comedy
- Expected: +38 videos, +8K utterances

### Priority 3: Hindi/Hinglish (2 → 30)
- Sources: Stand-up India, Netflix India comedy
- Method: YouTube + streaming platforms
- Expected: +28 videos, +6K utterances

### Priority 4: Additional Languages (0 → 10)
- French, Spanish, Japanese comedy
- Method: International comedy specials
- Expected: +10 videos, +2K utterances

---

## Implementation Timeline

| Phase | Duration | Tasks | Deliverable |
|-------|----------|-------|-------------|
| **Phase 1** | 1-2 weeks | Collection pipeline setup | 300 video candidates |
| **Phase 2** | 2-3 weeks | Feature extraction (GPU batch) | 300 WavLM + Prosody |
| **Phase 3** | 1 week | Gold-standard curation | 150 high-quality videos |
| **Phase 4** | 2-4 weeks | Paper 2 experiments | F1 improvement validated |
| **Phase 5** | 1 week | Paper 2 writeup | INTERSPEECH 2027 submission |

---

## Key Dependencies

| Component | Status | Location |
|-----------|--------|----------|
| WavLM LoRA Colab | ✅ Ready | `/Users/Subho/WavLM_LoRA_Finetune_Colab.ipynb` |
| Data package (71) | ✅ Ready | Google Drive: `1Pn2fpMnF79yN-1yTZMeJJvZkBYsuyVNw` |
| Prosody extractor | ✅ Working | `extract_egemaps_features.py` |
| WavLM extractor | ⚠️ Needs batch | `extract_wavlm_batch.py` |
| Collection pipeline | ❌ Needs build | `collect_youtube_fast.py` |
| Quality filter | ❌ Needs build | Quality estimation module |

---

## Next Steps

1. **Immediate:** Get arXiv endorsement → Submit Paper 1
2. **Short-term:** Build collection pipeline (300 videos)
3. **Medium-term:** Extract features for 300 videos  
4. **Long-term:** Curate gold_150 → Run Paper 2 experiments

---

*Last updated: 2026-06-20*
*Status: Scaleup architecture designed, awaiting endorsement + Paper 1 submission*
