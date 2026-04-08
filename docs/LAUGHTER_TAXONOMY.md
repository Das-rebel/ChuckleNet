# Laughter Taxonomy

## Task 26.1: Duchenne vs Non-Duchenne Classification

### Duchenne Laughter

**Neurological Origin**: Brainstem/limbic system activation

**Core Characteristics**:
- **Exhalation-only airflow**: No inhalation during laughter burst - continuous diaphragm-driven expiration
- **Brainstem/limbic neural control**: Involuntary emotional response system
- **Spontaneous**: Genuine emotional response, not volitional
- **Multiplicative cascade**: Each contraction triggers the next via positive feedback loop

**Physiological cascade**:
```
Emotional trigger → Limbic activation → Brainstem burst →
Diaphragmatic contraction → Epiglottal closure → Vocalization
```

**Acoustic features**:
- Longer duration (500ms+)
- Higher intensity
- More variability across bursts
- Unvoiced "hh" segments interspersed with voiced laughter

**Facial expression**: Full Duchenne marker (AU6 + AU12 co-occurrence)

**Examples**:
- Genuine amusement laughter
- Uncontrollable laughter
- Laughter from tickling

### Non-Duchenne Laughter

**Neurological Origin**: Speech motor cortex volitional control

**Core Characteristics**:
- **Controlled sequence airflow**: Deliberate pattern with inhalation phases between bursts
- **Speech motor involvement**: Uses speech planning regions (Broca's area, premotor cortex)
- **Volitional**: Can be started/stopped at will
- **Additive cascade**: Each burst is independently initiated

**Physiological cascade**:
```
Volitional trigger → Motor cortex → Respiratory pattern →
Vocal fold control → Articulatory positioning
```

**Acoustic features**:
- Shorter bursts (200-400ms)
- More regular pattern
- Often "hehe" or "haha" repeated syllables
- Clear inhalation gasps between bursts

**Facial expression**: May lack full Duchenne marker - AU6 or AU12 may appear independently

**Examples**:
- Polite social laughter
- Conversational laughter ("hehe")
- Awkward laughter
- Laughter used as speech marker

### Taxonomy Summary Table

| Feature | Duchenne | Non-Duchenne |
|---------|----------|--------------|
| Airflow | Exhalation-only | Inhalation present |
| Neural control | Brainstem/limbic | Speech motor cortex |
| Initiation | Involuntary/spontaneous | Volitional |
| Cascade pattern | Multiplicative | Additive |
| Duration | Long (500ms+) | Short (200-400ms) |
| AU6+AU12 | Both present | Variable |
| Kinematic signals | Strong (TIC-TALK) | Weak |
| Breathing rhythm | No inhalation during burst | Inhalation between bursts |

---

## Task 26.2: Multimodal Timeline Alignment

### Hybrid Forced Alignment Pipeline

The project implements multimodal timeline alignment via `training/hybrid_forced_alignment.py`:

**Architecture** (WhisperX + MFA hybrid):
1. **WhisperX** (coarse alignment): Voice Activity Detection, broad temporal binning
   - Accuracy: 22.4%
   - Fast processing

2. **Montreal Forced Aligner** (precise alignment): Tight temporal alignment
   - Accuracy: 41.6%
   - Better for laughter segment boundaries

**Combined approach**:
```python
# From hybrid_forced_alignment.py
class HybridForcedAlignment:
    def combine_alignments(self, whisperx_result, mfa_result):
        # WhisperX for VAD and coarse bins
        # MFA for precise timing within bins
```

**Alignment output structure**:
```python
{
    "whisperx_coarse": {...},  # VAD timestamps
    "mfa_precise": {...},      # Word-level timestamps
    "final_alignment": [...]    # Combined timeline
}
```

**Supported modalities**:
- Word-level text alignment
- Acoustic waveform timestamps
- Visual frame synchronization
- FACS action unit timing

**WESR-Bench compliance**: Tracks Discrete vs Continuous laughter alignment

---

## Task 26.3: BP4D+ AU6/AU12 Mapping to Sincerity/Spontaneity

### Action Unit Reference

**AU6** (Cheek Raiser): Orbicularis oculi superior fiber activation
- Correlates with genuine positive affect
- Difficult to produce voluntarily

**AU12** (Lip Corner Puller): Zygomaticus major activation
- Social smile component
- Can be produced voluntarily

### Duchenne Detection Mapping

BP4D+ dataset labels map to sincerity/spontaneity as follows:

| BP4D+ Label | Interpretation | Duchenne Indicator |
|-------------|----------------|-------------------|
| AU6 present | Orbicularis oculi activation | High sincerity |
| AU12 present | Zygomatic activation | Social/contextual |
| AU6+AU12 together | Full Duchenne smile | Spontaneous laughter |
| AU12 only | Partial activation | Non-Duchenne/social |

### Code Reference

From `docs/LAUGHTER_TAXONOMY.md`:
```python
# BP4D+ AU mapping for Duchenne detection
DUCHENNE_MARKERS = ["AU6", "AU12"]  # Both required for Duchenne
```

### Integration Points

- **TIC-TALK dataset**: Kinematic signals (arm spread, trunk lean) correlate with Duchenne intensity
- **StandUp4AI**: Word-level labels distinguish laughter types
- **UR-FUNNY**: Punchline context often triggers Duchenne

---

## Task 26.4: Stratified Cross-Dataset Splits

### Split Manager Implementation

The project implements stratified splits via `benchmarks/utils/split_manager.py`:

**Split Configuration**:
```python
@dataclass
class SplitConfig:
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    speaker_independent: bool = True
    show_independent: bool = True
    stratified: bool = True
    random_seed: int = 42
```

**Split Types**:

1. **Speaker-independent splits**: Samples from same speaker appear in only one split
   - Prevents speaker-specific features from leaking

2. **Show-independent splits**: Samples from same show only in one split
   - Important for comedy datasets with recurring comedians

3. **Stratified splits**: Maintains label distribution across splits
   - Uses `StratifiedShuffleSplit` from sklearn
   - Preserves Duchenne/Non-Duchenne ratio

4. **Cross-domain splits**: Train on one dataset, test on another
   - For generalization testing

**Validation**:
```python
def validate_splits(self, train_indices, val_indices, test_indices) -> bool:
    # Checks for:
    # - No overlap between splits
    # - Proper ratios (within 5% tolerance)
    # - Speaker/show independence if configured
```

**Balancing Criteria**:
- Class balance (Duchenne vs Non-Duchenne)
- Source diversity (multiple comedians/shows per split)
- Speaker isolation (no speaker in multiple splits)

---

## Implementation References

| Component | File |
|-----------|------|
| Laughter taxonomy | `docs/LAUGHTER_TAXONOMY.md` |
| Hybrid alignment | `training/hybrid_forced_alignment.py` |
| Split manager | `benchmarks/utils/split_manager.py` |
| BP4D+ mapping | `docs/LAUGHTER_TAXONOMY.md` |
| WESR taxonomy | `training/wesr_taxonomy_processor.py` |
