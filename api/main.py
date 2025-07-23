"""
Main FastAPI application entry-point for the multi-RAG API.

This module initializes the FastAPI application and includes all route handlers
for managing multiple RAG (Retrieval-Augmented Generation) instances.
"""

from fastapi import FastAPI

from services.rag_router import router as rag_router


# Initialize FastAPI app
app = FastAPI(
	title='Multi-RAG API',
	description='A file-based Retrieval-Augmented Generation service built on LlamaIndex',
	version='1.0.0'
)

# Include routers
app.include_router(rag_router)


@app.get('/')
async def health_check():
	"""
	Health check endpoint.

	:return: Status information about the API
	"""
	return {'status': 'healthy', 'message': 'Multi-RAG API is running'}


if __name__ == '__main__':
	import uvicorn
	uvicorn.run(app, host='0.0.0.0', port=8000)
