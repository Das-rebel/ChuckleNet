#!/usr/bin/env python3
"""
Expand dataset from 1,890 to 10,000 records.

Sources:
1. Existing run_42 data (1,890 records) - loaded as-is
2. HuggingFace CreativeLang/ColBERT_Humor_Detection (200K labeled) - convert to word-level format
3. Synthetic generation using run_42 word lists, label patterns, biosemotic distributions
4. Augmentation of existing examples (word substitution, shuffle, structure variation)

Output: data/expanded_10k/{train,valid,test}.jsonl
Target: ~35-40% laughter rate at sentence level, realistic biosemotic features.
"""

import json
import random
import statistics
import os
import re
from pathlib import Path
from typing import Any

# Paths
WD = Path("/Users/Subho/autonomous_laughter_prediction_essential")
RUN42 = Path("/Users/Subho/run_42_transfer_minimal/data")
OUT_DIR = WD / "data" / "expanded_10k"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_TOTAL = 10_000
TARGET_LAUGH_RATE = 0.37  # sentence-level laugh rate
SPLIT_RATIOS = {"train": 0.80, "valid": 0.16, "test": 0.04}

random.seed(42)


# ---------------------------------------------------------------------------
# 1. Load existing run_42 data
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open()]


print("Loading run_42 data...")
run42_train = load_jsonl(RUN42 / "train_merged.jsonl")
run42_valid = load_jsonl(RUN42 / "valid_merged.jsonl")
run42_test = load_jsonl(RUN42 / "test_merged.jsonl")
existing = run42_train + run42_valid + run42_test
print(f"  Loaded {len(existing)} existing records")


# ---------------------------------------------------------------------------
# 2. Analyze existing distributions
# ---------------------------------------------------------------------------

def analyze(arr: list[dict]) -> dict[str, Any]:
    laugh = [r for r in arr if r.get("label", 0) == 1 or any(l == 1 for l in r.get("labels", []))]
    duch = [r["duchenne_joy_intensity"] for r in arr if "duchenne_joy_intensity" in r]
    incon = [r["incongruity_expectation_violation_score"] for r in arr if "incongruity_expectation_violation_score" in r]
    tom_labels = [r.get("tom_speaker_intent_label", "humor_expression") for r in arr]
    wcs = [len(r["words"]) for r in arr]
    langs = [r.get("language", "en") for r in arr]

    return {
        "n": len(arr),
        "laugh_n": len(laugh),
        "laugh_rate": len(laugh) / len(arr),
        "duch_mean": statistics.mean(duch) if duch else 0.14,
        "duch_stdev": statistics.stdev(duch) if len(duch) > 1 else 0.12,
        "duch_min": min(duch) if duch else 0.0,
        "duch_max": max(duch) if duch else 0.61,
        "incon_mean": statistics.mean(incon) if incon else 0.19,
        "incon_stdev": statistics.stdev(incon) if len(incon) > 1 else 0.11,
        "incon_min": min(incon) if incon else 0.10,
        "incon_max": max(incon) if incon else 0.91,
        "wc_mean": statistics.mean(wcs),
        "wc_stdev": statistics.stdev(wcs) if len(wcs) > 1 else 5,
        "wc_min": min(wcs),
        "wc_max": max(wcs),
        "wc_median": statistics.median(wcs),
        "tom_labels": {k: tom_labels.count(k) for k in set(tom_labels)},
        "langs": {k: langs.count(k) for k in set(langs)},
    }


stats = analyze(existing)
print(f"\nExisting stats:")
print(f"  Records: {stats['n']}, Laugh rate: {stats['laugh_rate']:.3f}")
print(f"  Duchenne: mean={stats['duch_mean']:.3f}, stdev={stats['duch_stdev']:.3f}")
print(f"  Incongruity: mean={stats['incon_mean']:.3f}, stdev={stats['incon_stdev']:.3f}")
print(f"  Word count: mean={stats['wc_mean']:.1f}, median={stats['wc_median']:.0f}, range={stats['wc_min']}-{stats['wc_max']}")


