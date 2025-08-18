"""
RAG API router containing all endpoints for managing RAG indices and documents.
"""

import json
from collections.abc import AsyncGenerator
from typing import Any, Literal

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from llama_index.core.base.llms.types import ChatMessage as LLamaIndexChatMessage
from pydantic import BaseModel, Field

from src.openai_models import ModelInfo, get_openai_models
from src.rag import RAGService
from src.rag_config import RAGConfig
from src.types import StreamEvent
from src.logger import get_logger

router = APIRouter(prefix='/rag', tags=['RAG'])
rag_service = RAGService()
log = get_logger(__name__)


class ChatMessage(BaseModel):
	"""
	Represents a single message in the chat history.

	:param role: The role of the message sender ('user' or 'assistant')
	:param content: The content of the message
	"""
	role: Literal['user', 'assistant']
	content: str


class QueryPayload(BaseModel):
	"""
	Request payload for RAG query operations.
	:param query: The question or prompt to send to the RAG system
	:param history: The conversation history
	"""
	query: str
	history: list[ChatMessage] | None = Field(default_factory=list)


class QueryResponse(BaseModel):
	"""
	Response payload for RAG query operations.

	:param content: The answer from the RAG system
	"""
	content: str


class SymlinkPayload(BaseModel):
	"""
	Request payload for creating symbolic links.

	:param target_path: Path to the target file or directory
	:param link_name: Name for the symbolic link
	:param include_patterns: List of include glob patterns (optional)
	:param exclude_patterns: List of exclude glob patterns (optional)
	"""
	target_path: str
	link_name: str
	include_patterns: list[str] | None = Field(default_factory=lambda: ['**/*'])
	exclude_patterns: list[str] | None = Field(default_factory=list)


class FolderPayload(BaseModel):
	"""
	Request payload for creating folders.

	:param type: Type of operation ('folder')
	:param name: Name of the folder to create
	:param include_patterns: List of include glob patterns (optional)
	:param exclude_patterns: List of exclude glob patterns (optional)
	"""
	type: Literal['folder']
	name: str
	include_patterns: list[str] | None = Field(default_factory=lambda: ['**/*'])
	exclude_patterns: list[str] | None = Field(default_factory=list)


class GeneratePromptPayload(BaseModel):
	"""
	Request payload for generating system prompts.

	:param description: Description of the desired role or expertise
	"""
	description: str


class UrlPayload(BaseModel):
	"""
	Request payload for URL operations.

	:param url: The URL to add or remove
	"""
	url: str


# ---------------------------------------------------------------------
# RAG Management
# ---------------------------------------------------------------------

@router.get('', response_model=list[str])
async def list_rags() -> list[str]:
	"""
	List every existing RAG index.

	:return: List of RAG names
	"""
	return rag_service.list_rags()


@router.get('/{rag_name}/config', response_model=dict)
async def get_rag_config(rag_name: str) -> dict[str, Any]:
	"""
	Get the configuration for a specific RAG.

	:param rag_name: Name of the RAG instance
	:return: RAG configuration as dictionary
	:raises HTTPException: 404 if RAG not found
	"""
	try:
		config = rag_service.get_rag_config(rag_name)
		return config.model_dump()
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put('/{rag_name}/config', status_code=200)
async def update_rag_config(rag_name: str, config_data: dict[str, Any]):
	"""
	Update the configuration for a specific RAG.

	:param rag_name: Name of the RAG instance
	:param config_data: New configuration data
	:return: JSON response confirming update
	:raises HTTPException: 404 if RAG not found, 400 if invalid config
	"""
	try:
		# Load existing config to avoid resetting unspecified fields
		existing_config = rag_service.get_rag_config(rag_name)

		if len(config_data) == 0:
			raise HTTPException(status_code=400, detail='Invalid configuration: body must be a non-empty JSON object')

		# Only apply provided fields
		allowed_keys = {'chat_model', 'embedding_model', 'file_filters', 'system_prompt'}
		updates: dict[str, Any] = {k: v for k, v in config_data.items() if k in allowed_keys}

		if len(updates) == 0:
			# Nothing to update
			return JSONResponse({'detail': 'No changes provided'}, status_code=200)

		# Validate updates by constructing a partial model merged into existing
		new_config = existing_config.model_copy(update=updates)
		# Full-model validation
		validated_config = RAGConfig.model_validate(new_config.model_dump())

		rag_service.update_rag_config(rag_name, validated_config)
		return validated_config.model_dump()
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc
	except (KeyError, ValueError) as exc:
		raise HTTPException(status_code=400, detail=f'Invalid configuration: {str(exc)}') from exc


