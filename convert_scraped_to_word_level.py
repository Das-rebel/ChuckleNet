#!/usr/bin/env python3
"""
Convert scraped comedy transcripts (JSON format) to word-level JSONL training format.

Input: data/raw/scraped_comedy_transcripts.json
- 139 transcripts with inline [laughter] tags in content

Output schema matches existing standup_word_level format:
{
  "example_id": "scraped_neal_brennan_crazy_good_seg_000",
  "language": "en",
  "comedian_id": "scraped_neal_brennan_crazy_good",
  "show_id": "scraped_neal_brennan_crazy_good",
  "words": [...],
  "labels": [...],
  "metadata": {
    "source_url": "...",
    "title": "...",
    "segment_index": 0,
    "next_laughter_tag": "[laughter]",
    "laughter_type": "continuous",
    "conversion_mode": "inline_tag_heuristic"
  }
}
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


LAUGHTER_PATTERN = re.compile(r"\[.*?(?:laugh|laughter|chuckle|giggle|cheer).*?\]", re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*|['-][A-Za-z0-9]+|[^\w\s]")
TEXT_NORMALIZATION_TABLE = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201b": "'",
        "\u2032": "'",
        "\u00b4": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }
)


def normalize_text(text: str) -> str:
    return text.translate(TEXT_NORMALIZATION_TABLE)


def tokenize_text(text: str) -> List[str]:
    return TOKEN_PATTERN.findall(normalize_text(text))


def is_punctuation_token(token: str) -> bool:
    return bool(token) and all(not char.isalnum() for char in token)


def extract_last_non_empty_clause_tokens(context_words: List[str]) -> List[str]:
    clause_tokens: List[List[str]] = [[]]
    for token in context_words:
        if is_punctuation_token(token):
            clause_tokens.append([])
            continue
        clause_tokens[-1].append(token)
    non_empty = [clause for clause in clause_tokens if clause]
    return list(non_empty[-1]) if non_empty else []


def apply_context_token_policy(
    context_words: List[str],
    policy: str,
    context_tail_tokens: int,
) -> List[str]:
    if policy == "full":
        return list(context_words)
    if policy == "lexical_tail":
        lexical_words = [word for word in context_words if not is_punctuation_token(word)]
    elif policy == "clause_lexical_tail":
        lexical_words = extract_last_non_empty_clause_tokens(context_words)
    else:
        raise ValueError(f"Unsupported context token policy: {policy}")
    if context_tail_tokens <= 0:
        return []
    return lexical_words[-context_tail_tokens:]


def parse_transcript_content(content: str) -> List[Tuple[str, Optional[str]]]:
    """
    Parse transcript content and extract segments with their following laughter tags.
    Returns list of (segment_text, next_laughter_tag) tuples.
    """
    segments = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines and non-speech lines (stage directions, music cues)
        if not line:
            i += 1
            continue

        # Check if this line is a laughter/music/cheering tag (skip it as a segment)
        if LAUGHTER_PATTERN.match(line):
            i += 1
            continue

        # Check if line has speaker annotation like [Neal] or [Artist]
        # Remove speaker tags for processing
        cleaned_line = re.sub(r'^\[.*?\]\s*', '', line)

        if not cleaned_line.strip():
            i += 1
            continue

        # Look ahead for laughter tag
        next_laughter_tag = None
        for j in range(i + 1, min(i + 3, len(lines))):
            next_line = lines[j].strip()
            if LAUGHTER_PATTERN.match(next_line):
                next_laughter_tag = next_line
                break
            # Stop if we hit another speech line
            if next_line and not LAUGHTER_PATTERN.match(next_line):
                break

        segments.append((cleaned_line, next_laughter_tag))
        i += 1

    return segments


def get_laughter_type(tag: Optional[str]) -> str:
    """Classify laughter type based on tag content."""
    if not tag:
        return "unknown"
    tag_lower = tag.lower()
    if "chuckle" in tag_lower:
        return "discrete"
    if "cheer" in tag_lower:
        return "applause"
    if "continuous" in tag_lower or "laughs" in tag_lower:
        return "continuous"
    return "discrete"


def create_example(
    transcript_id: str,
    segment_index: int,
    words: List[str],
    labels: List[int],
    next_laughter_tag: Optional[str],
    metadata: Dict,
) -> Dict:
    """Create a single training example."""
    return {
        "example_id": f"scraped_{transcript_id}_seg_{segment_index:04d}",
        "language": "en",
        "comedian_id": f"scraped_{transcript_id}",
        "show_id": f"scraped_{transcript_id}",
        "words": words,
        "labels": labels,
        "metadata": {
            "segment_index": segment_index,
            "next_laughter_tag": next_laughter_tag,
            "laughter_type": get_laughter_type(next_laughter_tag),
            "conversion_mode": "inline_tag_heuristic_scraped",
            "context_token_policy": "clause_lexical_tail",
            "context_tail_tokens": 6,
            **metadata
        }
    }


def compute_split_key(transcript_id: str, num_splits: int = 10) -> int:
    """Deterministic split assignment based on transcript ID."""
    hash_val = int(hashlib.md5(transcript_id.encode()).hexdigest(), 16)
    return hash_val % num_splits


def convert_scraped_data(
    scraped_path: Path,
    output_dir: Path,
    context_tail_tokens: int = 6,
    min_words: int = 3,
    valid_ratio: float = 0.1,
    test_ratio: float = 0.1,
) -> Tuple[int, int, int]:
    """Convert scraped transcripts to word-level JSONL."""

    # Load scraped data
    with open(scraped_path, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)

    print(f"Loaded {len(scraped_data)} scraped transcripts")

    # Track all examples for each split
    train_examples = []
    valid_examples = []
    test_examples = []

    for transcript in scraped_data:
        url = transcript.get('url', '')
        title = transcript.get('title', '')
        content = transcript.get('content', '')
        laughter_count = transcript.get('laughter_count', 0)

        # Create transcript ID from URL
        transcript_id = re.sub(r'https?://', '', url).replace('/', '_').replace('-', '_')
        transcript_id = re.sub(r'[^a-zA-Z0-9_]', '', transcript_id)
        transcript_id = transcript_id[-50:]  # Limit length

        # Parse segments
        segments = parse_transcript_content(content)

        # Process segments in order, maintaining context
        context_words = []

        for seg_idx, (segment_text, next_laughter_tag) in enumerate(segments):
            current_words = tokenize_text(segment_text)

            if len(current_words) < min_words:
                context_words = []
                continue

            # Apply context policy
            context = apply_context_token_policy(
                context_words,
                policy="clause_lexical_tail",
                context_tail_tokens=context_tail_tokens
            )

            words = context + current_words
            labels = [0] * len(words)

            # Mark last word as positive if followed by laughter
            if next_laughter_tag and current_words:
                labels[-1] = 1

            example = create_example(
                transcript_id=transcript_id,
                segment_index=seg_idx,
                words=words,
                labels=labels,
                next_laughter_tag=next_laughter_tag,
                metadata={
                    "source_url": url,
                    "title": title,
                    "source_laughter_count": laughter_count,
                }
            )

            # Assign to split based on transcript ID (ensures no overlap)
            split_key = compute_split_key(transcript_id, 100)
            if split_key < int(test_ratio * 100):
                test_examples.append(example)
            elif split_key < int((test_ratio + valid_ratio) * 100):
                valid_examples.append(example)
            else:
                train_examples.append(example)

            # Update context
            context_words = current_words

    # Write outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    train_path = output_dir / "train.jsonl"
    valid_path = output_dir / "valid.jsonl"
    test_path = output_dir / "test.jsonl"

    for path, examples in [(train_path, train_examples), (valid_path, valid_examples), (test_path, test_examples)]:
        with open(path, 'w', encoding='utf-8') as f:
            for ex in examples:
                f.write(json.dumps(ex, ensure_ascii=False) + '\n')

    train_count = len(train_examples)
    valid_count = len(valid_examples)
    test_count = len(test_examples)

    print(f"\nConversion complete:")
    print(f"  Train: {train_count} examples")
    print(f"  Valid: {valid_count} examples")
    print(f"  Test:  {test_count} examples")
    print(f"  Total: {train_count + valid_count + test_count} examples")

    # Count positive examples
    train_pos = sum(1 for ex in train_examples if 1 in ex['labels'])
    valid_pos = sum(1 for ex in valid_examples if 1 in ex['labels'])
    test_pos = sum(1 for ex in test_examples if 1 in ex['labels'])
    print(f"\nPositive examples (before laughter):")
    print(f"  Train: {train_pos}")
    print(f"  Valid: {valid_pos}")
    print(f"  Test:  {test_pos}")

    return train_count, valid_count, test_count


def main():
    parser = argparse.ArgumentParser(description="Convert scraped transcripts to word-level JSONL.")
    parser.add_argument(
        "--scraped-path",
        type=Path,
        default=Path("/Users/Subho/autonomous_laughter_prediction/data/raw/scraped_comedy_transcripts.json"),
        help="Path to scraped transcripts JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/Users/Subho/autonomous_laughter_prediction/data/training/standup_word_level_large"),
        help="Output directory for train/valid/test JSONL files.",
    )
    parser.add_argument(
        "--context-tail-tokens",
        type=int,
        default=6,
        help="Number of lexical context tokens to prepend.",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=3,
        help="Minimum words per segment.",
    )
    parser.add_argument(
        "--valid-ratio",
        type=float,
        default=0.1,
        help="Validation split ratio.",
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.1,
        help="Test split ratio.",
    )
    args = parser.parse_args()

    convert_scraped_data(
        scraped_path=args.scraped_path,
        output_dir=args.output_dir,
        context_tail_tokens=args.context_tail_tokens,
        min_words=args.min_words,
        valid_ratio=args.valid_ratio,
        test_ratio=args.test_ratio,
    )


if __name__ == "__main__":
    main()