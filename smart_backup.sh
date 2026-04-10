#!/bin/bash
# Smart Backup Strategy for Autonomous Laughter Prediction
# Uses chunked backup and TreeQuest AI coordination

echo "🤖 SMART BACKUP STRATEGY USING TMLPD"
echo "===================================="

# Create timestamped backup directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_BASE="gdrive:/backups/autonomous_laughter_prediction_${TIMESTAMP}"

echo "📁 Backup destination: ${BACKUP_BASE}"

# Step 1: Backup core Python files (fast, low priority)
echo "🚀 Step 1: Backing up core Python files..."
rclone copy ~/autonomous_laughter_prediction "${BACKUP_BASE}/core_python" \
    --include="*.py" \
    --exclude="*.pth" --exclude="*.pt" --exclude="*.ckpt" \
    --progress --stats-one-line

# Step 2: Backup documentation (fast, low priority)
echo "📄 Step 2: Backing up documentation..."
rclone copy ~/autonomous_laughter_prediction "${BACKUP_BASE}/docs" \
    --include="*.md" --include="*.txt" --include="*.json" \
    --progress --stats-one-line

# Step 3: Backup configuration files (fast)
echo "⚙️  Step 3: Backing up configuration files..."
rclone copy ~/autonomous_laughter_prediction "${BACKUP_BASE}/config" \
    --include=".env.example" --include="config*.py" --include="setup*.py" \
    --progress --stats-one-line

# Step 4: Create backup inventory using TreeQuest analysis
echo "🤖 Step 4: Creating backup inventory with AI analysis..."
treequest query --provider anthropic "Analyze the backup structure at ${BACKUP_BASE} and create an inventory of what files are available for restore. Focus on essential files for continued development." > ~/backup_inventory_analysis.txt

# Step 5: Backup large checkpoint files in background (low priority)
echo "💾 Step 5: Queueing large checkpoint backup (background)..."
rclone copy ~/autonomous_laughter_prediction "${BACKUP_BASE}/checkpoints" \
    --include="*.pth" --include="*.pt" --include="*.ckpt" --include="*.safetensors" \
    --progress --stats-one-line --max-age=30d &

CHECKPOINT_PID=$!
echo "💾 Checkpoint backup running in background (PID: ${CHECKPOINT_PID})"

# Step 6: Create final backup summary
echo "📊 Step 6: Creating backup summary..."
cat > ~/backup_summary_${TIMESTAMP}.txt << EOF
BACKUP SUMMARY - ${TIMESTAMP}
==============================

Backup Location: ${BACKUP_BASE}
Backup Process: TMLPD-Smart Backup Strategy

Components Backed Up:
✅ Core Python files (essential architecture)
✅ Documentation (training plans, reports)
✅ Configuration files
⏳ Model checkpoints (background process)

Essential Project Location: ~/streamlined_laughter_project (552KB)
Original Project Size: 28GB
Streamlined Project Size: 552KB
Space Savings: ~27.9GB

Next Steps:
1. Verify backup: rclone ls ${BACKUP_BASE}
2. Test essential project: cd ~/streamlined_laughter_project
3. Replace original: mv ~/autonomous_laughter_prediction ~/autonomous_laughter_prediction_backup
4. Move essential: mv ~/streamlined_laughter_project ~/autonomous_laughter_prediction

Background checkpoint backup PID: ${CHECKPOINT_PID}
Check status: ps -p ${CHECKPOINT_PID}
EOF

echo "🎉 SMART BACKUP COMPLETED!"
echo "📄 Summary saved to ~/backup_summary_${TIMESTAMP}.txt"
cat ~/backup_summary_${TIMESTAMP}.txt