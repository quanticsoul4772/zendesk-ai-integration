"""
Configuration Manager

This module provides configuration management functionality.
"""

import json
import os
from typing import Any, Dict, Optional

from src.domain.interfaces.utility_interfaces import ConfigManager


class EnvironmentConfigManager(ConfigManager):
    """
    Configuration manager that uses environment variables.

    Environment variables are read with optional prefixes and fallbacks to default values.
    """

    def __init__(self, prefix: str = "", default_values: Optional[Dict[str, Any]] = None):
        """
        Initialize the configuration manager.

        Args:
            prefix: Prefix for environment variables
            default_values: Optional dictionary with default values
        """
        self.prefix = prefix
        self.config = default_values or {}

        # Load environment variables
        self._load_from_env()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value

    def load(self, filepath: str) -> bool:
        """
        Load configuration from a JSON file.

        Args:
            filepath: Path to configuration file

        Returns:
            Success indicator
        """
        try:
            if not os.path.exists(filepath):
                return False

            with open(filepath, 'r') as f:
                loaded_config = json.load(f)

            # Update configuration with loaded values
            self.config.update(loaded_config)
            return True
        except Exception as e:
            print(f"Error loading configuration from {filepath}: {e}")
            return False

    def save(self, filepath: str) -> bool:
        """
        Save configuration to a JSON file.

        Args:
            filepath: Path to save configuration to

        Returns:
            Success indicator
        """
        try:
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(filepath, 'w') as f:
                json.dump(self.config, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving configuration to {filepath}: {e}")
            return False

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary with all configuration values
        """
        return self.config.copy()

    def _load_from_env(self) -> None:
        """Load configuration values from environment variables."""
        for env_key, env_value in os.environ.items():
            # Check if the environment variable starts with the prefix
            if self.prefix and not env_key.startswith(self.prefix):
                continue

            # Remove prefix to get the actual configuration key
            config_key = env_key[len(self.prefix):] if self.prefix else env_key

            # Convert to lower case for case-insensitive lookups
            config_key = config_key.lower()

            # Try to parse as JSON for complex values
            try:
                value = json.loads(env_value)
            except json.JSONDecodeError:
                value = env_value

            self.config[config_key] = value


class JsonFileConfigManager(ConfigManager):
    """Configuration manager that uses a JSON file."""

    def __init__(self, filepath: Optional[str] = None, default_values: Optional[Dict[str, Any]] = None):
        """
        Initialize the configuration manager.

        Args:
            filepath: Path to configuration file
            default_values: Optional dictionary with default values
        """
        self.filepath = filepath
        self.config = default_values or {}

        # Load configuration from file if provided
        if filepath and os.path.exists(filepath):
            self.load(filepath)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value

        # Auto-save if filepath is set
        if self.filepath:
            self.save(self.filepath)

    def load(self, filepath: str) -> bool:
        """
        Load configuration from a JSON file.

        Args:
            filepath: Path to configuration file

        Returns:
            Success indicator
        """
        try:
            if not os.path.exists(filepath):
                return False

            with open(filepath, 'r') as f:
                loaded_config = json.load(f)

            # Update configuration with loaded values
            self.config.update(loaded_config)

            # Update filepath
            self.filepath = filepath

            return True
        except Exception as e:
            print(f"Error loading configuration from {filepath}: {e}")
            return False

    def save(self, filepath: Optional[str] = None) -> bool:
        """
        Save configuration to a JSON file.

        Args:
            filepath: Path to save configuration to (defaults to initialized filepath)

        Returns:
            Success indicator
        """
        try:
            save_path = filepath or self.filepath

            if not save_path:
                return False

            directory = os.path.dirname(save_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(save_path, 'w') as f:
                json.dump(self.config, f, indent=2)

            # Update filepath if new path provided
            if filepath:
                self.filepath = filepath

            return True
        except Exception as e:
            print(f"Error saving configuration to {filepath or self.filepath}: {e}")
            return False

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary with all configuration values
        """
        return self.config.copy()
