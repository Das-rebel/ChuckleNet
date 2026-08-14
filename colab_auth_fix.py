# The fix: Remove the auth cell and use direct file upload
# The notebook already has file upload cells, just skip the auth cell

import json

with open('H6_Prosody_Test_Colab.ipynb', 'r') as f:
    nb = json.load(f)

# Find and remove the auth cell (cell with id "auth")
new_cells = []
for cell in nb['cells']:
    if cell.get('metadata', {}).get('id') == 'auth':
        # Replace with a comment cell
        new_cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {"id": "auth"},
            "outputs": [],
            "source": [
                "# Authentication not needed - using direct file upload\n",
                "# Skip this cell\n",
                "print('Using direct file upload mode (no auth needed)')"
            ]
        })
    else:
        new_cells.append(cell)

nb['cells'] = new_cells

with open('H6_Prosody_Test_Colab.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)

print("Fixed notebook - removed auth cell")

# Also update the gdown cell to be clearer
with open('H6_Prosody_Test_Colab.ipynb', 'r') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    if 'gdown_segments' in str(cell.get('metadata', {}).get('id', '')):
        # Replace with simpler upload instructions
        cell['source'] = [
            "# Upload aligned_segments.jsonl\n",
            "# Option 1: Direct file upload (recommended)\n",
            "from google.colab import files\n",
            "uploaded = files.upload()\n",
            "for fn in uploaded.keys():\n",
            "    print(f'Uploaded: {fn} ({len(uploaded[fn])} bytes)')\n",
            "    # Move to working directory\n",
            "    import shutil\n",
            "    shutil.move(fn, 'aligned_segments.jsonl')"
        ]

with open('H6_Prosody_Test_Colab.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)

print("Updated notebook - fixed gdown cell too")

# Upload fixed version to GDrive
import subprocess
result = subprocess.run(['rclone', 'copy', 'H6_Prosody_Test_Colab.ipynb', 'gdrive:/laughter_prediction_backup/', '-q'], capture_output=True, text=True)
print(f"Uploaded to GDrive: {result.returncode == 0}")
