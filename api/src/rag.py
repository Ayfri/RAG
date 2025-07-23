"""
RAG related utilities built on top of LlamaIndex.

All indices and source documents are stored on the local filesystem:
- data/files/<rag_name>/ : raw files to embed
- data/indices/<rag_name>/ : vector indices & metadata
- data/configs/<rag_name>.json : configuration per RAG
"""

import json
from pathlib import Path
from typing import AsyncGenerator

import openai
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from src.config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY


class RAGConfig:
	"""
	Configuration class for individual RAG instances.
	"""

	def __init__(
		self,
		chat_model: str = 'gpt-4o-mini',
		embedding_model: str = 'text-embedding-3-large',
		system_prompt: str = 'You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.'
	):
		self.chat_model = chat_model
		self.embedding_model = embedding_model
		self.system_prompt = system_prompt

	@classmethod
	def from_dict(cls, data: dict) -> 'RAGConfig':
		"""Create RAGConfig from dictionary."""
		return cls(
			chat_model=data.get('chat_model', 'gpt-4o-mini'),
			embedding_model=data.get('embedding_model', 'text-embedding-3-large'),
			system_prompt=data.get('system_prompt', 'You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.')
		)

	def to_dict(self) -> dict:
		"""Convert RAGConfig to dictionary."""
		return {
			'chat_model': self.chat_model,
			'embedding_model': self.embedding_model,
			'system_prompt': self.system_prompt
		}


class RAGService:
	"""
	Utility class offering a minimal API to build, list and query Retrieval-Augmented Generation indices.

	This service manages RAG indices stored on the filesystem, providing methods to create,
	delete, query, and manage documents for multiple RAG instances.
	"""

	_FILES_DIR = Path('data/files')
	_INDICES_DIR = Path('data/indices')
	_CONFIGS_DIR = Path('data/configs')


	def __init__(self):
		"""
		Initialize the RAG service and ensure required directories exist.
		"""
		self._FILES_DIR.mkdir(parents=True, exist_ok=True)
		self._INDICES_DIR.mkdir(parents=True, exist_ok=True)
		self._CONFIGS_DIR.mkdir(parents=True, exist_ok=True)


	def create_rag(self, rag_name: str) -> None:
		"""
		(Re)create an index from the documents located under data/files/<rag_name>/.

		If an index already exists it gets overwritten.
		If the input directory does not exist, it will be created.

		:param rag_name: Name of the RAG instance
		"""
		files_path = self._FILES_DIR / rag_name
		files_path.mkdir(parents=True, exist_ok=True) # Ensure directory exists

		# Load or create configuration for this RAG
		config = self._load_rag_config(rag_name)

		# Configure embedding model for this specific RAG
		embed_model = OpenAIEmbedding(
			api_key=OPENAI_API_KEY,
			model=config.embedding_model,
		)

		docs = []
		if any(files_path.iterdir()): # Only load data if files exist
			docs = SimpleDirectoryReader(str(files_path)).load_data()

		# Temporarily set the embedding model for this operation
		original_embed_model = Settings.embed_model
		Settings.embed_model = embed_model

		try:
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
		finally:
			# Restore original embedding model
			Settings.embed_model = original_embed_model


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
		config_path = self._CONFIGS_DIR / f'{rag_name}.json'

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

		# Remove config file if it exists
		if config_path.exists():
			config_path.unlink()


	def get_rag_config(self, rag_name: str) -> RAGConfig:
		"""
		Get the configuration for a specific RAG.

		:param rag_name: Name of the RAG instance
		:return: RAGConfig instance
		"""
		return self._load_rag_config(rag_name)


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
		config = self._load_rag_config(rag_name)

		# Configure LLM with RAG-specific settings
		llm = OpenAI(
			api_key=OPENAI_API_KEY,
			model=config.chat_model,
			system_prompt=config.system_prompt
		)

		query_engine = index.as_query_engine(llm=llm)
		response = query_engine.query(query)
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
		config = self._load_rag_config(rag_name)

		# Configure LLM with RAG-specific settings
		llm = OpenAI(
			api_key=OPENAI_API_KEY,
			model=config.chat_model,
			system_prompt=config.system_prompt
		)

		query_engine = index.as_query_engine(llm=llm, streaming=True)
		response = query_engine.query(query)
		for chunk in response.response_gen:  # type: ignore[attr-defined]
			yield chunk


	def update_rag_config(self, rag_name: str, config: RAGConfig) -> None:
		"""
		Update the configuration for a specific RAG.

		:param rag_name: Name of the RAG instance
		:param config: New configuration
		:raises FileNotFoundError: If the RAG doesn't exist
		"""
		index_path = self._INDICES_DIR / rag_name
		if not index_path.exists():
			raise FileNotFoundError(f'RAG "{rag_name}" not found.')

		config_path = self._CONFIGS_DIR / f'{rag_name}.json'
		config_path.write_text(json.dumps(config.to_dict(), indent=2))


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

		# Load RAG-specific config for embedding model
		config = self._load_rag_config(rag_name)

		# Set up embedding model for loading
		embed_model = OpenAIEmbedding(
			api_key=OPENAI_API_KEY,
			model=config.embedding_model,
		)

		# Temporarily set the embedding model
		original_embed_model = Settings.embed_model
		Settings.embed_model = embed_model

		try:
			storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))
			return VectorStoreIndex.from_storage(storage_context)  # type: ignore[attr-defined]
		finally:
			# Restore original embedding model
			Settings.embed_model = original_embed_model


	def _load_rag_config(self, rag_name: str) -> RAGConfig:
		"""
		Load configuration for a specific RAG, creating default if not exists.

		:param rag_name: Name of the RAG instance
		:return: RAGConfig instance
		"""
		config_path = self._CONFIGS_DIR / f'{rag_name}.json'

		if config_path.exists():
			try:
				config_data = json.loads(config_path.read_text())
				return RAGConfig.from_dict(config_data)
			except (json.JSONDecodeError, KeyError) as e:
				print(f'Warning: Invalid config file for RAG "{rag_name}": {e}. Using defaults.')

		# Create default configuration
		default_config = RAGConfig()
		config_path.write_text(json.dumps(default_config.to_dict(), indent=2))
		return default_config
