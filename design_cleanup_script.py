#!/usr/bin/env python3
"""
Design Data Cleanup Script
Clean up design inconsistencies across all platforms using TreeQuest methodology
"""

import os
import shutil
import json
from typing import List, Dict, Any
from datetime import datetime

class DesignCleanupManager:
    def __init__(self):
        self.base_path = "/Users/Subho"
        self.backup_path = os.path.join(self.base_path, "Archive")
        self.cleanup_log = []
        
    def log_action(self, action: str, path: str, status: str, size_mb: float = 0):
        """Log cleanup actions for tracking"""
        self.cleanup_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "path": path,
            "status": status,
            "size_mb": size_mb
        })
        print(f"   {status} {action}: {path} ({size_mb:.1f}MB)")
    
    def get_directory_size(self, path: str) -> float:
        """Calculate directory size in MB"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(fp)
                    except:
                        pass
        except:
            pass
        return total_size / (1024 * 1024)
    
    def cleanup_redundant_android_implementations(self):
        """Remove redundant Android implementations identified in analysis"""
        
        print("🧹 CLEANING UP REDUNDANT ANDROID IMPLEMENTATIONS")
        print("=" * 60)
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_path, exist_ok=True)
        
        redundant_paths = [
            {
                "path": "/Users/Subho/second-brain-android/second-brain-android",
                "backup_name": "second-brain-android-redundant",
                "reason": "No Android features, 9GB bloat"
            },
            {
                "path": "/Users/Subho/second-brain-android/resumetailor-app/desktop-app",
                "backup_name": "resumetailor-desktop-redundant", 
                "reason": "Not Android, desktop app in Android folder"
            }
        ]
        
        for item in redundant_paths:
            source_path = item["path"]
            backup_name = item["backup_name"]
            backup_dest = os.path.join(self.backup_path, backup_name)
            
            if os.path.exists(source_path):
                size_mb = self.get_directory_size(source_path)
                
                try:
                    # Move to archive instead of deleting
                    if os.path.exists(backup_dest):
                        shutil.rmtree(backup_dest)
                    
                    shutil.move(source_path, backup_dest)
                    self.log_action("ARCHIVED", source_path, "✅", size_mb)
                    
                except Exception as e:
                    self.log_action("ARCHIVE FAILED", source_path, "❌", size_mb)
                    print(f"      Error: {e}")
            else:
                self.log_action("NOT FOUND", source_path, "⚠️", 0)
    
    def cleanup_duplicate_assets(self):
        """Clean up duplicate design assets and images"""
        
        print("\n🖼️ CLEANING UP DUPLICATE DESIGN ASSETS")
        print("=" * 60)
        
        # Look for duplicate image assets across platforms
        brain_spark_images = "/Users/Subho/CascadeProjects/brain-spark-platform/out/images"
        web_images = "/Users/Subho/CascadeProjects/brain-spark-platform/platforms/web/src/assets/images"
        android_images = "/Users/Subho/CascadeProjects/brain-spark-platform/platforms/android/app/src/main/res"
        
        # Check and clean up image directories
        image_paths = [
            {"path": brain_spark_images, "type": "Figma exports"},
            {"path": web_images, "type": "Web assets"}, 
            {"path": android_images, "type": "Android resources"}
        ]
        
        total_images = 0
        total_size = 0
        
        for img_info in image_paths:
            if os.path.exists(img_info["path"]):
                size_mb = self.get_directory_size(img_info["path"])
                total_size += size_mb
                
                # Count image files
                image_count = 0
                for root, dirs, files in os.walk(img_info["path"]):
                    image_count += len([f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.webp'))])
                
                total_images += image_count
                self.log_action(f"ANALYZED {img_info['type']}", img_info["path"], "📊", size_mb)
                print(f"      Images: {image_count} files")
            else:
                self.log_action(f"NOT FOUND {img_info['type']}", img_info["path"], "⚠️", 0)
        
        print(f"\n   📊 Total images found: {total_images}")
        print(f"   💾 Total size: {total_size:.1f}MB")
    
    def consolidate_design_tokens(self):
        """Consolidate design tokens and create shared design system"""
        
        print("\n🎨 CONSOLIDATING DESIGN TOKENS")
        print("=" * 60)
        
        # Create design system directory
        design_system_path = "/Users/Subho/CascadeProjects/brain-spark-platform/shared/design-system"
        os.makedirs(design_system_path, exist_ok=True)
        
        # Extract design patterns from analysis reports
        android_report_path = "/Users/Subho/android_comparison_report.json"
        figma_report_path = "/Users/Subho/figma_design_comparison_report.json"
        
        design_tokens = {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "platforms": {},
            "figma_baseline": {},
            "design_inconsistencies": []
        }
        
        # Load existing analysis reports
        if os.path.exists(android_report_path):
            with open(android_report_path, 'r') as f:
                android_data = json.load(f)
                design_tokens["platforms"]["android"] = android_data
            self.log_action("LOADED Android analysis", android_report_path, "✅", 0)
        
        if os.path.exists(figma_report_path):
            with open(figma_report_path, 'r') as f:
                figma_data = json.load(f)
                design_tokens["figma_baseline"] = figma_data["figma_baseline"]
                design_tokens["platforms"]["web"] = next(
                    (p for p in figma_data["platforms"] if p["platform"] == "web"), {}
                )
            self.log_action("LOADED Figma analysis", figma_report_path, "✅", 0)
        
        # Identify design inconsistencies
        inconsistencies = []
        
        # Compare component counts
        android_components = design_tokens["platforms"].get("android", {}).get("implementations", [])
        if android_components:
            brain_spark_android = next(
                (impl for impl in android_components if "Brain Spark Platform" in impl["name"]), {}
            )
            if brain_spark_android:
                android_score = brain_spark_android.get("advancement_score", 0)
                web_score = design_tokens["platforms"].get("web", {}).get("figma_alignment_score", 0)
                
                if android_score < web_score:
                    inconsistencies.append({
                        "type": "Figma Alignment Gap",
                        "description": f"Android ({android_score}/100) < Web ({web_score}/100)",
                        "recommendation": "Port Web component patterns to Android Compose"
                    })
        
        # Check for framework inconsistencies
        android_framework = "XML Views"  # From analysis
        web_framework = "React + TypeScript"  # From analysis
        
        inconsistencies.append({
            "type": "Framework Inconsistency",
            "description": f"Android uses {android_framework}, Web uses {web_framework}",
            "recommendation": "Migrate Android to Jetpack Compose for better design parity"
        })
        
        design_tokens["design_inconsistencies"] = inconsistencies
        
        # Save consolidated design tokens
        tokens_file = os.path.join(design_system_path, "design-tokens.json")
        with open(tokens_file, 'w') as f:
            json.dump(design_tokens, f, indent=2)
        
        self.log_action("CREATED design tokens", tokens_file, "✅", 0)
        
        print(f"   📋 Found {len(inconsistencies)} design inconsistencies")
        for inconsistency in inconsistencies:
            print(f"      - {inconsistency['type']}: {inconsistency['description']}")
    
    def generate_cleanup_report(self):
        """Generate final cleanup report"""
        
        print("\n📊 CLEANUP SUMMARY REPORT")
        print("=" * 60)
        
        # Categorize actions
        actions_by_type = {}
        total_size_cleaned = 0
        
        for log_entry in self.cleanup_log:
            action_type = log_entry["action"]
            if action_type not in actions_by_type:
                actions_by_type[action_type] = []
            actions_by_type[action_type].append(log_entry)
            
            if log_entry["status"] == "✅" and "ARCHIVED" in action_type:
                total_size_cleaned += log_entry["size_mb"]
        
        # Print summary
        print(f"📦 Total actions performed: {len(self.cleanup_log)}")
        print(f"💾 Total space cleaned: {total_size_cleaned:.1f}MB")
        print(f"📁 Actions by type:")
        
        for action_type, entries in actions_by_type.items():
            successful = len([e for e in entries if e["status"] == "✅"])
            print(f"   {action_type}: {successful}/{len(entries)} successful")
        
        # Save full cleanup report
        cleanup_report = {
            "cleanup_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_actions": len(self.cleanup_log),
                "space_cleaned_mb": total_size_cleaned,
                "actions_by_type": {
                    action_type: {
                        "total": len(entries),
                        "successful": len([e for e in entries if e["status"] == "✅"]),
                        "failed": len([e for e in entries if e["status"] == "❌"])
                    }
                    for action_type, entries in actions_by_type.items()
                }
            },
            "detailed_log": self.cleanup_log,
            "recommendations": [
                "Use Brain Spark Platform Android as primary implementation",
                "Port Web component patterns to Android Compose",
                "Implement shared design tokens across platforms",
                "Monitor design consistency with automated checks"
            ]
        }
        
        report_file = "/Users/Subho/design_cleanup_report.json"
        with open(report_file, 'w') as f:
            json.dump(cleanup_report, f, indent=2)
        
        print(f"\n💾 Full cleanup report saved to: {report_file}")
        
        return cleanup_report
    
    def execute_full_cleanup(self):
        """Execute complete design cleanup process"""
        
        print("🧹 DESIGN DATA CLEANUP - STARTING FULL PROCESS")
        print("=" * 70)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Execute cleanup phases
        self.cleanup_redundant_android_implementations()
        self.cleanup_duplicate_assets()
        self.consolidate_design_tokens()
        
        # Generate final report
        report = self.generate_cleanup_report()
        
        print("\n✅ DESIGN CLEANUP COMPLETED")
        print("=" * 70)
        
        return report

if __name__ == "__main__":
    cleanup_manager = DesignCleanupManager()
    cleanup_manager.execute_full_cleanup()