"""
OpenAI models management module.

This module handles fetching and categorizing OpenAI models from the API,
filtering out deprecated models and organizing them by type.
"""

import re
from datetime import datetime
from typing import TypedDict

import openai

from src.config import OPENAI_API_KEY


# Configure OpenAI client
openai.api_key = OPENAI_API_KEY


class ModelInfo(TypedDict):
	created: str
	id: str
	is_reasoning: bool
	name: str
	year: int


async def get_openai_models() -> dict[str, list[ModelInfo]]:
	"""
	Fetch and categorize available OpenAI models.

	Filters out deprecated models and organizes remaining models into categories:
	- chat: Text generation and conversation models
	- embedding: Text embedding models
	- thinking: Reasoning models (o1, o3, o4 series)

	Prioritizes models from 2025 based on their creation date.

	:return: Dictionary with categorized model lists
	:raises Exception: If OpenAI API call fails
	"""
	try:
		# Fetch models from OpenAI API
		client = openai.OpenAI(api_key=OPENAI_API_KEY)
		response = client.models.list()

		# Initialize categorized model lists
		categorized_models: dict[str, list[ModelInfo]] = {
			'chat': [],
			'embedding': [],
			'thinking': [],
			'special': []
		}

		for model in response.data:
			model_id = model.id
			model_created = datetime.fromtimestamp(model.created)

			# Skip deprecated models and focus on 2025+ models
			if _is_deprecated_model(model_id) or model_created.year < 2024:
				continue

			# Create model info object
			model_info: ModelInfo = {
				'created': model_created.isoformat(),
				'id': model_id,
				'is_reasoning': _is_thinking_model(model_id),
				'name': _get_display_name(model_id),
				'year': model_created.year
			}

			# Categorize models
			if _is_special_model(model_id):
				categorized_models['special'].append(model_info)
			elif _is_thinking_model(model_id):
				categorized_models['thinking'].append(model_info)
			elif _is_embedding_model(model_id):
				categorized_models['embedding'].append(model_info)
			elif _is_chat_model(model_id):
				categorized_models['chat'].append(model_info)

		# Sort each category by creation date (newest first) and prioritize 2025 models
		for category in categorized_models:
			categorized_models[category].sort(
				key=lambda x: (x['year'], x['created']),
				reverse=True
			)

		return categorized_models

	except Exception as e:
		raise Exception(f'Failed to fetch models from OpenAI API: {str(e)}')


def _is_deprecated_model(model_id: str) -> bool:
	"""
	Check if a model is deprecated based on known deprecated model patterns.

	Based on Azure OpenAI deprecation schedules and OpenAI announcements.

	:param model_id: The model identifier
	:return: True if the model is deprecated
	"""
	deprecated_patterns = [
		# Legacy GPT-3.5 versions
		'gpt-3.5-turbo',
		# Legacy GPT-4 versions
		'gpt-4-0314',
		'gpt-4-0613',
		'gpt-4-32k',
		'gpt-4-turbo',
		'gpt-4.5-preview', # This model was a preview and is being replaced by GPT-4.1
		# Old text completion models
		'text-davinci',
		'text-curie',
		'text-babbage',
		'text-ada',
		'davinci',
		'curie',
		'babbage',
		'ada',
		'code-davinci',
		'code-cushman',
		# Instruct models
		'gpt-3.5-turbo-instruct',
		# Preview models with explicit retirement dates
		'gpt-4o-audio-preview', # Retiring September 2025
		'gpt-4o-realtime-preview', # Retiring September 2025
		'o1-preview',  # Retiring July 2025
		'o1-mini', # Retiring October 2025
		# Generic previews if not explicitly handled by special models
		'-preview', # Catch all for other preview models not explicitly listed
	]

	# Check for exact matches or pattern matches
	model_lower = model_id.lower()
	for pattern in deprecated_patterns:
		if pattern in model_lower:
			return True

	# Special case for text-embedding-ada-002 as it's being replaced
	if 'text-embedding-ada-002' in model_lower:
		return True

	# Filter out models with date suffixes (e.g., -2025-04-14, _2025_04_14)
	# This regex matches a dash or underscore followed by YYYY, MM, DD
	if re.search(r'[-_]\d{4}[-_]\d{2}[-_]\d{2}$', model_id):
		return True

	return False


def _is_special_model(model_id: str) -> bool:
	"""
	Check if a model is a special model (audio, image, video, etc.).

	:param model_id: The model identifier
	:return: True if the model is a special model
	"""
	special_patterns = [
		'whisper',
		'tts-1',
		'tts-1-hd',
		'gpt-4o-mini-realtime-preview',
		'gpt-4o-transcribe',
		'gpt-4o-mini-tts',
		'gpt-4o-mini-transcribe',
		'gpt-image-1',
		'dall-e',
		'sora',
		'gpt-4o-search-preview',
		'gpt-4o-mini-search-preview',
		# Models not working with API
		'chatgpt-4o-latest',
  		'gpt-5-chat-latest',
	]
	model_lower = model_id.lower()
	return any(pattern in model_lower for pattern in special_patterns)


