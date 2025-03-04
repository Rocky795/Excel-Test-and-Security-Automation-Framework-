# File: object_repository.py
import json
import os
import re
import logging
from typing import Dict, Any, Union


class ObjectRepository:
    def __init__(self, repo_file: str,logger=None):
        """Initialize object repository with repository file path"""
        self.repo_file = repo_file
        self.logger = logger or logging.getLogger("SalesforceAutomation")
        self.objects = self._load_repository()

    def _load_repository(self) -> Dict[str, Any]:
        """Load object repository from JSON file"""
        self.logger.info(f"Loading object repository from {self.repo_file}")
        if not os.path.exists(self.repo_file):
            # Create empty repository file if it doesn't exist
            empty_repo = {}
            os.makedirs(os.path.dirname(self.repo_file), exist_ok=True)
            with open(self.repo_file, 'w') as file:
                json.dump(empty_repo, file, indent=4)
            self.logger.info(f"Created new empty repository file: {self.repo_file}")
            return empty_repo

        try:
            with open(self.repo_file, 'r') as file:
                repository = json.load(file)
                self.logger.info(f"Successfully loaded {len(repository)} objects from repository")
                return repository
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON format in repository file: {self.repo_file}")
            raise ValueError(f"Invalid JSON format in repository file: {self.repo_file}")
        except Exception as e:
            self.logger.error(f"Error loading object repository: {str(e)}")
            raise Exception(f"Error loading object repository: {str(e)}")

    def get_object_locator(self, object_name: str, params: Dict[str, str] = None) -> str:
        """
        Get locator for the specified object with parameter substitution
        
        Args:
            object_name: Name of the object to locate
            params: Dictionary of parameters to substitute in the locator
            
        Returns:
            String with the locator value, with parameters substituted if provided
        """
        locator = None
        
        # Try exact match first
        if object_name in self.objects:
            locator = self.objects[object_name]
        else:
            # Try case-insensitive match
            object_lower = object_name.lower()
            for key, value in self.objects.items():
                if key.lower() == object_lower:
                    locator = value
                    self.logger.debug(f"Found case-insensitive match for '{object_name}' -> '{key}'")
                    break
            
            # If still not found, try partial match
            if locator is None:
                for key, value in self.objects.items():
                    if key.lower() in object_lower or object_lower in key.lower():
                        locator = value
                        self.logger.warning(f"Using partial match for '{object_name}' -> '{key}'")
                        break
        
        # If locator is still None, we couldn't find it
        if locator is None:
            self.logger.error(f"Object '{object_name}' not found in repository")
            print(f"Object '{object_name}' not found in repository")
            raise ValueError(f"Object '{object_name}' not found in repository")
            
        # Apply parameter substitution if needed
        if params and '{' in locator:
            try:
                # Apply all parameter substitutions
                for key, value in params.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in locator:
                        locator = locator.replace(placeholder, str(value))
                        print(f"Substituted '{key}' with '{value}' in locator")
                        self.logger.debug(f"Substituted '{key}' with '{value}' in locator")
                
                # Check if any parameters are missing
                if '{' in locator and '}' in locator:
                    missing_params = []
                    import re
                    for param in re.findall(r'\{([^}]+)\}', locator):
                        missing_params.append(param)
                    if missing_params:

                        print(f"Missing parameters in locator: {', '.join(missing_params)}")
                        self.logger.warning(f"Missing parameters in locator: {', '.join(missing_params)}")
            except Exception as e:
                self.logger.error(f"Error during parameter substitution: {str(e)}")
                raise ValueError(f"Error during parameter substitution: {str(e)}")
                
        return locator

    def add_object(self, object_name: str, locator: str) -> None:
        """Add or update an object in the repository"""
        self.objects[object_name] = locator

        # Save to file
        with open(self.repo_file, 'w') as file:
            json.dump(self.objects, file, indent=4)

        self.logger.info(f"Added/updated object '{object_name}' in repository")
        
    def get_all_objects(self) -> Dict[str, str]:
        """Return all objects in the repository"""
        return self.objects.copy()
        
    def remove_object(self, object_name: str) -> bool:
        """Remove an object from the repository if it exists"""
        if object_name in self.objects:
            del self.objects[object_name]
            
            # Save to file
            with open(self.repo_file, 'w') as file:
                json.dump(self.objects, file, indent=4)
                
            self.logger.info(f"Removed object '{object_name}' from repository")
            return True
        else:
            self.logger.warning(f"Cannot remove: Object '{object_name}' not found in repository")
            return False