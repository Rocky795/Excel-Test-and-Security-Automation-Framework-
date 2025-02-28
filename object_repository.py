# File: object_repository.py
import json
import os
import re
from typing import Dict, Any, Union


class ObjectRepository:
    def __init__(self, repo_file: str):
        """Initialize object repository with repository file path"""
        self.repo_file = repo_file
        self.objects = self._load_repository()

    def _load_repository(self) -> Dict[str, Any]:
        """Load object repository from JSON file"""
        if not os.path.exists(self.repo_file):
            raise FileNotFoundError(f"Object repository file not found: {self.repo_file}")

        try:
            with open(self.repo_file, 'r') as file:
                repository = json.load(file)
                print(f"Successfully loaded {len(repository)} objects from repository")
                return repository
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in repository file: {self.repo_file}")
        except Exception as e:
            raise Exception(f"Error loading object repository: {e}")

    def get_object_locator(self, object_name: str) -> str:
        """Get locator for the specified object"""
        # Try exact match first
        if object_name in self.objects:
            return self.objects[object_name]

        # Try case-insensitive match
        object_lower = object_name.lower()
        for key, value in self.objects.items():
            if key.lower() == object_lower:
                return value

        # Try partial match (object name contains the key)
        for key, value in self.objects.items():
            if key.lower() in object_lower or object_lower in key.lower():
                print(f"Warning: Using partial match for '{object_name}' -> '{key}'")
                return value

        raise ValueError(f"Object '{object_name}' not found in repository")

    def add_object(self, object_name: str, locator: str) -> None:
        """Add or update an object in the repository"""
        self.objects[object_name] = locator

        # Save to file
        with open(self.repo_file, 'w') as file:
            json.dump(self.objects, file, indent=4)

        print(f"Added/updated object '{object_name}' in repository")