# ---------------------------------------------------------------------------
# 3. Collect vocabulary / pattern libraries from existing data
# ---------------------------------------------------------------------------

print("\nBuilding vocabulary libraries...")

all_words_laugh = []  # words that appear in laughter-labeled segments
all_words_no_laugh = []  # words that appear in non-laugh segments
for r in existing:
    ws = r["words"]
    ls = r.get("labels", [])
    has_laugh = any(l == 1 for l in ls)
    for i, w in enumerate(ws):
        w_lower = w.lower()
        if has_laugh:
            all_words_laugh.append(w_lower)
        else:
            all_words_no_laugh.append(w_lower)

# Count frequencies
from collections import Counter
laugh_word_freq = Counter(all_words_laugh)
no_laugh_word_freq = Counter(all_words_no_laugh)

laugh_words_unique = set(all_words_laugh)
no_laugh_words_unique = set(all_words_no_laugh)

# Transition probabilities: word -> (next_word, count)
def build_trans(word_list: list[str]) -> dict[str, Counter]:
    trans = {}
    for i in range(len(word_list) - 1):
        w = word_list[i]
        nxt = word_list[i + 1]
        if w not in trans:
            trans[w] = Counter()
        trans[w][nxt] += 1
    return trans

laugh_trans = build_trans(all_words_laugh)
no_laugh_trans = build_trans(all_words_no_laugh)

print(f"  Unique laugh words: {len(laugh_words_unique)}")
print(f"  Unique no-laugh words: {len(no_laugh_words_unique)}")
print(f"  Laugh transition entries: {len(laugh_trans)}")
print(f"  No-laugh transition entries: {len(no_laugh_trans)}")


# ---------------------------------------------------------------------------
# 4. Try loading HuggingFace dataset
# ---------------------------------------------------------------------------

print("\nAttempting to load HuggingFace CreativeLang/ColBERT_Humor_Detection...")
hf_records = []
try:
    from datasets import load_dataset

    ds = load_dataset("CreativeLang/ColBERT_Humor_Detection", split="train")
    print(f"  HuggingFace dataset loaded: {len(ds)} records")
    print(f"  Columns: {ds.column_names}")
    print(f"  Sample: {ds[0]}")

    # Convert to our word-level format
    for i, row in enumerate(ds):
        text = row.get("text") or row.get("sentence") or row.get("content") or str(row)
        label = row.get("label") or row.get("humor") or row.get("is_humor") or 0

        if not text or not isinstance(text, str):
            continue

        # Tokenize simply
        words = re.findall(r"\b[\w']+\b|[^\w\s]", text)
        if len(words) < 3 or len(words) > 120:
            continue

        # Convert ColBERT label to our binary
        # ColBERT: 1 = humorous, 0 = non-humorous
        is_humor = int(label) == 1

        # Assign word-level labels: for humorous, label ~60% of words (especially punchline)
        # for non-humorous, label ~5% (occasional chuckles)
        if is_humor:
            # Label the last ~40% of words (punchline zone)
            n = len(words)
            punch_start = int(n * 0.6)
            labels = [0] * punch_start + [1] * (n - punch_start)
        else:
            # Label ~5% randomly (false positives / neutral delivery)
            labels = [1 if random.random() < 0.05 else 0 for _ in words]

        # Generate biosemotic features
        duchenne = random.gauss(stats["duch_mean"], stats["duch_stdev"])
        duchenne = max(0.0, min(0.65, duchenne))

        incon = random.gauss(stats["incon_mean"], stats["incon_stdev"])
        incon = max(0.10, min(0.91, incon))

        tom_options = ["humor_expression", "setup", "playful_banter", "other"]
        tom_weights = [0.6, 0.2, 0.1, 0.1]
        tom_label = random.choices(tom_options, weights=tom_weights)[0]

        record = {
            "example_id": f"hf_humor_{i}",
            "language": "en",
            "comedian_id": "hf_ColBERT",
            "show_id": "hf_ColBERT",
            "words": words,
            "labels": labels,
            "duchenne_joy_intensity": round(duchenne, 4),
            "duchenne_genuine_humor_probability": round(duchenne * random.uniform(0.8, 1.2), 4),
            "duchenne_spontaneous_laughter_markers": 0.0,
            "duchenne_setup_punchline_structure": round(random.uniform(0.5, 1.0), 2),
            "incongruity_expectation_violation_score": round(incon, 4),
            "incongruity_humor_complexity_score": round(incon * random.uniform(0.85, 1.15), 4),
            "incongruity_resolution_time": round(random.uniform(0.0, 0.6), 4),
            "tom_speaker_intent_label": tom_label,
            "tom_speaker_intent_confidence": round(random.uniform(0.65, 0.85), 2),
            "tom_audience_perspective_score": round(random.uniform(0.0, 0.7), 4),
            "tom_social_context_humor_score": round(random.uniform(0.0, 0.6), 4),
            "tom_character_interaction_pattern": "monologue",
            "tom_character_interaction_score": 0.87,
            "label": 1 if is_humor else 0,
            "is_sentence_level": True,
            "metadata": {"source": "hf_ColBERT_humor_detection"},
        }
        hf_records.append(record)

    print(f"  Converted {len(hf_records)} records from HuggingFace")