def _is_thinking_model(model_id: str) -> bool:
	"""
	Check if a model is a reasoning/thinking model.

	:param model_id: The model identifier
	:return: True if the model is a thinking model
	"""
	thinking_patterns = ['o1', 'o3', 'o4', 'deep-research', 'gpt-5']
	# Ensure it's not also an embedding or special model
	return any(pattern in model_id.lower() for pattern in thinking_patterns) and \
		not _is_embedding_model(model_id) and \
		not _is_special_model(model_id)


def _is_embedding_model(model_id: str) -> bool:
	"""
	Check if a model is an embedding model.

	:param model_id: The model identifier
	:return: True if the model is an embedding model
	"""
	embedding_patterns = ['embedding', 'embed']
	return any(pattern in model_id.lower() for pattern in embedding_patterns) and not _is_special_model(model_id)


def _is_chat_model(model_id: str) -> bool:
	"""
	Check if a model is a chat/text generation model.

	:param model_id: The model identifier
	:return: True if the model is a chat model
	"""
	chat_patterns = ['gpt', 'turbo', 'chat', 'llama', 'qwen', 'claude', 'gemini', 'mixtral', 'command']
	# Exclude models that are explicitly embedding, thinking, or special models.
	return any(pattern in model_id.lower() for pattern in chat_patterns) and \
		not _is_embedding_model(model_id) and \
		not _is_thinking_model(model_id) and \
		not _is_special_model(model_id)


def _get_display_name(model_id: str) -> str:
	"""
	Generate a human-readable display name for a model.

	:param model_id: The model identifier
	:return: Human-readable model name
	"""
	# Map common model IDs to friendly names
	name_mappings = {
		# GPT-5 family
		'gpt-5': 'GPT-5',
		'gpt-5-2025-08-07': 'GPT-5',
		'gpt-5-mini': 'GPT-5 Mini',
		'gpt-5-mini-2025-08-07': 'GPT-5 Mini',
		'gpt-5-nano': 'GPT-5 Nano',
		'gpt-5-nano-2025-08-07': 'GPT-5 Nano',
		# GPT-4 family
		'gpt-4.1': 'GPT-4.1',
		'gpt-4.1-2025-04-14': 'GPT-4.1',
		'gpt-4.1-mini': 'GPT-4.1 Mini',
		'gpt-4.1-mini-2025-04-14': 'GPT-4.1 Mini',
		'gpt-4.1-nano': 'GPT-4.1 Nano',
		'gpt-4.1-nano-2025-04-14': 'GPT-4.1 Nano',
		'gpt-4o': 'GPT-4o',
		'gpt-4o-2024-08-06': 'GPT-4o',
		'gpt-4o-mini': 'GPT-4o Mini',
		'gpt-4o-mini-2024-07-18': 'GPT-4o Mini',
		'gpt-4o-mini-search-preview': 'GPT-4o Mini Search Preview',
		'gpt-4o-mini-search-preview-2025-03-11': 'GPT-4o Mini Search Preview',
		'gpt-4o-search-preview': 'GPT-4o Search Preview',
		'gpt-4o-search-preview-2025-03-11': 'GPT-4o Search Preview',
		# GPT-3.5 family
		'gpt-3.5-turbo': 'GPT-3.5 Turbo',
		# Embedding models
		'text-embedding-3-large': 'Text Embedding 3 Large',
		'text-embedding-3-small': 'Text Embedding 3 Small',
		# Reasoning models
		'o1': 'o1',
		'o1-2024-12-17': 'o1',
		'o1-pro': 'o1 Pro',
		'o1-pro-2025-03-19': 'o1 Pro',
		'o3': 'o3',
		'o3-2025-04-16': 'o3',
		'o3-deep-research': 'o3 Deep Research',
		'o3-deep-research-2025-06-26': 'o3 Deep Research',
		'o3-mini': 'o3 Mini',
		'o3-mini-2025-01-31': 'o3 Mini',
		'o3-pro': 'o3 Pro',
		'o3-pro-2025-06-10': 'o3 Pro',
		'o4-mini': 'o4 Mini',
		'o4-mini-2025-04-16': 'o4 Mini',
		'o4-mini-deep-research': 'o4 Mini Deep Research',
		'o4-mini-deep-research-2025-06-26': 'o4 Mini Deep Research',
		# Codex models
		'codex-mini-latest': 'Codex Mini Latest',
		# Image models
		'gpt-image-1': 'GPT Image 1',
		# Computer use preview
		'computer-use-preview': 'Computer Use Preview',
		'computer-use-preview-2025-03-11': 'Computer Use Preview',
	}

	if model_id in name_mappings:
		return name_mappings[model_id]

	# Convert kebab-case to title case
	return model_id.replace('-', ' ').title()
