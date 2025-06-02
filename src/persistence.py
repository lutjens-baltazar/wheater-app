import os
import json
from datetime import datetime
from github import Github
from typing import Dict, Any

class ModelStorage:
    def __init__(self):
        self.github = Github(os.getenv('GITHUB_TOKEN'))
        self.repo = self.github.get_repo(os.getenv('GITHUB_REPOSITORY'))
        self.file_path = 'data/model_stats.json'

    def load_stats(self) -> Dict[str, Any]:
        try:
            file = self.repo.get_contents(self.file_path, ref="main")
            content = json.loads(file.decoded_content.decode())
            return content
        except Exception as e:
            print(f"No existing stats found: {e}")
            return {}

    def save_stats(self, stats: Dict[str, Any]):
        try:
            content = json.dumps(stats, indent=2)
            try:
                # Try to get existing file
                file = self.repo.get_contents(self.file_path, ref="main")
                self.repo.update_file(
                    self.file_path,
                    f"Update model stats {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    content,
                    file.sha
                )
            except Exception:
                # File doesn't exist, create it
                self.repo.create_file(
                    self.file_path,
                    f"Initial model stats {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    content
                )
        except Exception as e:
            print(f"Error saving stats: {e}")