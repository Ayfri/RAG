"""
RAG Document Manager for handling document and URL operations.

Manages file operations, directory structures, URL documents, and document metadata
for RAG systems. Separated from core RAG functionality for better organization.
"""

import json
import os
from pathlib import Path
from typing import Any, cast

from llama_index.core import Settings, VectorStoreIndex, load_index_from_storage, StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding

from src.config import OPENAI_API_KEY
from src.logger import get_logger
from src.rag_config import RAGConfig
from src.utils import fetch_url_content, get_dir_stats

logger = get_logger(__name__)


class RAGDocumentManager:
	"""Manages document operations for RAG systems including files, directories, and URLs."""

	def __init__(self, files_dir: Path | None = None, indices_dir: Path | None = None, configs_dir: Path | None = None, resumes_dir: Path | None = None):
		"""Initialize the document manager with directory paths."""
		self._FILES_DIR = files_dir or Path('data/files')
		self._INDICES_DIR = indices_dir or Path('data/indices')
		self._CONFIGS_DIR = configs_dir or Path('data/configs')
		self._RESUMES_DIR = resumes_dir or Path('data/resumes')

		# Ensure directories exist
		self._FILES_DIR.mkdir(parents=True, exist_ok=True)
		self._INDICES_DIR.mkdir(parents=True, exist_ok=True)
		self._CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
		self._RESUMES_DIR.mkdir(parents=True, exist_ok=True)


	@property
	def configs_dir(self) -> Path:
		"""Get the configs directory path."""
		return self._CONFIGS_DIR


	@property
	def files_dir(self) -> Path:
		"""Get the files directory path."""
		return self._FILES_DIR


	@property
	def indices_dir(self) -> Path:
		"""Get the indices directory path."""
		return self._INDICES_DIR


	@property
	def resumes_dir(self) -> Path:
		"""Get the resumes directory path."""
		return self._RESUMES_DIR


	def add_url_to_rag(self, rag_name: str, url: str, config: RAGConfig) -> None:
		"""Add a URL as a document to a RAG index."""
		existing_urls = self.list_urls_in_rag(rag_name, config)
		for existing_url in existing_urls:
			if existing_url['url'] == url:
				raise Exception(f"URL '{url}' already exists in RAG '{rag_name}'")

		document = fetch_url_content(url)
		embed_model = OpenAIEmbedding(
			api_key=OPENAI_API_KEY,
			model=config.embedding_model,
		)

		try:
			index = self._load_index(rag_name, config)
		except FileNotFoundError:
			index = VectorStoreIndex.from_documents([])

		original_embed_model = Settings.embed_model
		Settings.embed_model = embed_model

		try:
			index.insert(document)
			self.save_index(rag_name, index)
		finally:
			Settings.embed_model = original_embed_model


	def create_folder(self, rag_name: str, folder_name: str) -> Path:
		"""Create an empty folder in the RAG's document directory."""
		files_path = self._FILES_DIR / rag_name
		files_path.mkdir(parents=True, exist_ok=True)

		folder_path = files_path / folder_name
		if folder_path.exists():
			raise FileExistsError(f'Folder "{folder_name}" already exists')

		folder_path.mkdir(parents=True, exist_ok=True)
		return folder_path


	def create_symlink(self, rag_name: str, target_path: str, link_name: str) -> Path:
		"""Create a symbolic link in the RAG's document directory."""
		files_path = self._FILES_DIR / rag_name
		files_path.mkdir(parents=True, exist_ok=True)

		target = Path(target_path)
		if not target.exists():
			raise FileNotFoundError(f'Target path "{target_path}" does not exist.')

		link_path = files_path / link_name
		if link_path.exists():
			raise FileExistsError(f'Link "{link_name}" already exists in RAG "{rag_name}".')

		if os.name == 'nt':
			if target.is_dir():
				link_path.symlink_to(target, target_is_directory=True)
			else:
				link_path.symlink_to(target)
		else:
			link_path.symlink_to(target)

		return link_path


	def delete_file(self, rag_name: str, filename: str) -> None:
		"""Delete a specific file from the RAG's document directory."""
		files_path = self._FILES_DIR / rag_name
		if not files_path.exists():
			raise FileNotFoundError(f'Files directory for RAG "{rag_name}" not found.')

		file_path = files_path / filename
		if not file_path.exists():
			raise FileNotFoundError(f'File "{filename}" not found in RAG "{rag_name}".')

		file_path.unlink()


	def get_files(self, input_path: Path) -> list[str]:
		"""Return list of file names (not directories or symlinks) in input_path."""
		return [f.name for f in input_path.iterdir() if f.is_file() and not f.is_symlink()]


	def get_rag_config(self, rag_name: str) -> RAGConfig:
		"""Get the configuration for a specific RAG."""
		return self._load_rag_config(rag_name)


	def get_summary_path(self, rag_name: str) -> Path:
		"""Get the path to the summary file for a RAG."""
		return self._RESUMES_DIR / f'{rag_name}.md'


	def get_symlinks(self, input_path: Path) -> list[Path]:
		"""Return list of symlink Paths in input_path."""
		return [f for f in input_path.iterdir() if f.is_symlink()]


	def list_files(self, rag_name: str) -> list[dict[str, Any]]:
		"""List all files and directories in the RAG's document directory with metadata."""
		files_path = self._FILES_DIR / rag_name
		if not files_path.exists():
			raise FileNotFoundError(f'Files directory for RAG "{rag_name}" not found.')

		items: list[dict[str, Any]] = []
		for item in files_path.iterdir():
			item_info: dict[str, Any] = {
				'name': item.name,
				'type': 'directory' if item.is_dir() else 'file',
				'is_symlink': item.is_symlink()
			}

			try:
				stat = item.stat()
				item_info['last_modified'] = stat.st_mtime
			except OSError:
				item_info['last_modified'] = None

			if item.is_symlink():
				try:
					resolved_target = item.resolve()
					item_info['target'] = str(item.readlink())
					item_info['resolved_target_type'] = 'directory' if resolved_target.is_dir() else 'file'
					if resolved_target.is_dir():
						file_count, total_size = get_dir_stats(resolved_target)
						item_info['file_count'] = file_count
						item_info['size'] = total_size
					else:
						try:
							item_info['size'] = resolved_target.stat().st_size
						except OSError:
							item_info['size'] = None
				except OSError:
					item_info['target'] = '<broken link>'
					item_info['resolved_target_type'] = 'unknown'
			else:
				if item.is_dir():
					file_count, total_size = get_dir_stats(item)
					item_info['file_count'] = file_count
					item_info['size'] = total_size
				else:
					try:
						item_info['size'] = item.stat().st_size
					except OSError:
						item_info['size'] = None

			items.append(item_info)

		return sorted(items, key=lambda x: (x['type'], x['name'].lower()))


	def list_urls_in_rag(self, rag_name: str, config: RAGConfig) -> list[dict[str, str]]:
		"""List all URLs in a RAG index."""
		try:
			index = self._load_index(rag_name, config)
			documents: list[dict[str, str]] = []
			seen_urls: set[str] = set()

			for node in index.docstore.docs.values():
				if node.metadata.get('source_type') == 'web_page':
					url = cast(str, node.metadata.get('url', ''))
					if url not in seen_urls:
						seen_urls.add(url)
						documents.append({
							'url': url,
							'title': node.metadata.get('title', ''),
							'domain': node.metadata.get('domain', ''),
							'content_type': node.metadata.get('content_type', '')
						})

			return documents

		except FileNotFoundError:
			raise Exception(f"RAG '{rag_name}' not found")


	def load_index(self, rag_name: str) -> VectorStoreIndex:
		"""Load a persisted RAG index from disk. Public method for external use."""
		return self._load_index(rag_name, self._load_rag_config(rag_name))


	def remove_url_from_rag(self, rag_name: str, url: str, config: RAGConfig) -> None:
		"""Remove a URL document from a RAG index."""
		try:
			index = self._load_index(rag_name, config)

			deleted_count = 0
			for doc_id, doc in index.docstore.docs.items():
				if doc.metadata.get('url') == url:
					index.delete_ref_doc(doc_id, delete_from_docstore=True)
					index.delete_nodes([doc.node_id], delete_from_docstore=True)
					deleted_count += 1

			if deleted_count == 0:
				raise Exception(f"URL '{url}' not found in RAG '{rag_name}'")

			self.save_index(rag_name, index)

		except FileNotFoundError:
			raise Exception(f"RAG '{rag_name}' not found")


	def save_directory(self, rag_name: str, directory_name: str, directory_content: dict[str, Any]) -> Path:
		"""Save a directory structure to the RAG's document directory."""
		files_path = self._FILES_DIR / rag_name
		files_path.mkdir(parents=True, exist_ok=True)

		dir_path = files_path / directory_name
		dir_path.mkdir(exist_ok=True)

		def _create_structure(base_path: Path, structure: dict[str, dict[str, Any] | bytes]):
			for name, content in structure.items():
				item_path = base_path / name
				if isinstance(content, dict):
					item_path.mkdir(exist_ok=True)
					_create_structure(item_path, content)
				else:
					item_path.write_bytes(content)

		_create_structure(dir_path, directory_content)
		return dir_path


	def save_file(self, rag_name: str, filename: str, content: bytes) -> Path:
		"""Save a file to the RAG's document directory."""
		files_path = self._FILES_DIR / rag_name
		files_path.mkdir(parents=True, exist_ok=True)

		file_path = files_path / filename
		file_path.parent.mkdir(parents=True, exist_ok=True)
		file_path.write_bytes(content)
		return file_path


	def save_index(self, rag_name: str, index: VectorStoreIndex) -> None:
		"""Save index to disk."""
		persist_dir = self._INDICES_DIR / rag_name
		if persist_dir.exists():
			for child in persist_dir.iterdir():
				child.unlink()
		else:
			persist_dir.mkdir(parents=True, exist_ok=True)
		index.storage_context.persist(persist_dir=str(persist_dir))


	def save_summary(self, rag_name: str, summary: str) -> None:
		"""Save a project summary for a RAG."""
		summary_path = self.get_summary_path(rag_name)
		summary_path.write_text(summary, encoding='utf-8')


	def update_rag_config(self, rag_name: str, config: RAGConfig) -> None:
		"""Update the configuration for a specific RAG."""
		index_path = self._INDICES_DIR / rag_name
		if not index_path.exists():
			raise FileNotFoundError(f'RAG "{rag_name}" not found.')

		config_path = self._CONFIGS_DIR / f'{rag_name}.json'
		config_path.write_text(config.model_dump_json(indent=4))


	def _load_index(self, rag_name: str, config: RAGConfig) -> VectorStoreIndex:
		"""Load a persisted RAG index from disk."""
		persist_dir = self._INDICES_DIR / rag_name
		if not persist_dir.exists():
			raise FileNotFoundError(f'No index found for RAG "{rag_name}".')

		embed_model = OpenAIEmbedding(
			api_key=OPENAI_API_KEY,
			model=config.embedding_model,
		)

		original_embed_model = Settings.embed_model
		Settings.embed_model = embed_model

		try:
			storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))
			return load_index_from_storage(storage_context, use_async=True)  # type: ignore[attr-defined]
		finally:
			Settings.embed_model = original_embed_model


	def _load_rag_config(self, rag_name: str) -> RAGConfig:
		"""Load configuration for a specific RAG, creating default if not exists."""
		config_path = self._CONFIGS_DIR / f'{rag_name}.json'

		if config_path.exists():
			try:
				return RAGConfig.model_validate_json(config_path.read_text())
			except (json.JSONDecodeError, KeyError) as e:
				logger.warning(f'Invalid config file for RAG "{rag_name}": {e}. Using defaults.')

		default_config = RAGConfig()
		config_path.write_text(default_config.model_dump_json(indent=2))
		return default_config