except ImportError:
    print("  datasets package not available, skipping HuggingFace source")
except Exception as e:
    print(f"  HuggingFace load failed: {e}")


# ---------------------------------------------------------------------------
# 5. Synthetic generation
# ---------------------------------------------------------------------------

print("\nGenerating synthetic records...")

# Template patterns observed:
# - "Why do we X in YYYY?" -> laugh at end (punchline question)
# - "There are no beaches..." -> observational setup
# - "How many X does it take to Y?" -> joke setup
# - "My friend was trying to annoy me..." -> story setup
# - Chinese patterns: word tuples with specific semantic patterns

COMMON_STARTS_EN = [
    "Why do we", "How do you", "What does a", "I was at the",
    "My friend was", "Tired of", "I just realized",
    "There are no", "I matched with someone who", "Standing in",
    "Love long walks", "My printer says", "Do you want",
    "gig.", "Okay, it was after", "It appears that",
]

SETUP_TRANSITIONS_EN = [
    "But I", "And then", "So I", "Well,", "Turns out",
    "Apparently,", "The problem is", "The worst part",
]

PUNCHLINE_WORDS_EN = list(laugh_words_unique & {
    "game", "puppy", "wine", "champagne", "box", "leaking", "floor",
    "here", "beaches", "Arizona", "wrong", "right", "joke", "funny",
    "piss", "shit", "wake", "pisser", "shitter", "bonus", "send",
    "play", "toucan", "annoy", "bird", "puns", "nothing", "comes",
})

SYNTH_TOM_LABELS = ["humor_expression", "setup", "playful_banter"]


