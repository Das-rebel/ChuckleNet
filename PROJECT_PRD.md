# Autonomous Laughter Prediction - Project Requirements Document

## Project Overview
Unified Autonomous Laughter Prediction: Integrating Biosemiotic Evolution and Cascade Dynamics within an 8GB Autoresearch Paradigm

## Target Benchmarks
- Word-Level Laughter: F1 > 0.7222
- Textual Incongruity: F1: 77.0%
- Vocal Event Detection: 38.0% (WESR-Bench)
- Sincerity Detection: 82.1%
- Memory Efficiency: 6x compression (3-bit KV Cache)

## Hardware Constraints
- Apple Mac M2 with 8GB RAM
- Peak memory target: < 5GB during training
- MLX + QLoRA (4-bit quantization)
- TurboQuant KV cache compression

## Tasks

### 1. Project Initialization and Research Governance
1.1 Define research scope, hypotheses, and success thresholds
1.2 Create TaskMaster project structure and initial task registry
1.3 Configure reproducible environment for 8GB Mac M2
1.4 Set experiment logging and artifact versioning

### 2. Data Acquisition, Licensing, and Ingestion
2.1 Acquire StandUp4AI and ingest word-level labels (3,617 videos, 130K+ labels)
2.2 Acquire TIC-TALK and parse kinematic signals (5,400+ segments)
2.3 Acquire UR-FUNNY, MERIP, PESD, BP4D+, and SMILE datasets
2.4 Implement exclusion policy for MHD and Big Bang Theory
2.5 Build unified multimodal ingestion pipeline

### 3. Multimodal Label Harmonization and Split Design
3.1 Define laughter taxonomy (Duchenne vs Non-Duchenne + auxiliaries)
3.2 Align word-level, acoustic, visual, and FACS timelines
3.3 Map BP4D+ AU6/AU12 to sincerity/spontaneity signals
3.4 Create stratified cross-dataset splits

### 4. Hardware Optimization and Memory-Constrained Training Stack
4.1 Profile baseline memory and throughput on MLX
4.2 Integrate QLoRA 4-bit weight compression in MLX
4.3 Integrate TurboQuant 3-bit KV cache compression (~6x reduction)
4.4 Implement memory guardrails and auto-batch scaling
4.5 Verify peak memory target under full training load (< 5GB)

### 5. Evolutionary and Biosemiotic Laughter Modeling
5.1 Formalize Duchenne vs Non-Duchenne mechanistic feature set
5.2 Implement airflow dynamics modeling
5.3 Simulate neural control pathways (brainstem/limbic vs speech motor)
5.4 Encode phylogenetic priors for hominin phonic sociality

### 6. Statistical Dynamics and Symmetric Expansion Engine
6.1 Implement additomultiplicative cascade detector
6.2 Quantify multiplicative dominance for Duchenne laughter
6.3 Quantify additive stabilization for Non-Duchenne laughter
6.4 Build symmetric expansion scaling profiler

### 7. MLSA Hypothesis Module (V, K, D)
7.1 Implement Violation Delta (V) via ESR deviation
7.2 Implement Knowledge Alignment (K) via Common Knowledge Graph
7.3 Implement Social Distance (D) estimator
7.4 Implement laughter probability head P(laugh)=σ(αV+βK-γD)
7.5 Calibrate MLSA outputs across datasets

### 8. GCACU Cognitive Architecture Integration
8.1 Implement Gated Contrast-Attention for incongruity monitoring
8.2 Implement Theory of Mind (ToM) state modeling
8.3 Integrate HitEmotion framework components
8.4 Implement Transfer Entropy speaker-audience handshake
8.5 Validate integrated GCACU behavior on held-out scenarios

### 9. Autoresearch Loop and Distribution-Aware Training Automation
9.1 Build Codex-driven hypothesis generation templates
9.2 Automate MLX + TurboQuant compile/train/eval pipeline
9.3 Integrate UPL (Uncertainty-Aware Pseudo-Labeling)
9.4 Add benchmark-aware objective scheduling
9.5 Implement loop safety constraints and rollback

### 10. Benchmark Validation, Ablations, and Final Delivery
10.1 Run full benchmark suite and verify target thresholds
10.2 Run component ablations (MLSA, GCACU, evolutionary, statistical)
10.3 Validate memory and compression claims on 8GB Mac M2
10.4 Produce reproducibility package and TaskMaster completion updates

## Key Components
- GCACU: Gated Contrast-Attention Contextualized-Understanding
- ToM: Theory of Mind for mental state modeling
- MLSA: Multi-Layered Social Alignment hypothesis
- UPL: Uncertainty-Aware Pseudo-Labeling
- TurboQuant: 3-bit KV cache compression (QJL + PolarQuant)

## Excluded per User Request
- MHD (Big Bang Theory) dataset - excluded from training
