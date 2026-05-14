#!/usr/bin/env python3
"""
Generate synthetic word-level comedy data with laughter labels.
Analyzes existing data to learn distributions, then generates realistic synthetic examples.
"""

import json
import random
import numpy as np
from collections import Counter
from pathlib import Path


# Comedy type templates with word patterns
COMEDY_TEMPLATES = {
    "observational": {
        "setup_words": [
            "you", "know", "what", "i", "hate", "when", "people", "always", "never", "why",
            "have", "you", "ever", "noticed", "they", "we", "its", "like", "just", "so",
            "but", "thing", "stuff", "is", "that", "this", "really", "actually", "basically"
        ],
        "punchline_words": [
            "same", "thing", "every", "time", "all", "the", "time", "right", "guys", "literally",
            "honestly", "thats", "thats", "the", "worst", "perfect", "exactly", "true", "fact",
            "sad", "funny", "crazy", "ridiculous", "insane", "outrageous", "absurd", "typical"
        ],
        "context_words": [
            "i", "was", "at", "the", "store", "yesterday", "last", "week", "my", "friend",
            "went", "to", "and", "then", "but", "so", "anyway", "finally", "suddenly"
        ]
    },
    "one_liner": {
        "setup_words": [
            "what", "do", "you", "call", "why", "how", "i", "tried", "to", "tell",
            "my", "friend", "said", "heard", "the", "best", "worst", "funniest"
        ],
        "punchline_words": [
            "nothing", "everything", "something", "idk", "nvm", "tbh", "lol", "lmao",
            "dead", "gone", "done", "over", "it", "him", "her", "us", "them", "now"
        ],
        "context_words": [
            "and", "so", "but", "then", "right", "exactly", "basically", "literally"
        ]
    },
    "story_based": {
        "setup_words": [
            "so", "one", "time", "i", "was", "this", "guy", "girl", "there", "here",
            "when", "all", "suddenly", "anyway", "finally", "the", "end", "story"
        ],
        "punchline_words": [
            "died", "cried", "laughed", "walked", "left", "right", "straight", "home",
            "crazy", "insane", "wild", "nuts", "epic", "legendary", "historic", "gone"
        ],
        "context_words": [
            "i", "me", "my", "we", "us", "they", "them", "he", "she", "the", "a", "an",
            "and", "but", "or", "so", "then", "because", "when", "if", "although"
        ]
    },
    "political_social": {
        "setup_words": [
            "politicians", "government", "society", "people", "everyone", "nobody",
            "they", "we", "the", "this", "that", "system", "world", "country", "country"
        ],
        "punchline_words": [
            "same", "old", "new", "different", "worse", "better", "insane", "crazy",
            "ridiculous", "absurd", "typical", "pathetic", "tragic", "comical", "sad"
        ],
        "context_words": [
            "its", "like", "just", "really", "actually", "basically", "honestly",
            "truth", "fact", "point", "issue", "problem", "situation", "case"
        ]
    },
    "self_deprecating": {
        "setup_words": [
            "i", "my", "me", "myself", "im", "am", "was", "always", "never", "sometimes",
            "usually", "probably", "definitely", "certainly", "maybe", "perhaps"
        ],
        "punchline_words": [
            "pathetic", "terrible", "awful", "horrible", "miserable", "hopeless",
            "useless", "worthless", "disaster", "wreck", "mess", "fool", "idiot", "loser"
        ],
        "context_words": [
            "but", "though", "however", "still", "yet", "at", "least", "least", "i",
            "even", "also", "as", "well", "than", "more", "less", "too", "very"
        ]
    }
}

LAUGHTER_TYPES = [
    "discrete",
    "continuous", 
    "high_density_laughter",
    "neutral_delivery",
    "joyful_context",
    "marked_laughter"
]

TOM_INTENT_LABELS = [
    "humor_expression",
    "playful_banter",
    "reactive_amusement",
    "sarcastic_commentary"
]