def make_synth_record(idx: int, is_laugh: bool) -> dict:
    """Generate a synthetic record using run_42 word patterns."""
    wc = max(3, min(97, int(random.gauss(stats["wc_mean"], stats["wc_stdev"]))))

    # Build a sentence using transition probabilities
    if is_laugh:
        # Use laugh vocabulary
        if random.random() < 0.5 and all_words_laugh:
            start = random.choice(all_words_laugh)
        else:
            start = random.choice(COMMON_STARTS_EN)

        words = [start]
        for _ in range(wc - 1):
            last = words[-1].lower()
            if last in laugh_trans and laugh_trans[last]:
                next_options = list(laugh_trans[last].keys())
                next_weights = list(laugh_trans[last].values())
                words.append(random.choices(next_options, weights=next_weights)[0])
            else:
                words.append(random.choice(list(laugh_words_unique)))

        # Label punchline (last ~40%)
        punch_start = int(len(words) * random.uniform(0.55, 0.75))
        labels = [0] * punch_start + [1] * (len(words) - punch_start)

        duchenne = random.gauss(0.20, 0.10)  # slightly higher for laughter
        incon = random.gauss(0.22, 0.09)
        label_val = 1
        tom = "humor_expression" if random.random() < 0.75 else "playful_banter"
    else:
        # Use no-laugh vocabulary
        if random.random() < 0.3 and all_words_no_laugh:
            start = random.choice(all_words_no_laugh)
        else:
            start = random.choice([
                "The", "I", "It", "They", "He", "She", "We",
                "This", "That", "These", "Those",
            ])

        words = [start]
        for _ in range(wc - 1):
            last = words[-1].lower()
            if last in no_laugh_trans and no_laugh_trans[last]:
                next_options = list(no_laugh_trans[last].keys())
                next_weights = list(no_laugh_trans[last].values())
                words.append(random.choices(next_options, weights=next_weights)[0])
            else:
                words.append(random.choice(list(no_laugh_words_unique)))

        # Label ~5% (false positive / neutral delivery)
        labels = [1 if random.random() < 0.05 else 0 for _ in words]

        duchenne = random.gauss(0.06, 0.05)  # lower for no-laugh
        incon = random.gauss(0.16, 0.06)
        label_val = 0
        tom = random.choices(["setup", "other", "humor_expression"], weights=[0.5, 0.3, 0.2])[0]

    duchenne = max(0.0, min(0.65, duchenne))
    incon = max(0.10, min(0.91, incon))

    return {
        "example_id": f"synth_{idx}",
        "language": random.choices(["en", "zh"], weights=[0.73, 0.27])[0],
        "comedian_id": "synthetic",
        "show_id": "synthetic",
        "words": words,
        "labels": labels,
        "duchenne_joy_intensity": round(duchenne, 4),
        "duchenne_genuine_humor_probability": round(duchenne * random.uniform(0.8, 1.2), 4),
        "duchenne_spontaneous_laughter_markers": 0.0,
        "duchenne_setup_punchline_structure": round(random.uniform(0.5, 1.0), 2),
        "incongruity_expectation_violation_score": round(incon, 4),
        "incongruity_humor_complexity_score": round(incon * random.uniform(0.85, 1.15), 4),
        "incongruity_resolution_time": round(random.uniform(0.0, 0.6), 4),
        "tom_speaker_intent_label": tom,
        "tom_speaker_intent_confidence": round(random.uniform(0.65, 0.85), 2),
        "tom_audience_perspective_score": round(random.uniform(0.0, 0.7), 4),
        "tom_social_context_humor_score": round(random.uniform(0.0, 0.5), 4),
        "tom_character_interaction_pattern": "monologue",
        "tom_character_interaction_score": 0.87,
        "label": label_val,
        "is_sentence_level": True,
        "metadata": {"source": "synthetic_generation"},
    }


# ---------------------------------------------------------------------------
# 6. Augmentation of existing records
# ---------------------------------------------------------------------------

print("\nGenerating augmented copies...")

AUGMENTATION_MODES = ["word_substitution", "shuffle_non_laugh", "punchline_shift"]


def augment_record(r: dict, idx: int) -> dict:
    """Create an augmented copy with modified words/labels."""
    words = list(r["words"])
    labels = list(r.get("labels", [0] * len(words)))
    new_words, new_labels = list(words), list(labels)

    mode = random.choice(AUGMENTATION_MODES)

    if mode == "word_substitution" and len(words) > 5:
        # Replace up to 20% of non-laugh words with synonyms from vocabulary
        n_sub = max(1, int(len(words) * 0.15))
        positions = random.sample(range(len(words)), min(n_sub, len(words)))
        for pos in positions:
            if labels[pos] == 0:  # only substitute non-laugh words
                new_words[pos] = random.choice(list(no_laugh_words_unique))

    elif mode == "shuffle_non_laugh" and len(words) > 8:
        # Shuffle contiguous non-laugh chunks
        non_laugh_spans = []
        i = 0
        while i < len(words):
            if labels[i] == 0:
                start = i
                while i < len(words) and labels[i] == 0:
                    i += 1
                non_laugh_spans.append((start, i))
            else:
                i += 1

        if non_laugh_spans:
            span = random.choice(non_laugh_spans)
            span_words = new_words[span[0]:span[1]]
            random.shuffle(span_words)
            new_words[span[0]:span[1]] = span_words

    elif mode == "punchline_shift" and any(l == 1 for l in labels):
        # Move punchline label slightly earlier or later
        laugh_indices = [i for i, l in enumerate(labels) if l == 1]
        if laugh_indices:
            shift = random.choice([-1, 0, 1, 2])
            new_labels = [0] * len(labels)
            for orig_idx in laugh_indices:
                new_idx = max(0, min(len(labels) - 1, orig_idx + shift))
                new_labels[new_idx] = 1

    # Add small noise to biosemotic features
    duchenne = r.get("duchenne_joy_intensity", 0.14)
    duchenne += random.gauss(0.0, 0.02)
    duchenne = max(0.0, min(0.65, duchenne))

    incon = r.get("incongruity_expectation_violation_score", 0.19)
    incon += random.gauss(0.0, 0.02)
    incon = max(0.10, min(0.91, incon))

    return {
        **r,
        "example_id": f"{r['example_id']}_aug{idx}",
        "words": new_words,
        "labels": new_labels,
        "duchenne_joy_intensity": round(duchenne, 4),
        "incongruity_expectation_violation_score": round(incon, 4),
        "metadata": {**r.get("metadata", {}), "augmented": True, "augmentation_mode": mode},
    }


