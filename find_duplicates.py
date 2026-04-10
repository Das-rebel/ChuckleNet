import os
import hashlib
from collections import defaultdict

def hash_file(path, block_size=65536):
    hasher = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(block_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        # Silently ignore files that cannot be read (e.g., permission issues)
        # but log to stderr for debugging if needed.
        print(f"Error hashing {path}: {e}")
        return None

def find_duplicates(root_dir):
    hash_dict = defaultdict(list)
    for dirpath, _, filenames in os.walk(root_dir):
        for name in filenames:
            full_path = os.path.join(dirpath, name)
            # Ensure it's a regular file before attempting to hash
            if not os.path.isfile(full_path):
                continue
            file_hash = hash_file(full_path)
            if file_hash:
                hash_dict[file_hash].append(full_path)
    # Print groups with more than one file
    for file_hash, paths in hash_dict.items():
        if len(paths) > 1:
            print(f"Duplicate group (hash={file_hash}):")
            for p in paths:
                print(f"  {p}")
            print()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Find duplicate files by content hash.")
    parser.add_argument("directory", nargs="?", default=os.path.expanduser("~"), help="Root directory to scan (default: home directory)")
    args = parser.parse_args()
    find_duplicates(args.directory)
