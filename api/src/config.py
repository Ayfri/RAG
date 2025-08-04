"""
Global configuration settings for the RAG API, loaded from environment variables.

This module handles the loading and validation of essential environment variables,
providing a centralized access point for API configuration.
"""

import os

import dotenv


# Load environment variables from .env file (optional)
found_dotenv = dotenv.load_dotenv()

# Note: .env file is optional in Docker environment
# Environment variables can be set via docker-compose.yml


def get_var(name: str, default: str | None = None, /, optional: bool = False) -> str:
	"""
	Retrieve an environment variable by name.

	:param name: The name of the environment variable.
	:param default: Default value if the variable is not found. Defaults to None.
	:param optional: If True, returns an empty string if the variable is not found and no default is provided.
	:return: The value of the environment variable.
	:raises ValueError: If the environment variable is not found and not optional, and no default is provided.
	"""
	value = os.getenv(name, default)

	if value is None and not optional:
		raise ValueError(f"Environment variable '{name}' not found. Please set it in your .env file or via docker-compose.yml environment variables.")

	return value or ""


OPENAI_API_KEY = get_var("OPENAI_API_KEY")
