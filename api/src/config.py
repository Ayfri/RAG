"""
Global configuration settings for the RAG API, loaded from environment variables.

This module handles the loading and validation of essential environment variables,
providing a centralized access point for API configuration.
"""

import os

import dotenv


# Load environment variables from .env file
found_dotenv = dotenv.load_dotenv()

# Ensure .env file is found
if not found_dotenv:
	raise FileNotFoundError("No '.env' file found. Please create one with necessary environment variables.")


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
		raise ValueError(f"Environment variable '{name}' not found. Please set it in your .env file.")

	return value or ""


OPENAI_API_KEY = get_var("OPENAI_API_KEY")
