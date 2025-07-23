"""
RAG API router containing all endpoints for managing RAG indices and documents.
"""

from typing import AsyncGenerator

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from src.rag import RAGConfig, RAGService
from src.openai_models import get_openai_models

router = APIRouter(prefix='/rag', tags=['RAG'])
rag_service = RAGService()


class QueryPayload(BaseModel):
	"""
	Request payload for RAG query operations.

	:param query: The question or prompt to send to the RAG system
	"""
	query: str


class ConfigPayload(BaseModel):
	"""
	Request payload for RAG configuration operations.

	:param chat_model: OpenAI model to use for chat completions
	:param embedding_model: OpenAI model to use for embeddings
	:param system_prompt: System prompt to guide the model's responses
	"""
	chat_model: str = 'gpt-4o-mini'
	embedding_model: str = 'text-embedding-3-large'
	system_prompt: str = 'You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.'


# ---------------------------------------------------------------------
# OpenAI Models
# ---------------------------------------------------------------------

@router.get('/models')
async def get_models():
	"""
	Retrieve available OpenAI models, filtered by deprecation status and categorized.

	Returns models in three categories:
	- chat: Models for text generation and conversation
	- embedding: Models for creating embeddings
	- thinking: Models specialized for reasoning (o1, o3, o4 series)

	:return: Dictionary with categorized model lists
	:raises HTTPException: 500 if OpenAI API fails
	"""
	try:
		models = await get_openai_models()
		return JSONResponse(content=models, status_code=200)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to fetch OpenAI models: {str(e)}')


# ---------------------------------------------------------------------
# RAG Configuration Management
# ---------------------------------------------------------------------

@router.get('/{rag_name}/config')
async def get_rag_config(rag_name: str):
	"""
	Get the configuration for a specific RAG.

	:param rag_name: Name of the RAG instance
	:return: RAG configuration as dictionary
	:raises HTTPException: 404 if RAG not found
	"""
	if rag_name not in rag_service.list_rags():
		raise HTTPException(status_code=404, detail='RAG not found')

	try:
		config = rag_service.get_rag_config(rag_name)
		return config.to_dict()
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f'Failed to get config: {str(exc)}') from exc


@router.put('/{rag_name}/config')
async def update_rag_config(rag_name: str, config: ConfigPayload):
	"""
	Update the configuration for a specific RAG.

	:param rag_name: Name of the RAG instance
	:param config: New configuration settings
	:return: JSON response confirming update
	:raises HTTPException: 404 if RAG not found, 500 if update fails
	"""
	if rag_name not in rag_service.list_rags():
		raise HTTPException(status_code=404, detail='RAG not found')

	try:
		rag_config = RAGConfig(
			chat_model=config.chat_model,
			embedding_model=config.embedding_model,
			system_prompt=config.system_prompt
		)
		rag_service.update_rag_config(rag_name, rag_config)
		return JSONResponse({'message': f'Configuration for RAG "{rag_name}" updated successfully.'})
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f'Failed to update config: {str(exc)}') from exc


# ---------------------------------------------------------------------
# Document Management
# ---------------------------------------------------------------------

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


@router.get('/{rag_name}/files', response_model=list[str])
async def list_files(rag_name: str) -> list[str]:
	"""
	List all files in the RAG's document directory.

	:param rag_name: Name of the RAG instance
	:return: List of filenames in the document directory
	:raises HTTPException: 404 if RAG not found
	"""
	try:
		return rag_service.list_files(rag_name)
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/{rag_name}/files', status_code=201)
async def upload_file(rag_name: str, file: UploadFile = File(...)):
	"""
	Upload a document to the RAG's files directory.

	:param rag_name: Name of the RAG instance
	:param file: File to upload
	:return: JSON response with upload details
	:raises HTTPException: 500 if upload fails
	"""
	try:
		file_path = rag_service.save_file(rag_name, file.filename or 'unnamed_file', file.file.read())
		return JSONResponse({
			'detail': f'File uploaded successfully',
			'filename': file.filename,
			'path': str(file_path)
		}, status_code=201)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f'Upload failed: {str(exc)}') from exc


# ---------------------------------------------------------------------
# Query Operations
# ---------------------------------------------------------------------

@router.post('/{rag_name}/query', response_model=str)
async def query_rag(rag_name: str, payload: QueryPayload) -> str:
	"""
	Return the full answer for payload.query using the specified RAG.

	:param rag_name: Name of the RAG instance to query
	:param payload: Query request containing the question
	:return: Generated response as string
	:raises HTTPException: 404 if RAG not found, 500 if query fails
	"""
	if rag_name not in rag_service.list_rags():
		raise HTTPException(status_code=404, detail='RAG not found')

	try:
		return rag_service.query(rag_name, payload.query)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f'Query failed: {str(exc)}') from exc


@router.post('/{rag_name}/stream')
async def stream_rag(rag_name: str, payload: QueryPayload):
	"""
	Stream the answer for payload.query token-by-token using Server-Sent Events.

	:param rag_name: Name of the RAG instance to query
	:param payload: Query request containing the question
	:return: Streaming response with text chunks
	:raises HTTPException: 404 if RAG not found
	"""
	if rag_name not in rag_service.list_rags():
		raise HTTPException(status_code=404, detail='RAG not found')

	async def _generator() -> AsyncGenerator[str, None]:
		"""
		Internal generator for streaming response chunks.

		:yield: Individual response tokens as strings
		"""
		try:
			async for chunk in rag_service.stream_query(rag_name, payload.query):
				yield chunk
		except Exception as exc:
			yield f'Error: {str(exc)}'

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
		print(f"Error creating RAG: {e}") # Log the full error
		raise HTTPException(status_code=500, detail=f'Failed to create RAG: {e}')


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


@router.get('', response_model=list[str])
async def list_rags() -> list[str]:
	"""
	Return every existing RAG name (folder under data/indices).

	:return: List of available RAG instance names
	"""
	return rag_service.list_rags()
