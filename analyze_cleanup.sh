#!/bin/bash
# Quick analysis of what can be cleaned up

echo "🔍 STORAGE ANALYSIS - What can be cleaned up?"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Large directories
echo "📁 LARGE DIRECTORIES (>500MB):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
du -sh ~/autonomous_laughter_prediction ~/.* ~/* 2>/dev/null | sort -hr | head -15 | while read size path; do
    name=$(basename "$path")
    case "$name" in
        autonomous_laughter_prediction)
            echo -e "🔴 $name: $size - RECOMMENDED FOR CLOUD (28GB project data)"
            ;;
        ~)
            echo -e "🔴 $name: $size - RECOMMENDED FOR REMOVAL (backup files)"
            ;;
        .android|.npm|.gradle|.pnpm-store)
            echo -e "🟡 $name: $size - CAN BE CACHED AND CLEANED"
            ;;
        Library|.git)
            echo -e "🟢 $name: $size - KEEP (essential system files)"
            ;;
        *)
            echo -e "🔵 $name: $size - BACKUP AND EVALUATE"
            ;;
    esac
done

echo ""
echo "📄 LOOSE FILES IN HOME DIRECTORY:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Python scripts: $(find ~ -maxdepth 1 -name "*.py" -type f | wc -l | xargs)"
echo "Shell scripts: $(find ~ -maxdepth 1 -name "*.sh" -type f | wc -l | xargs)"
echo "Markdown files: $(find ~ -maxdepth 1 -name "*.md" -type f | wc -l | xargs)"
echo "JSON files: $(find ~ -maxdepth 1 -name "*.json" -type f | wc -l | xargs)"
echo "Text files: $(find ~ -maxdepth 1 -name "*.txt" -type f | wc -l | xargs)"
echo "Backup files: $(find ~ -maxdepth 1 -name "*backup*" -o -name "*.old" -o -name "*.bak" | wc -l | xargs)"

echo ""
echo "🗑️  DUPLICATE/REDUNDANT FILES:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
find ~ -maxdepth 1 -name "*backup*" -o -name "*.old" -o -name "*.bak" -o -name "*.duplicate" 2>/dev/null | head -10

echo ""
echo "💾 ESTIMATED SPACE RECOVERY:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "autonomous_laughter_prediction: 28GB → cloud"
echo "~ backup directory: 4.9GB → remove"
echo "Package caches: 5GB → clean"
echo "Temporary files: 1GB → remove"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "📊 TOTAL RECOVERY: ~38GB local storage"
echo ""
echo "🚀 READY TO CLEANUP?"
echo "Run: ./cleanup_and_backup.sh"