# ---------------------------------------------------------------------------
# 7. Build combined pool and split
# ---------------------------------------------------------------------------

print("\nBuilding combined record pool...")

# Separate existing into laugh and no-laugh for precise math
existing_laugh_recs = [r for r in existing if r.get("label", 0) == 1 or any(l == 1 for l in r.get("labels", []))]
existing_no_laugh_recs = [r for r in existing if r.get("label", 0) == 0 and not any(l == 1 for l in r.get("labels", []))]
existing_laugh = len(existing_laugh_recs)
existing_no_laugh = len(existing_no_laugh_recs)

# Add HuggingFace records (small sample)
HF_SIZE = 500
hf_sample = random.sample(hf_records, min(len(hf_records), HF_SIZE)) if hf_records else []
hf_laugh = sum(1 for r in hf_sample if r.get("label", 0) == 1 or any(l == 1 for l in r.get("labels", [])))
hf_no_laugh = len(hf_sample) - hf_laugh
print(f"  Existing: {existing_laugh} laugh, {existing_no_laugh} no-laugh")
print(f"  HF ({len(hf_sample)}): {hf_laugh} laugh, {hf_no_laugh} no-laugh")

# Precise math: we need final totals of TARGET_LAUGH_RATE*TARGET total laugh
# and (1-TARGET_LAUGH_RATE)*TARGET total no-laugh
target_laugh = int(TARGET_TOTAL * TARGET_LAUGH_RATE)
target_no_laugh = TARGET_TOTAL - target_laugh

# Compute synth needs
synth_needed_laugh = max(0, target_laugh - existing_laugh - hf_laugh)
synth_needed_no_laugh = max(0, target_no_laugh - existing_no_laugh - hf_no_laugh)

# Pool now = all existing + hf_sample
pool = existing_no_laugh_recs + existing_laugh_recs + hf_sample

print(f"  Target: {target_laugh} laugh / {target_no_laugh} no-laugh out of {TARGET_TOTAL}")
print(f"  Synth needed: {synth_needed_laugh} laugh, {synth_needed_no_laugh} no-laugh")
print(f"  Generating synth: {synth_needed_laugh} laugh, {synth_needed_no_laugh} no-laugh (target {TARGET_LAUGH_RATE:.0%})")

synth_records = []
synth_idx = 0

# Generate laugh records
for i in range(synth_needed_laugh):
    synth_records.append(make_synth_record(synth_idx, is_laugh=True))
    synth_idx += 1

# Generate no-laugh records
for i in range(synth_needed_no_laugh):
    synth_records.append(make_synth_record(synth_idx, is_laugh=False))
    synth_idx += 1

pool.extend(synth_records)
print(f"  Generated {len(synth_records)} synthetic records")

synth_records = []
synth_idx = 0

# Generate laugh records
for i in range(synth_needed_laugh):
    synth_records.append(make_synth_record(synth_idx, is_laugh=True))
    synth_idx += 1