@router.get('/models', response_model=dict[str, list[ModelInfo]])
async def get_available_models() -> dict[str, list[ModelInfo]]:
	"""
	Get all available OpenAI models for chat and embeddings.

	:return: Dictionary containing available chat models and embedding models
	"""
	return await get_openai_models()


@router.post('/{rag_name}/generate-prompt', response_model=dict)
async def generate_system_prompt(rag_name: str, payload: GeneratePromptPayload) -> dict[str, str]:
	"""
	Generate a system prompt based on a description.

	:param rag_name: Name of the RAG instance
	:param payload: Description of the desired role or expertise
	:return: Generated system prompt
	:raises HTTPException: 404 if RAG not found
	"""
	if rag_name not in rag_service.list_rags():
		raise HTTPException(status_code=404, detail='RAG not found')

	try:
		# Use the RAG service to generate a prompt
		prompt = rag_service.generate_system_prompt(payload.description)
		return {'prompt': prompt}
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f'Failed to generate prompt: {str(exc)}') from exc


# ---------------------------------------------------------------------
# Document Management
# ---------------------------------------------------------------------

@router.post('/{rag_name}/urls', status_code=201)
async def add_url_to_rag(rag_name: str, payload: UrlPayload):
	"""
	Add a URL as a document to a RAG index.

	:param rag_name: Name of the RAG instance
	:param payload: URL to add
	:return: JSON response with URL details
	:raises HTTPException: 404 if RAG not found, 400 if URL processing fails
	"""
	if rag_name not in rag_service.list_rags():
		raise HTTPException(status_code=404, detail='RAG not found')

	try:
		rag_service.add_url_to_rag(rag_name, payload.url)
		return JSONResponse({
			'detail': 'URL added successfully to RAG index',
			'url': payload.url
		}, status_code=201)
	except Exception as exc:
		raise HTTPException(status_code=400, detail=f'Failed to add URL: {str(exc)}') from exc


@router.delete('/{rag_name}/urls', status_code=204)
async def remove_url_from_rag(rag_name: str, payload: UrlPayload):
	"""
	Remove a URL document from a RAG index.

	:param rag_name: Name of the RAG instance
	:param payload: URL to remove
	:raises HTTPException: 404 if RAG not found, 400 if removal fails
	"""
	if rag_name not in rag_service.list_rags():
		raise HTTPException(status_code=404, detail='RAG not found')

	try:
		rag_service.remove_url_from_rag(rag_name, payload.url)
	except Exception as exc:
		raise HTTPException(status_code=400, detail=f'Failed to remove URL: {str(exc)}') from exc


@router.get('/{rag_name}/urls', response_model=list[dict[str, str]])
async def list_urls_in_rag(rag_name: str) -> list[dict[str, str]]:
	"""
	List all URLs in a RAG index.

	:param rag_name: Name of the RAG instance
	:return: List of URL documents with metadata
	:raises HTTPException: 404 if RAG not found
	"""
	if rag_name not in rag_service.list_rags():
		raise HTTPException(status_code=404, detail='RAG not found')

	try:
		return rag_service.list_urls_in_rag(rag_name)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f'Failed to list URLs: {str(exc)}') from exc

