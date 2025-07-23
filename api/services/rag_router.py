"""
RAG API router containing all endpoints for managing RAG indices and documents.
"""

from typing import AsyncGenerator

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from api.src.rag import RAGService

router = APIRouter(prefix='/rag', tags=['RAG'])
rag_service = RAGService()


class QueryPayload(BaseModel):
	"""
	Request payload for RAG query operations.

	:param query: The question or prompt to send to the RAG system
	"""
	query: str


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
		return JSONResponse({'detail': f'RAG "{rag_name}" created successfully'}, status_code=201)
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f'Failed to create RAG: {str(exc)}') from exc


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