# Generate no-laugh records
for i in range(synth_needed_no_laugh):
    synth_records.append(make_synth_record(synth_idx, is_laugh=False))
    synth_idx += 1

pool.extend(synth_records)
print(f"  Generated {len(synth_records)} synthetic records ({synth_needed_laugh} laugh, {synth_needed_no_laugh} no-laugh)")

# Augment existing + HF records (create 2 augmented copies per record, up to limit)
augment_budget = max(0, TARGET_TOTAL - len(pool))
if augment_budget > 0:
    candidates = [r for r in pool if r.get("label", 0) == 1 or any(l == 1 for l in r.get("labels", []))]
    n_aug = min(augment_budget, len(candidates) * 2)
    print(f"  Generating {n_aug} augmented copies...")
    for i in range(n_aug):
        source = candidates[i % len(candidates)]
        pool.append(augment_record(source, i // len(candidates)))

print(f"\nTotal pool size: {len(pool)}")

# Final laugh rate check - use sentence-level label only
final_laugh = sum(1 for r in pool if r.get("label", 0) == 1)
final_no_laugh = len(pool) - final_laugh
print(f"Final laugh: {final_laugh} / no-laugh: {final_no_laugh} = {final_laugh/len(pool)*100:.1f}%")

# Truncate to exactly TARGET_TOTAL with proper rate stratification
if len(pool) > TARGET_TOTAL:
    laugh_pool = [r for r in pool if r.get("label", 0) == 1]
    no_laugh_pool = [r for r in pool if r.get("label", 0) == 0]
    target_laugh_n = int(TARGET_TOTAL * TARGET_LAUGH_RATE)
    target_no_laugh_n = TARGET_TOTAL - target_laugh_n
    print(f"Truncating to {TARGET_TOTAL}: need {target_laugh_n} laugh, {target_no_laugh_n} no-laugh")
    selected_laugh = random.sample(laugh_pool, min(len(laugh_pool), target_laugh_n))
    selected_no_laugh = random.sample(no_laugh_pool, min(len(no_laugh_pool), target_no_laugh_n))
    pool = selected_laugh + selected_no_laugh
    print(f"After truncation: {len(pool)} total, {len(selected_laugh)} laugh ({len(selected_laugh)/len(pool)*100:.1f}%)")

# Shuffle and split
random.shuffle(pool)
n_train = int(len(pool) * SPLIT_RATIOS["train"])
n_valid = int(len(pool) * SPLIT_RATIOS["valid"])
# test gets the rest

split_train = pool[:n_train]
split_valid = pool[n_train:n_train + n_valid]
split_test = pool[n_train + n_valid:]

print(f"\nFinal split: train={len(split_train)}, valid={len(split_valid)}, test={len(split_test)}")

# Verify splits
for name, split in [("train", split_train), ("valid", split_valid), ("test", split_test)]:
    n = len(split)
    laugh = sum(1 for r in split if r.get("label", 0) == 1)
    print(f"  {name}: {n} records, laugh rate: {laugh/n*100:.1f}%")


# ---------------------------------------------------------------------------
# 8. Write output files
# ---------------------------------------------------------------------------

def write_jsonl(records: list[dict], path: Path):
    with path.open("w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


print(f"\nWriting output to {OUT_DIR}...")
write_jsonl(split_train, OUT_DIR / "train.jsonl")
write_jsonl(split_valid, OUT_DIR / "valid.jsonl")
write_jsonl(split_test, OUT_DIR / "test.jsonl")

for name in ["train", "valid", "test"]:
    p = OUT_DIR / f"{name}.jsonl"
    print(f"  {p}: {p.stat().st_size / 1024:.1f} KB")

print("\nDone.")
print(f"\nExpansion summary:")
print(f"  Original: 1,890 records")
print(f"  Expanded: {len(split_train) + len(split_valid) + len(split_test):,} records")
print(f"  Sources: run_42 ({len(existing)}) + HF ({len(hf_sample) if hf_records else 0}) + synth ({len(synth_records)}) + aug ({n_aug if augment_budget > 0 else 0})")
print(f"  Output: {OUT_DIR}")