class SyntheticComedyGenerator:
    def __init__(self, source_file=None, seed=42):
        random.seed(seed)
        np.random.seed(seed)
        
        # Learn distributions from source data if provided
        self.word_count_mean = 16
        self.word_count_std = 6
        self.word_count_min = 6
        self.word_count_max = 35
        
        # Biosemotic feature ranges (learned from data)
        self.duchenne_joy_range = (0.0, 0.613)
        self.duchenne_genuine_range = (0.216, 0.728)
        self.incongruity_range = (0.116, 0.915)
        
        # Laughter label distribution
        self.laughter_density_possible = True  # Some examples have high laughter density
        self.zero_laughter_prob = 0.35  # ~35% have no laughter
        
        # Track all words seen for vocabulary
        self.vocabulary = self._build_vocabulary()
        
    def _build_vocabulary(self):
        """Build vocabulary from comedy word patterns."""
        vocab = set()
        for comedy_type in COMEDY_TEMPLATES.values():
            vocab.update(comedy_type["setup_words"])
            vocab.update(comedy_type["punchline_words"])
            vocab.update(comedy_type["context_words"])
        
        # Add common English words for filler
        common_words = [
            "i", "the", "a", "an", "and", "or", "but", "if", "then", "so", "to", "of",
            "in", "on", "at", "by", "for", "with", "from", "as", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "can", "this", "that", "these", "those",
            "it", "he", "she", "they", "we", "you", "my", "your", "his", "her", "its", "our",
            "their", "what", "which", "who", "whom", "when", "where", "why", "how",
            "all", "each", "every", "both", "few", "more", "most", "other", "some", "any",
            "no", "not", "only", "own", "same", "than", "too", "very", "just", "also",
            "now", "here", "there", "then", "always", "never", "sometimes", "often", "usually",
            "really", "very", "quite", "pretty", "actually", "basically", "literally", "honestly",
            "exactly", "especially", "finally", "suddenly", " slowly", " quickly", "finally"
        ]
        vocab.update(common_words)
        return vocab
    
    def _sample_word_count(self):
        """Sample word count from observed distribution."""
        # Heavy集中在15词左右
        count = int(np.random.normal(self.word_count_mean, self.word_count_std))
        return max(self.word_count_min, min(self.word_count_max, count))
    
    def _generate_word_sequence(self, num_words, comedy_type=None):
        """Generate realistic word sequence for comedy."""
        if comedy_type is None:
            comedy_type = random.choice(list(COMEDY_TEMPLATES.keys()))
        
        template = COMEDY_TEMPLATES[comedy_type]
        words = []
        
        # Decide structure: setup + punchline
        if num_words < 8:
            # Short joke: mostly punchline
            punchline_start = random.randint(0, max(0, num_words - 4))
            punchline_len = random.randint(2, min(5, num_words - punchline_start))
        elif num_words < 15:
            # Medium joke: ~60% setup
            punchline_start = int(num_words * 0.6)
        else:
            # Long joke: ~50-70% setup  
            punchline_start = int(num_words * random.uniform(0.5, 0.7))
        
        # Generate setup words
        for i in range(punchline_start):
            if i < 3:
                # Start with setup connector
                words.append(random.choice(template["setup_words"][:10]))
            else:
                words.append(random.choice(list(self.vocabulary)))
        
        # Generate punchline words (higher density of laughter labels)
        punchline_len = num_words - punchline_start
        for i in range(punchline_len):
            if i < punchline_len // 2:
                words.append(random.choice(template["punchline_words"]))
            else:
                words.append(random.choice(list(self.vocabulary)))
        
        return words[:num_words]
    
    def _generate_labels(self, words, comedy_type=None):
        """
        Generate laughter labels. Punchline words get label=1.
        Returns labels list aligned with words.
        """
        num_words = len(words)
        labels = [0] * num_words
        
        # Determine punchline region (last 20-50% of words)
        punchline_start = int(num_words * random.uniform(0.5, 0.8))
        
        # Laughter density depends on comedy type
        if comedy_type == "one_liner":
            # One-liners: punchline is dense laughter
            for i in range(punchline_start, num_words):
                labels[i] = 1
        elif comedy_type == "observational":
            # Observational: punchline + some setup
            labels[punchline_start] = 1  # Key punchline word
            for i in range(punchline_start + 1, num_words):
                if random.random() < 0.7:
                    labels[i] = 1
        elif comedy_type == "story_based":
            # Story: laughter near end climax
            for i in range(punchline_start, num_words):
                if random.random() < 0.6:
                    labels[i] = 1
        elif comedy_type == "self_deprecating":
            # Self-deprecating: moderate density
            for i in range(punchline_start, num_words):
                if random.random() < 0.5:
                    labels[i] = 1
        else:
            # Default: punchline region gets laughter
            for i in range(punchline_start, num_words):
                labels[i] = 1
        
        # Handle edge case: no laughter if randomly selected
        if random.random() < self.zero_laughter_prob:
            labels = [0] * num_words
        
        return labels
    
    def _generate_biosemiotics(self, labels, comedy_type=None):
        """Generate biosemotic features based on label distribution."""
        laughter_count = sum(labels)
        laughter_ratio = laughter_count / len(labels) if labels else 0
        
        # Duchenne joy: higher when more laughter words
        base_joy = random.uniform(*self.duchenne_joy_range)
        if laughter_ratio > 0.5:
            duchenne_joy = base_joy * random.uniform(1.5, 2.5)
        elif laughter_ratio > 0.2:
            duchenne_joy = base_joy * random.uniform(1.0, 1.5)
        else:
            duchenne_joy = base_joy * random.uniform(0.5, 1.0)
        duchenne_joy = min(0.9, max(0.0, duchenne_joy))
        
        # Duchenne genuine humor: moderate correlation with laughter
        duchenne_genuine = random.uniform(*self.duchenne_genuine_range)
        if laughter_ratio > 0:
            duchenne_genuine = min(0.9, duchenne_genuine * random.uniform(1.1, 1.3))
        
        # Incongruity: varies by comedy type
        base_incongruity = random.uniform(*self.incongruity_range)
        if comedy_type in ["one_liner", "observational"]:
            incongruity = base_incongruity * random.uniform(1.2, 1.6)
        elif comedy_type == "story_based":
            incongruity = base_incongruity * random.uniform(0.9, 1.2)
        else:
            incongruity = base_incongruity
        incongruity = min(0.95, max(0.05, incongruity))
        
        return {
            "duchenne_joy_intensity": round(duchenne_joy, 4),
            "duchenne_genuine_humor_probability": round(duchenne_genuine, 4),
            "incongruity_expectation_violation_score": round(incongruity, 4)
        }
    
    def _get_laughter_type(self, labels, comedy_type=None):
        """Determine laughter type based on label distribution."""
        laughter_count = sum(labels)
        laughter_ratio = laughter_count / len(labels) if labels else 0
        
        if laughter_ratio == 0:
            return "neutral_delivery"
        elif laughter_ratio > 0.7:
            return "high_density_laughter"
        elif laughter_ratio > 0.3:
            return "discrete"
        else:
            return random.choice(["continuous", "joyful_context", "marked_laughter"])
    
    def _get_tom_label(self, labels, comedy_type=None):
        """Get theory of mind intent label."""
        if sum(labels) == 0:
            return random.choice(TOM_INTENT_LABELS[:1] + [TOM_INTENT_LABELS[-1]])
        elif comedy_type == "self_deprecating":
            return "reactive_amusement"
        elif comedy_type == "observational":
            return "playful_banter"
        else:
            return random.choice(TOM_INTENT_LABELS)
    
    def generate_example(self, example_id=None, comedy_type=None):
        """Generate a single synthetic comedy example."""
        if example_id is None:
            example_id = f"synthetic_{random.randint(100000, 999999)}"
        
        if comedy_type is None:
            comedy_type = random.choice(list(COMEDY_TEMPLATES.keys()))
        
        # Generate structure
        num_words = self._sample_word_count()
        words = self._generate_word_sequence(num_words, comedy_type)
        labels = self._generate_labels(words, comedy_type)
        biosemiotics = self._generate_biosemiotics(labels, comedy_type)
        
        return {
            "example_id": example_id,
            "words": words,
            "labels": labels,
            "laughter_type": self._get_laughter_type(labels, comedy_type),
            **biosemiotics,
            "tom_speaker_intent_label": self._get_tom_label(labels, comedy_type),
            "metadata": {
                "source": "synthetic",
                "comedy_type": comedy_type,
                "generated": True
            }
        }
    
    def generate_dataset(self, num_examples, output_path=None, comedy_type_weights=None):
        """Generate a dataset of synthetic comedy examples."""
        if comedy_type_weights is None:
            comedy_type_weights = {
                "observational": 0.30,
                "one_liner": 0.20,
                "story_based": 0.20,
                "political_social": 0.15,
                "self_deprecating": 0.15
            }
        
        examples = []
        comedy_types = list(comedy_type_weights.keys())
        weights = list(comedy_type_weights.values())
        
        for i in range(num_examples):
            comedy_type = random.choices(comedy_types, weights=weights)[0]
            example_id = f"synthetic_{i:05d}"
            example = self.generate_example(example_id, comedy_type)
            examples.append(example)
            
            if (i + 1) % 1000 == 0:
                print(f"Generated {i + 1}/{num_examples} examples...")
        
        # Write to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                for example in examples:
                    f.write(json.dumps(example) + '\n')
            print(f"Saved {num_examples} examples to {output_path}")
        
        return examples


