"""
Session Memory Manager for Algo Trading Project
Stores and retrieves session context, progress, and insights
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List

class SessionMemory:
    def __init__(self, memory_file: str = "session_memory.json"):
        self.memory_file = memory_file
        self.data = self.load_memory()
    
    def load_memory(self) -> Dict[str, Any]:
        """Load memory from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading memory: {e}")
                return self._create_default_memory()
        return self._create_default_memory()
    
    def save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            print(f"✓ Memory saved to {self.memory_file}")
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def update_progress(self, task: str, status: str = "completed"):
        """Update task progress"""
        if status == "completed":
            if task not in self.data["progress"]["completed_tasks"]:
                self.data["progress"]["completed_tasks"].append(task)
        
        self.data["progress"]["current_task"] = task
        self.data["session_info"]["last_updated"] = datetime.now().isoformat()
        self.save_memory()
    
    def add_insight(self, category: str, insight: str):
        """Add a new insight"""
        if category not in self.data["key_insights"]:
            self.data["key_insights"][category] = []
        
        if insight not in self.data["key_insights"][category]:
            self.data["key_insights"][category].append(insight)
        
        self.save_memory()
    
    def get_current_context(self) -> str:
        """Get formatted current context"""
        context = f"""
=== ALGO TRADING SESSION CONTEXT ===
Project: {self.data['session_info']['project_name']}
Last Updated: {self.data['session_info']['last_updated']}
Current Phase: {self.data['session_info']['current_phase']}

COMPLETED TASKS:
{chr(10).join('✓ ' + task for task in self.data['progress']['completed_tasks'])}

CURRENT TASK: {self.data['progress']['current_task']}

NEXT TASKS:
{chr(10).join('• ' + task for task in self.data['progress']['next_tasks'])}

CONFIGURATION:
• Broker: {self.data['configuration']['broker']}
• Session Token: {self.data['configuration']['session_token']}
• Symbols: {', '.join(self.data['configuration']['symbols'])}
• WebSocket: {'Enabled' if self.data['configuration']['websocket_enabled'] else 'Disabled'}

KEY FILES:
{chr(10).join('• ' + file for file in self.data['file_structure']['main_files'])}
=========================================
"""
        return context
    
    def _create_default_memory(self) -> Dict[str, Any]:
        """Create default memory structure"""
        return {
            "session_info": {
                "last_updated": datetime.now().isoformat(),
                "project_name": "ICICI Breeze Algo Trading Dashboard",
                "current_phase": "Initial Setup"
            },
            "progress": {
                "completed_tasks": [],
                "current_task": "Setting up session memory",
                "next_tasks": []
            },
            "configuration": {},
            "file_structure": {"main_files": [], "data_files": []},
            "key_insights": {},
            "websocket_requirements": {}
        }

# Usage example
if __name__ == "__main__":
    memory = SessionMemory()
    print(memory.get_current_context())