#!/usr/bin/env python3
"""
Convert Hindi (and other) transcripts to expanded_10k format.

Converts Whisper transcript JSON to JSONL format matching expanded_10k structure.
"""
import json
import os
import random
from pathlib import Path
from typing import List, Dict, Any


def extract_words_from_segments(segments: List[Dict]) -> List[str]:
    """Extract words from Whisper segments."""
    words = []
    for segment in segments:
        for word_info in segment.get('words', []):
            word = word_info.get('word', '').strip()
            if word:
                # Remove leading/trailing spaces
                words.append(word)
    return words


def generate_biosemotic_features(words: List[str], language: str) -> Dict[str, Any]:
    """Generate placeholder biosemotic features.

    Note: These should be refined using the teacher model later.
    For now, generate reasonable placeholders.
    """
    num_words = len(words)

    # Generate random but reasonable values
    return {
        'duchenne_joy_intensity': [random.uniform(0.0, 0.3) for _ in range(num_words)],
        'duchenne_genuine_humor_probability': [random.uniform(0.0, 0.3) for _ in range(num_words)],
        'duchenne_spontaneous_laughter_markers': [0.0 for _ in range(num_words)],
        'duchenne_setup_punchline_structure': ['setup'] * num_words,
        'incongruity_expectation_violation_score': [random.uniform(0.1, 0.4) for _ in range(num_words)],
        'incongruity_humor_complexity_score': [random.uniform(0.1, 0.4) for _ in range(num_words)],
        'incongruity_resolution_time': [random.uniform(0.1, 0.5) for _ in range(num_words)],
        'tom_speaker_intent_label': ['informative'] * num_words,
        'tom_speaker_intent_confidence': [random.uniform(0.5, 0.9) for _ in range(num_words)],
        'tom_audience_perspective_score': [random.uniform(0.3, 0.7) for _ in range(num_words)],
        'tom_social_context_humor_score': [random.uniform(0.2, 0.5) for _ in range(num_words)],
        'tom_character_interaction_pattern': ['monologue'] * num_words,
        'tom_character_interaction_score': [0.0 for _ in range(num_words)]
    }


def convert_transcript_to_training_format(
    transcript_path: str,
    example_id_base: str,
    comedian_id: str = "unknown",
    show_id: str = "unknown"
) -> List[Dict[str, Any]]:
    """Convert a single transcript to training format.

    Splits long transcripts into multiple examples (max 50 words each).
    """
    with open(transcript_path) as f:
        data = json.load(f)

    language = data.get('language', 'unknown')
    segments = data.get('segments', [])

    # Extract all words
    all_words = extract_words_from_segments(segments)

    if not all_words:
        return []

    # Split into chunks of max 50 words
    max_words = 50
    examples = []

    for i in range(0, len(all_words), max_words):
        chunk_words = all_words[i:i + max_words]

        # Create example
        example = {
            'example_id': f"{example_id_base}_{i // max_words}",
            'language': language,
            'comedian_id': comedian_id,
            'show_id': show_id,
            'words': chunk_words,
            'labels': [0] * len(chunk_words),  # All 0 (no laughter) - needs refinement
            'label': 0,  # Overall label (0 = no laughter)
            'is_sentence_level': False,
            'metadata': {
                'source': 'youtube_whisper',
                'video_id': data.get('metadata', {}).get('video_id', 'unknown'),
                'timestamp': data.get('metadata', {}).get('timestamp', 'unknown')
            }
        }

        # Add biosemotic features
        biosemotic = generate_biosemotic_features(chunk_words, language)
        example.update(biosemotic)

        examples.append(example)

    return examples


def process_all_hindi_transcripts(
    input_dir: str,
    output_dir: str
) -> Dict[str, int]:
    """Process all Hindi transcripts and save to output directory."""

    os.makedirs(output_dir, exist_ok=True)

    # Find all transcript files
    transcript_files = list(Path(input_dir).glob('*_transcript.json'))

    print(f"Found {len(transcript_files)} transcript files")

    all_examples = {
        'train': [],
        'valid': [],
        'test': []
    }

    for i, transcript_path in enumerate(transcript_files):
        print(f"Processing {transcript_path.name}...")

        # Extract comedian name from filename
        video_id = transcript_path.stem.replace('_transcript', '')
        comedian_id = "vir_das"  # All current are Vir Das

        # Convert to training format
        examples = convert_transcript_to_training_format(
            str(transcript_path),
            example_id_base=f"indian_{video_id}",
            comedian_id=comedian_id
        )

        # Split into train/valid/test (80/10/10)
        random.shuffle(examples)
        n = len(examples)
        train_end = int(0.8 * n)
        valid_end = int(0.9 * n)

        all_examples['train'].extend(examples[:train_end])
        all_examples['valid'].extend(examples[train_end:valid_end])
        all_examples['test'].extend(examples[valid_end:])

        print(f"  - Generated {len(examples)} examples")
        print(f"  - Total words: {sum(len(ex['words']) for ex in examples)}")

    # Save to files
    stats = {}
    for split, examples in all_examples.items():
        output_path = os.path.join(output_dir, f'{split}.jsonl')

        # Load existing examples if file exists
        existing_examples = []
        if os.path.exists(output_path):
            with open(output_path) as f:
                existing_examples = [json.loads(line) for line in f]

        # Append new examples
        all_split_examples = existing_examples + examples

        # Save
        with open(output_path, 'w') as f:
            for ex in all_split_examples:
                f.write(json.dumps(ex) + '\n')

        stats[split] = len(all_split_examples)
        print(f"\n{split}: {len(all_split_examples)} total examples")

    return stats


def main():
    """Main function."""
    # Paths
    input_dir = '/Users/Subho/autonomous_laughter_prediction_essential/data/audio_comedy/transcripts/unknown'
    output_dir = '/Users/Subho/autonomous_laughter_prediction_essential/data/indian_comedy_processed'

    print("=" * 60)
    print("Processing Hindi transcripts to training format")
    print("=" * 60)

    stats = process_all_hindi_transcripts(input_dir, output_dir)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for split, count in stats.items():
        print(f"{split}: {count} examples")
    print("=" * 60)

    # Count total words
    total_words = 0
    for split in ['train', 'valid', 'test']:
        path = os.path.join(output_dir, f'{split}.jsonl')
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    ex = json.loads(line)
                    total_words += len(ex.get('words', []))

    print(f"Total words: {total_words}")
    print("=" * 60)


if __name__ == '__main__':
    main()