def analyze_source_data(source_path):
    """Analyze existing data to learn distributions."""
    print(f"Analyzing source data from {source_path}...")
    
    word_counts = []
    laughter_ratios = []
    duchenne_joy = []
    duchenne_genuine = []
    incongruity = []
    comedy_types = []
    tom_labels = []
    
    with open(source_path) as f:
        for line in f:
            d = json.loads(line)
            words = d.get('words', [])
            labels = d.get('labels', [])
            
            word_counts.append(len(words))
            if labels:
                laughter_ratios.append(sum(labels) / len(labels))
            
            duchenne_joy.append(d.get('duchenne_joy_intensity', 0))
            duchenne_genuine.append(d.get('duchenne_genuine_humor_probability', 0))
            incongruity.append(d.get('incongruity_expectation_violation_score', 0))
            comedy_types.append(d.get('laughter_type', 'unknown'))
            tom_labels.append(d.get('tom_speaker_intent_label', 'unknown'))
    
    print(f"\n=== Source Data Analysis ===")
    print(f"Total examples: {len(word_counts)}")
    print(f"Word count: mean={np.mean(word_counts):.1f}, median={np.median(word_counts):.1f}")
    print(f"Laughter ratio: mean={np.mean(laughter_ratios):.3f}, median={np.median(laughter_ratios):.3f}")
    print(f"Duchenne joy: [{min(duchenne_joy):.3f}, {max(duchenne_joy):.3f}], mean={np.mean(duchenne_joy):.3f}")
    print(f"Duchenne genuine: [{min(duchenne_genuine):.3f}, {max(duchenne_genuine):.3f}], mean={np.mean(duchenne_genuine):.3f}")
    print(f"Incongruity: [{min(incongruity):.3f}, {max(incongruity):.3f}], mean={np.mean(incongruity):.3f}")
    print(f"Laughter types: {Counter(comedy_types).most_common(5)}")
    print(f"TOM labels: {set(tom_labels)}")
    
    return {
        "word_count_mean": np.mean(word_counts),
        "word_count_std": np.std(word_counts),
        "duchenne_joy_range": (min(duchenne_joy), max(duchenne_joy)),
        "duchenne_genuine_range": (min(duchenne_genuine), max(duchenne_genuine)),
        "incongruity_range": (min(incongruity), max(incongruity)),
        "laughter_types": list(set(comedy_types)),
        "tom_labels": list(set(tom_labels))
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic comedy data")
    parser.add_argument("--source", default="/Users/Subho/run_42_transfer_minimal/data/train_merged.jsonl",
                        help="Source data file to analyze")
    parser.add_argument("--output", default="training/synthetic_comedy_data.jsonl",
                        help="Output file path")
    parser.add_argument("--num-examples", type=int, default=8500,
                        help="Number of synthetic examples to generate")
    parser.add_argument("--target-total", type=int, default=10000,
                        help="Target total examples (generates num-examples to reach this)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze source data")
    args = parser.parse_args()
    
    # Analyze source data
    stats = analyze_source_data(args.source)
    
    if args.analyze_only:
        return
    
    # Check existing count
    source_count = 0
    try:
        with open(args.source) as f:
            source_count = sum(1 for _ in f)
        print(f"\nSource file has {source_count} examples")
    except:
        pass
    
    # Calculate how many to generate
    target = args.target_total
    current = source_count
    to_generate = max(0, target - current)
    
    if to_generate > 0:
        print(f"\nGenerating {to_generate} synthetic examples to reach {target} total...")
        
        generator = SyntheticComedyGenerator(seed=args.seed)
        
        # Override ranges with learned values
        generator.duchenne_joy_range = stats['duchenne_joy_range']
        generator.duchenne_genuine_range = stats['duchenne_genuine_range']
        generator.incongruity_range = stats['incongruity_range']
        
        output_path = Path(args.output)
        examples = generator.generate_dataset(to_generate, output_path)
        
        print(f"\nGeneration complete!")
        print(f"Output: {output_path}")
    else:
        print(f"\nAlready have {current} examples, target is {target}. No generation needed.")


if __name__ == "__main__":
    main()
