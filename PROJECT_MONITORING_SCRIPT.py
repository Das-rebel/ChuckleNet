#!/usr/bin/env python3
"""
Second Brain Android Project Monitoring Script
Tracks development progress and updates implementation plan
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
import hashlib

class ProjectMonitor:
    def __init__(self, project_root="/Users/Subho/second-brain-v6/apps/android-native"):
        self.project_root = Path(project_root)
        self.plan_file = Path("/Users/Subho/ANDROID_SECOND_BRAIN_IMPLEMENTATION_PLAN.md")
        self.last_state_file = Path("/Users/Subho/.second_brain_monitor_state.json")

    def get_project_state(self):
        """Analyze current project state and return metrics"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "kotlin_files": [],
            "component_count": 0,
            "activity_count": 0,
            "service_count": 0,
            "repository_count": 0,
            "data_model_count": 0,
            "ui_component_count": 0,
            "new_features": [],
            "file_checksums": {}
        }

        # Scan Kotlin files
        if self.project_root.exists():
            for kt_file in self.project_root.rglob("*.kt"):
                relative_path = str(kt_file.relative_to(self.project_root))
                state["kotlin_files"].append(relative_path)

                # Calculate file checksum for change detection
                with open(kt_file, 'rb') as f:
                    content = f.read()
                    state["file_checksums"][relative_path] = hashlib.md5(content).hexdigest()

                # Categorize files
                with open(kt_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                    if "Activity" in content and "class" in content:
                        state["activity_count"] += 1
                    if "Service" in content and "class" in content:
                        state["service_count"] += 1
                    if "Repository" in content and "class" in content:
                        state["repository_count"] += 1
                    if "@Composable" in content:
                        state["ui_component_count"] += 1
                    if "data class" in content:
                        state["data_model_count"] += 1

        state["component_count"] = len(state["kotlin_files"])
        return state

    def load_last_state(self):
        """Load previous monitoring state"""
        if self.last_state_file.exists():
            with open(self.last_state_file, 'r') as f:
                return json.load(f)
        return None

    def save_current_state(self, state):
        """Save current monitoring state"""
        with open(self.last_state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def detect_changes(self, current_state, last_state):
        """Detect changes between current and last state"""
        if not last_state:
            return {
                "new_files": current_state["kotlin_files"],
                "modified_files": [],
                "deleted_files": [],
                "new_features": self.detect_features(current_state)
            }

        current_files = set(current_state["kotlin_files"])
        last_files = set(last_state.get("kotlin_files", []))

        changes = {
            "new_files": list(current_files - last_files),
            "deleted_files": list(last_files - current_files),
            "modified_files": [],
            "new_features": []
        }

        # Detect modified files
        for file_path in current_files & last_files:
            current_checksum = current_state["file_checksums"].get(file_path)
            last_checksum = last_state.get("file_checksums", {}).get(file_path)
            if current_checksum != last_checksum:
                changes["modified_files"].append(file_path)

        # Detect new features
        changes["new_features"] = self.detect_features(current_state)

        return changes

    def detect_features(self, state):
        """Detect implemented features based on file patterns"""
        features = []

        file_patterns = {
            "Universal Capture": ["UniversalCapture", "CaptureService", "capture"],
            "Bookmark Management": ["Bookmark", "bookmark"],
            "Collection System": ["Collection", "collection"],
            "AI Processing": ["AIService", "ai", "AI"],
            "Search Engine": ["Search", "search"],
            "Twitter Integration": ["Twitter", "twitter", "Tweet"],
            "Review System": ["Review", "review", "Spaced"],
            "Analytics": ["Analytics", "analytics", "tracking"],
            "Offline Support": ["Offline", "offline", "sync"],
            "Knowledge Graph": ["KnowledgeGraph", "graph"],
        }

        for feature, patterns in file_patterns.items():
            for file_path in state["kotlin_files"]:
                if any(pattern in file_path for pattern in patterns):
                    if feature not in features:
                        features.append(feature)

        return features

    def calculate_progress(self, state):
        """Calculate implementation progress percentages"""
        total_required_components = {
            "activities": 10,  # Estimated required activities
            "services": 15,    # Estimated required services
            "repositories": 8, # Estimated required repositories
            "ui_components": 50, # Estimated required UI components
            "data_models": 20   # Estimated required data models
        }

        progress = {}
        progress["activities"] = min(100, (state["activity_count"] / total_required_components["activities"]) * 100)
        progress["services"] = min(100, (state["service_count"] / total_required_components["services"]) * 100)
        progress["repositories"] = min(100, (state["repository_count"] / total_required_components["repositories"]) * 100)
        progress["ui_components"] = min(100, (state["ui_component_count"] / total_required_components["ui_components"]) * 100)
        progress["data_models"] = min(100, (state["data_model_count"] / total_required_components["data_models"]) * 100)

        # Overall progress weighted average
        weights = {
            "activities": 0.2,
            "services": 0.3,
            "repositories": 0.2,
            "ui_components": 0.2,
            "data_models": 0.1
        }

        overall = sum(progress[key] * weights[key] for key in weights.keys())
        progress["overall"] = overall

        return progress

    def update_implementation_plan(self, changes, progress, state):
        """Update the implementation plan with new tasks and progress"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Read current plan
        plan_content = ""
        if self.plan_file.exists():
            with open(self.plan_file, 'r') as f:
                plan_content = f.read()

        # Create progress update section
        progress_update = f"""

## 📊 Latest Progress Update ({timestamp})

### Current Implementation Status:
- **Overall Progress:** {progress['overall']:.1f}%
- **Activities:** {state['activity_count']} implemented ({progress['activities']:.1f}%)
- **Services:** {state['service_count']} implemented ({progress['services']:.1f}%)
- **Repositories:** {state['repository_count']} implemented ({progress['repositories']:.1f}%)
- **UI Components:** {state['ui_component_count']} implemented ({progress['ui_components']:.1f}%)
- **Data Models:** {state['data_model_count']} implemented ({progress['data_models']:.1f}%)

### Recent Changes Detected:
"""

        if changes["new_files"]:
            progress_update += f"#### ✅ New Files Added ({len(changes['new_files'])}):\n"
            for file in changes["new_files"][:10]:  # Limit to 10 most recent
                progress_update += f"- `{file}`\n"
            if len(changes["new_files"]) > 10:
                progress_update += f"- ... and {len(changes['new_files']) - 10} more files\n"
            progress_update += "\n"

        if changes["modified_files"]:
            progress_update += f"#### 🔄 Modified Files ({len(changes['modified_files'])}):\n"
            for file in changes["modified_files"][:10]:
                progress_update += f"- `{file}`\n"
            if len(changes["modified_files"]) > 10:
                progress_update += f"- ... and {len(changes['modified_files']) - 10} more files\n"
            progress_update += "\n"

        if changes["new_features"]:
            progress_update += f"#### 🚀 Features Detected:\n"
            for feature in changes["new_features"]:
                progress_update += f"- {feature}\n"
            progress_update += "\n"

        # Add next priority tasks based on progress
        priority_tasks = self.generate_priority_tasks(progress, state)
        if priority_tasks:
            progress_update += f"#### 🎯 Next Priority Tasks:\n"
            for task in priority_tasks:
                progress_update += f"- {task}\n"
            progress_update += "\n"

        # Insert progress update at the end of the plan
        updated_content = plan_content + progress_update

        # Write updated plan
        with open(self.plan_file, 'w') as f:
            f.write(updated_content)

    def generate_priority_tasks(self, progress, state):
        """Generate priority tasks based on current progress"""
        tasks = []

        # If overall progress is low, focus on foundation
        if progress["overall"] < 20:
            tasks.extend([
                "Complete Universal Capture backend integration",
                "Implement Supabase data layer",
                "Build bookmark repository and basic CRUD operations",
                "Create AI processing service foundation"
            ])
        elif progress["overall"] < 50:
            tasks.extend([
                "Enhance AI content analysis pipeline",
                "Implement semantic search capabilities",
                "Build collection management system",
                "Add real-time sync functionality"
            ])
        elif progress["overall"] < 80:
            tasks.extend([
                "Complete Twitter integration suite",
                "Implement spaced repetition review system",
                "Add knowledge graph visualization",
                "Build workflow automation features"
            ])
        else:
            tasks.extend([
                "Performance optimization and profiling",
                "Comprehensive testing and QA",
                "Accessibility compliance validation",
                "Production deployment preparation"
            ])

        # Add specific missing component tasks
        if state["repository_count"] < 5:
            tasks.append("Implement missing repository classes for data management")

        if state["service_count"] < 8:
            tasks.append("Create additional background services for AI and sync")

        if state["ui_component_count"] < 20:
            tasks.append("Build more UI components for feature completeness")

        return tasks[:8]  # Limit to 8 priority tasks

    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        print(f"🔍 Monitoring Second Brain Android project at {datetime.now()}")

        # Get current state
        current_state = self.get_project_state()
        last_state = self.load_last_state()

        # Detect changes
        changes = self.detect_changes(current_state, last_state)

        # Calculate progress
        progress = self.calculate_progress(current_state)

        # Report findings
        print(f"📊 Overall Progress: {progress['overall']:.1f}%")
        print(f"📁 Total Kotlin files: {len(current_state['kotlin_files'])}")
        print(f"🆕 New files: {len(changes['new_files'])}")
        print(f"🔄 Modified files: {len(changes['modified_files'])}")
        print(f"🚀 Features detected: {', '.join(changes['new_features']) if changes['new_features'] else 'None'}")

        # Update implementation plan if significant changes detected
        if (changes["new_files"] or changes["modified_files"] or
            (last_state and abs(progress["overall"] - last_state.get("last_progress", 0)) > 1)):

            print("📝 Updating implementation plan...")
            self.update_implementation_plan(changes, progress, current_state)
            current_state["last_progress"] = progress["overall"]

        # Save current state
        self.save_current_state(current_state)

        return {
            "state": current_state,
            "changes": changes,
            "progress": progress
        }

def main():
    """Main monitoring function"""
    monitor = ProjectMonitor()

    # Run monitoring cycle
    result = monitor.run_monitoring_cycle()

    # Return summary for external use
    return {
        "overall_progress": result["progress"]["overall"],
        "component_count": result["state"]["component_count"],
        "new_files": len(result["changes"]["new_files"]),
        "features_detected": result["changes"]["new_features"]
    }

if __name__ == "__main__":
    main()