@router.delete('/{rag_name}/files/{filename}', status_code=204)
async def delete_file(rag_name: str, filename: str):
	"""
	Delete a specific file from the RAG's document directory.

	:param rag_name: Name of the RAG instance
	:param filename: Name of the file to delete
	:raises HTTPException: 404 if file or RAG not found
	"""
	try:
		rag_service.delete_file(rag_name, filename)
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get('/{rag_name}/files', response_model=list[dict[str, Any]])
async def list_files(rag_name: str) -> list[dict[str, Any]]:
	"""
	List all files and directories in the RAG's document directory.

	:param rag_name: Name of the RAG instance
	:return: List of file/directory info with name, type, and link target (if symlink)
	:raises HTTPException: 404 if RAG not found
	"""
	try:
		return rag_service.list_files(rag_name)
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/{rag_name}/files', status_code=201)
async def upload_file_or_create_folder(rag_name: str, request: Request, file: UploadFile | None = File(None)):
	"""
	Upload a document to the RAG's files directory or create a folder with filters.

	:param rag_name: Name of the RAG instance
	:param request: HTTP request object
	:param file: File to upload (for file uploads)
	:return: JSON response with upload/creation details
	:raises HTTPException: 400 for invalid requests, 500 if operation fails
	"""
	# Handle file upload (multipart/form-data) - check file presence first
	if file is not None and file.filename:
		try:
			file_path = rag_service.save_file(rag_name, file.filename or 'unnamed_file', await file.read())
			return JSONResponse({
				'detail': f'File uploaded successfully',
				'filename': file.filename,
				'path': str(file_path)
			}, status_code=201)
		except Exception as exc:
			raise HTTPException(status_code=500, detail=f'Upload failed: {str(exc)}') from exc

	# Handle folder creation (JSON request)
	content_type = request.headers.get('content-type', '')
	if content_type.startswith('application/json'):
		try:
			body = await request.json()
			folder_data = FolderPayload.model_validate(body)

			# Create the folder
			folder_path = rag_service.create_folder(rag_name, folder_data.name)

			# Update RAG configuration with file filters
			try:
				config = rag_service.get_rag_config(rag_name)
			except FileNotFoundError:
				config = RAGConfig()

			config.file_filters[folder_data.name] = {
				'include': folder_data.include_patterns or ['**/*'],
				'exclude': folder_data.exclude_patterns or []
			}

			rag_service.update_rag_config(rag_name, config)

			return JSONResponse({
				'detail': f'Folder created successfully with file filters',
				'folder_name': folder_data.name,
				'path': str(folder_path),
				'filters': config.file_filters[folder_data.name]
			}, status_code=201)

		except Exception as exc:
			raise HTTPException(status_code=500, detail=f'Folder creation failed: {str(exc)}') from exc

	else:
		raise HTTPException(status_code=400, detail='Invalid request: must provide either file for upload or JSON data for folder creation')


@router.post('/{rag_name}/symlink', status_code=201)
async def create_symlink(rag_name: str, payload: SymlinkPayload):
	"""
	Create a symbolic link in the RAG's document directory with file filters.

	:param rag_name: Name of the RAG instance
	:param payload: Symbolic link creation request
	:return: JSON response with symlink details
	:raises HTTPException: 400 if target doesn't exist or link already exists, 500 if creation fails
	"""
	try:
		link_path = rag_service.create_symlink(rag_name, payload.target_path, payload.link_name)

		# Update RAG configuration with file filters
		try:
			config = rag_service.get_rag_config(rag_name)
		except FileNotFoundError:
			config = RAGConfig()

		config.file_filters[payload.link_name] = {
			'include': payload.include_patterns or ['**/*'],
			'exclude': payload.exclude_patterns or []
		}

		rag_service.update_rag_config(rag_name, config)

		return JSONResponse({
			'detail': 'Symbolic link created successfully with file filters',
			'link_name': payload.link_name,
			'target_path': payload.target_path,
			'path': str(link_path),
			'filters': config.file_filters[payload.link_name]
		}, status_code=201)
	except FileNotFoundError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except FileExistsError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f'Symlink creation failed: {str(exc)}') from exc


