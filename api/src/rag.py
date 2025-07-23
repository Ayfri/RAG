"""
RAG related utilities built on top of LlamaIndex.

All indices and source documents are stored on the local filesystem:
- data/files/<rag_name>/ : raw files to embed
- data/indices/<rag_name>/ : vector indices & metadata
"""

from pathlib import Path
from typing import AsyncGenerator

from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex


class RAGService:
	"""
	Utility class offering a minimal API to build, list and query Retrieval-Augmented Generation indices.

	This service manages RAG indices stored on the filesystem, providing methods to create,
	delete, query, and manage documents for multiple RAG instances.
	"""

	_FILES_DIR = Path('data/files')
	_INDICES_DIR = Path('data/indices')


	def __init__(self):
		"""
		Initialize the RAG service and ensure required directories exist.
		"""
		self._FILES_DIR.mkdir(parents=True, exist_ok=True)
		self._INDICES_DIR.mkdir(parents=True, exist_ok=True)


	def create_rag(self, rag_name: str) -> None:
		"""
		(Re)create an index from the documents located under data/files/<rag_name>/.

		If an index already exists it gets overwritten.

		:param rag_name: Name of the RAG instance
		:raises FileNotFoundError: If the input directory for the RAG doesn't exist
		"""
		files_path = self._FILES_DIR / rag_name
		if not files_path.exists():
			raise FileNotFoundError(
				f'No input directory found for RAG "{rag_name}". Expected {files_path}.'
			)

		# Load & embed documents
		docs = SimpleDirectoryReader(str(files_path)).load_data()
		index = VectorStoreIndex.from_documents(docs)

		# Persist on disk (overwrite)
		persist_dir = self._INDICES_DIR / rag_name
		if persist_dir.exists():
			# remove previous index to avoid stale files
			for child in persist_dir.iterdir():
				child.unlink()
		else:
			persist_dir.mkdir(parents=True, exist_ok=True)

		index.storage_context.persist(persist_dir=str(persist_dir))


	def delete_file(self, rag_name: str, filename: str) -> None:
		"""
		Delete a specific file from the RAG's document directory.

		:param rag_name: Name of the RAG instance
		:param filename: Name of the file to delete
		:raises FileNotFoundError: If the files directory or specific file doesn't exist
		"""
		files_path = self._FILES_DIR / rag_name
		if not files_path.exists():
			raise FileNotFoundError(f'Files directory for RAG "{rag_name}" not found.')

		file_path = files_path / filename
		if not file_path.exists():
			raise FileNotFoundError(f'File "{filename}" not found in RAG "{rag_name}".')

		file_path.unlink()


	def delete_rag(self, rag_name: str) -> None:
		"""
		Delete a RAG index and all its associated files.

		:param rag_name: Name of the RAG instance to delete
		:raises FileNotFoundError: If the RAG doesn't exist
		"""
		index_path = self._INDICES_DIR / rag_name
		files_path = self._FILES_DIR / rag_name

		if not index_path.exists():
			raise FileNotFoundError(f'RAG "{rag_name}" not found.')

		# Remove index directory
		if index_path.exists():
			for child in index_path.rglob('*'):
				if child.is_file():
					child.unlink()
			index_path.rmdir()

		# Remove files directory if it exists
		if files_path.exists():
			for child in files_path.rglob('*'):
				if child.is_file():
					child.unlink()
			files_path.rmdir()


	def list_files(self, rag_name: str) -> list[str]:
		"""
		List all files in the RAG's document directory.

		:param rag_name: Name of the RAG instance
		:return: List of filenames in the RAG's document directory
		:raises FileNotFoundError: If the files directory doesn't exist
		"""
		files_path = self._FILES_DIR / rag_name
		if not files_path.exists():
			raise FileNotFoundError(f'Files directory for RAG "{rag_name}" not found.')

		return [f.name for f in files_path.iterdir() if f.is_file()]


	def list_rags(self) -> list[str]:
		"""
		Return every available RAG name.

		:return: List of RAG names (directory names under data/indices)
		"""
		return [p.name for p in self._INDICES_DIR.iterdir() if p.is_dir()]


	def query(self, rag_name: str, query: str) -> str:
		"""
		Return the answer for query using the given rag_name.

		:param rag_name: Name of the RAG instance to query
		:param query: Question to ask the RAG
		:return: Generated response as string
		:raises FileNotFoundError: If the RAG index doesn't exist
		"""
		index = self._load_index(rag_name)
		response = index.as_query_engine().query(query)
		return str(response)


	def save_file(self, rag_name: str, filename: str, content: bytes) -> Path:
		"""
		Save a file to the RAG's document directory.

		:param rag_name: Name of the RAG instance
		:param filename: Name for the saved file
		:param content: File content as bytes
		:return: Path to the saved file
		"""
		files_path = self._FILES_DIR / rag_name
		files_path.mkdir(parents=True, exist_ok=True)

		file_path = files_path / filename
		file_path.write_bytes(content)
		return file_path


	async def stream_query(self, rag_name: str, query: str) -> AsyncGenerator[str, None]:
		"""
		Asynchronously yield the answer token-by-token.

		:param rag_name: Name of the RAG instance to query
		:param query: Question to ask the RAG
		:yield: Individual response tokens as strings
		:raises FileNotFoundError: If the RAG index doesn't exist
		"""
		index = self._load_index(rag_name)
		query_engine = index.as_query_engine(streaming=True)
		response = query_engine.query(query)
		for chunk in response.response_gen:  # type: ignore[attr-defined]
			yield chunk


	def _load_index(self, rag_name: str) -> VectorStoreIndex:
		"""
		Load a persisted RAG index from disk.

		:param rag_name: Name of the RAG instance to load
		:return: Loaded VectorStoreIndex instance
		:raises FileNotFoundError: If the index directory doesn't exist
		"""
		persist_dir = self._INDICES_DIR / rag_name
		if not persist_dir.exists():
			raise FileNotFoundError(f'No index found for RAG "{rag_name}".')
		storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))
		return VectorStoreIndex.from_storage(storage_context)  # type: ignore[attr-defined]
