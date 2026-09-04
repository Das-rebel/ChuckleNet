# Project Charter: Autonomous Laughter Prediction

**Project:** Biosemiotic Evolution and Cascade Dynamics for Autonomous Laughter Prediction
**Date:** 2026-04-03
**Hardware:** Apple Mac M2, 8GB RAM

---

## 1. Research Scope

### Core Objective
Develop an autonomous laughter prediction system based on biosemiotic evolution principles and cascade dynamics, capable of operating on resource-constrained Apple Silicon (8GB RAM).

### Research Focus Areas

1. **Biosemiotic Evolution**: Model Duchenne vs Non-Duchenne laughter using evolutionary features:
   - Airflow dynamics (exhalation-only vs controlled sequence)
   - Neural control pathways (brainstem/limbic vs speech motor)
   - Phylogenetic priors (hominin phonic sociality)

2. **Cascade Dynamics**: Implement cascade detection for:
   - Multiplicative dominance patterns (Duchenne laughter)
   - Additive stabilization patterns (Non-Duchenne laughter)

3. **Cognitive Architecture (GCACU)**: Integrate:
   - Gated Contrast-Attention (ToM for incongruity monitoring)
   - Theory of Mind (audience/comedian mental state tracking)
   - HitEmotion (emotional state for sarcasm detection)
   - Transfer Entropy (speaker-audience informational handshake)

4. **Multi-Layered Social Alignment (MLSA)**:
   - Violation Delta (V): ESR deviation scoring
   - Knowledge Alignment (K): Common Knowledge Graph
   - Social Distance (D): Contextual/interactional cues
   - Probability head: P(laugh) = sigma(alpha*V + beta*K - gamma*D)

5. **Universal Persistence Layer (UPL)**: Uncertainty-aware pseudo-labeling

6. **TurboQuant**: 3-bit KV cache for 6x memory compression

---

## 2. Target Benchmarks

| Benchmark | Target | Current Baseline |
|-----------|--------|------------------|
| Word-Level Laughter F1 | > 0.7222 | TBD |
| Textual Incongruity F1 | > 77.0% | TBD |
| Vocal Event Detection | > 38.0% | TBD |
| Sincerity Detection | > 82.1% | TBD |
| Memory Compression | 6x | TBD |

---

## 3. Key Components

| Component | Owner | Description |
|-----------|-------|-------------|
| GCACU | Task 31 | Gated Contrast-Attention Cognitive Architecture |
| ToM | Task 31.2 | Theory of Mind state modeling |
| MLSA | Task 30 | Multi-Layered Social Alignment |
| UPL | Task 32.3 | Universal Persistence Layer |
| TurboQuant | Task 27.3 | 3-bit KV cache quantization |
| QLoRA | Task 27.2 | 4-bit model compression |
| Engram | Task 27.4 | O(1) SSD offloading |

---

## 4. Hardware Constraints

- **Device:** Apple Mac M2
- **RAM:** 8GB
- **Target Peak Memory:** < 5GB during training
- **MLX Framework:** Required for Apple Silicon optimization

---

## 5. Success Criteria

The project is considered successful when:

1. All five benchmark thresholds are met or exceeded
2. Full training runs complete without OOM on 8GB Mac M2
3. Autonomous research loop operates continuously (5-minute cycles)
4. Reproducibility package enables independent reproduction

---

## 6. Task Dependencies

```
Task 24 (Project Init)
    └── Task 25 (Data Acquisition)
            └── Task 26 (Label Harmonization)
                    ├── Task 27 (Hardware Optimization) ──┐
                    ├── Task 28 (Biosemiotic Evolution)   │
                    └── Task 30 (MLSA Module)             │
                            └── Task 31 (GCACU Integration)
                                    └── Task 32 (Autoresearch Loop)
                                            └── Task 33 (Benchmark Validation)
                                                    └── Task 34 (Final Integration)
```

---

## 7. Governance

- **Methodology:** Empirical, hypothesis-driven
- **Validation:** WESR-balanced benchmark suite
- **Iteration:** Codex-driven autonomous research loop
- **Safety:** Auto-rollback on failure, quarantine invalid hypotheses