# ---------------------------------------------------------------------
# Query Operations
# ---------------------------------------------------------------------


@router.post('/{rag_name}/stream')
async def stream_rag(rag_name: str, payload: QueryPayload):
	"""
	Stream the answer for payload.query token-by-token using Server-Sent Events, using the agentic workflow.

	:param rag_name: Name of the RAG instance to query
	:param payload: Query request containing the question
	:return: Streaming response with JSON events, one per line
	:raises HTTPException: 404 if RAG not found
	"""
	if rag_name not in rag_service.list_rags():
		raise HTTPException(status_code=404, detail='RAG not found')

	async def _generator() -> AsyncGenerator[str, None]:
		history = [LLamaIndexChatMessage(role=msg.role, content=msg.content) for msg in (payload.history or [])]
		try:
			event: StreamEvent
			async for event in rag_service.async_agent_stream(rag_name, payload.query, history):
				# Simply serialize each event as JSON and send it as a line
				try:
					event_json = json.dumps(event)
					yield f"{event_json}\n"
				except (TypeError, ValueError) as e:
					log.warning(f"failed to serialize event: {e}")
					# Continue with next event if one fails
					continue
		except Exception as exc:
			log.exception(f'error during agent stream: {exc}')
			# Send error as a JSON event
			error_event = {
				'type': 'error',
				'data': f'An unexpected error occurred during the stream. Please check the server logs.'
			}
			yield f"{json.dumps(error_event)}\n"

	return StreamingResponse(_generator(), media_type='text/plain')


# ---------------------------------------------------------------------
# RAG Index Management
# ---------------------------------------------------------------------

@router.post('/{rag_name}', status_code=201)
async def create_rag(rag_name: str):
	"""
	Build a new RAG index from the documents located in data/files/<rag_name>/.

	:param rag_name: Name of the RAG instance to create
	:return: JSON response confirming creation
	:raises HTTPException: 404 if input directory not found, 500 if creation fails
	"""
	try:
		rag_service.create_rag(rag_name)
		return JSONResponse(status_code=200, content={'message': f'RAG "{rag_name}" created/rebuilt successfully.'})
	except Exception as e:
		log.exception(f"error creating RAG: {e}")
		raise HTTPException(status_code=500, detail=f'Failed to create RAG: {e}')


@router.post('/{rag_name}/reindex', status_code=200)
async def reindex_rag(rag_name: str):
	"""
	Manually reindex a RAG from all files in its document directory.

	This endpoint rebuilds the vector index using all files currently
	in the RAG's document directory, including any recently added files
	or symbolic links.

	:param rag_name: Name of the RAG instance to reindex
	:return: JSON response confirming reindexing
	:raises HTTPException: 404 if RAG not found, 500 if reindexing fails
	"""
	if rag_name not in rag_service.list_rags():
		raise HTTPException(status_code=404, detail='RAG not found')

	try:
		rag_service.create_rag(rag_name)  # create_rag already handles rebuilding
		return JSONResponse({'message': f'RAG "{rag_name}" reindexed successfully.'})
	except Exception as e:
		log.exception(f"error reindexing RAG: {e}")
		raise HTTPException(status_code=500, detail=f'Failed to reindex RAG: {e}')


@router.delete('/{rag_name}', status_code=204)
async def delete_rag(rag_name: str):
	"""
	Delete a RAG index and all its associated files.

	:param rag_name: Name of the RAG instance to delete
	:raises HTTPException: 404 if RAG not found
	"""
	try:
		rag_service.delete_rag(rag_name)
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc
