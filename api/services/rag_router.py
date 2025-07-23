"""
RAG API router containing all endpoints for managing RAG indices and documents.
"""

from typing import AsyncGenerator

from fastapi import APIRouter, File, HTTPException, UploadFile, Form
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
	"""
	target_path: str
	link_name: str


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
async def get_rag_config(rag_name: str) -> dict:
	"""
	Get the configuration for a specific RAG.

	:param rag_name: Name of the RAG instance
	:return: RAG configuration as dictionary
	:raises HTTPException: 404 if RAG not found
	"""
	try:
		config = rag_service.get_rag_config(rag_name)
		return config.to_dict()
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put('/{rag_name}/config', status_code=200)
async def update_rag_config(rag_name: str, config_data: dict):
	"""
	Update the configuration for a specific RAG.

	:param rag_name: Name of the RAG instance
	:param config_data: New configuration data
	:return: JSON response confirming update
	:raises HTTPException: 404 if RAG not found, 400 if invalid config
	"""
	try:
		config = RAGConfig.from_dict(config_data)
		rag_service.update_rag_config(rag_name, config)
		return JSONResponse({'detail': 'Configuration updated successfully'})
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc
	except (KeyError, ValueError) as exc:
		raise HTTPException(status_code=400, detail=f'Invalid configuration: {str(exc)}') from exc


@router.get('/models', response_model=dict)
async def get_available_models() -> dict:
	"""
	Get all available OpenAI models for chat and embeddings.

	:return: Dictionary containing available chat models and embedding models
	"""
	return await get_openai_models()


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


@router.get('/{rag_name}/files', response_model=list[dict])
async def list_files(rag_name: str) -> list[dict]:
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


@router.post('/{rag_name}/symlink', status_code=201)
async def create_symlink(rag_name: str, payload: SymlinkPayload):
	"""
	Create a symbolic link in the RAG's document directory.

	:param rag_name: Name of the RAG instance
	:param payload: Symbolic link creation request
	:return: JSON response with symlink details
	:raises HTTPException: 400 if target doesn't exist or link already exists, 500 if creation fails
	"""
	try:
		link_path = rag_service.create_symlink(rag_name, payload.target_path, payload.link_name)
		return JSONResponse({
			'detail': 'Symbolic link created successfully',
			'link_name': payload.link_name,
			'target_path': payload.target_path,
			'path': str(link_path)
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

@router.post('/{rag_name}/query', response_model=QueryResponse)
async def query_rag(rag_name: str, payload: QueryPayload) -> QueryResponse:
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
		response_content = rag_service.query(rag_name, payload.query)
		return QueryResponse(content=response_content)
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
		print(f"Error reindexing RAG: {e}")  # Log the full error
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
