"""
RAG related utilities built on top of LlamaIndex.

All indices and source documents are stored on the local filesystem:
- data/files/<rag_name>/ : raw files to embed
- data/indices/<rag_name>/ : vector indices & metadata
- data/configs/<rag_name>.json : configuration per RAG
"""

import json
import os
import re
from pathlib import Path
import textwrap
from typing import AsyncGenerator
from urllib.parse import urlparse

import openai
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex, Settings, load_index_from_storage
from llama_index.core.agent.workflow import AgentOutput, ToolCallResult
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.readers.json import JSONReader
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.schema import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# Web scraping imports
import html2text
import requests
from bs4 import BeautifulSoup

from src.agent import get_agent
from src.config import OPENAI_API_KEY
from src.rag_config import RAGConfig
from src.types import (
	ChatHistoryItem,
	DocumentItem,
	SearchResultItem,
	StreamEvent,
	TokenStreamEvent,
	SourcesStreamEvent,
	DocumentsStreamEvent,
	ReadFileStreamEvent,
	ListFilesStreamEvent,
	ChatHistoryStreamEvent,
	FinalStreamEvent,
	FileReadResult,
	FileListResult
)

openai.api_key = OPENAI_API_KEY


class RAGService:
	"""
	Utility class offering a minimal API to build, list and query Retrieval-Augmented Generation indices.

	This service manages RAG indices stored on the filesystem, providing methods to create,
	delete, query, and manage documents for multiple RAG instances.
	"""

	_FILES_DIR = Path('data/files')
	_INDICES_DIR = Path('data/indices')
	_CONFIGS_DIR = Path('data/configs')
	_RESUMES_DIR = Path('data/resumes')


	def __init__(self):
		"""
		Initialize the RAG service and ensure required directories exist.
		"""
		self._FILES_DIR.mkdir(parents=True, exist_ok=True)
		self._INDICES_DIR.mkdir(parents=True, exist_ok=True)
		self._CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
		self._RESUMES_DIR.mkdir(parents=True, exist_ok=True)


	def get_files(self, input_path: Path) -> list[str]:
		"""Return list of file names (not directories or symlinks) in input_path."""
		return [f.name for f in input_path.iterdir() if f.is_file() and not f.is_symlink()]

	def get_symlinks(self, input_path: Path) -> list[Path]:
		"""Return list of symlink Paths in input_path."""
		return [f for f in input_path.iterdir() if f.is_symlink()]

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

		docs: list[Document] = []
		files = self.get_files(files_path)
		symlinks = self.get_symlinks(files_path)

		# Load documents from symlinks
		if symlinks:
			for link_path in symlinks:
				# Get file filters for this specific symlink
				symlink_name = link_path.name
				filters = config.get_file_filters_for_path(symlink_name)

				# Use glob patterns for symlinked directories/files
				reader_kwargs = {
					'recursive': True,
					'encoding': 'utf-8'
				}

				# Apply exclude globs if configured
				if filters['exclude']:
					reader_kwargs['exclude'] = filters['exclude']

				loaded_docs = SimpleDirectoryReader(str(link_path), **reader_kwargs).load_data(show_progress=True)

				# Apply include filtering
				filtered_docs = self._filter_documents_by_include_globs(loaded_docs, filters['include'])
				docs.extend(filtered_docs)

		# Load documents from files in the base directory
		if files:
			# Get file filters for the base directory (use special key "_base" or empty string)
			base_filters = config.get_file_filters_for_path('_base')

			if all(file.endswith(".json") for file in files):
				# Apply glob filtering to JSON files
				filtered_files = self._filter_files_by_globs(files, base_filters['include'], base_filters['exclude'])
				for file in filtered_files:
					docs.extend(JSONReader().load_data(input_file=str(files_path / file)))
			else:
				# Use glob patterns for regular files
				reader_kwargs = {
					'recursive': True,
					'encoding': 'utf-8'
				}

				# Apply exclude globs if configured
				if base_filters['exclude']:
					reader_kwargs['exclude'] = base_filters['exclude']

				loaded_docs = SimpleDirectoryReader(str(files_path), **reader_kwargs).load_data(show_progress=True)

				# Apply include filtering
				filtered_docs = self._filter_documents_by_include_globs(loaded_docs, base_filters['include'])
				docs.extend(filtered_docs)

		# If no documents are found, still create and persist an empty index.
		# This allows initializing a RAG with no documents without error.

		original_embed_model = Settings.embed_model
		Settings.embed_model = embed_model

		try:
			print(f"Creating index for {rag_name} with {len(docs)} documents")
			# VectorStoreIndex.from_documents([]) will create an empty index.
			index = VectorStoreIndex.from_documents(docs, show_progress=True)

			# Persist on disk (overwrite)
			persist_dir = self._INDICES_DIR / rag_name
			if persist_dir.exists():
				# remove previous index to avoid stale files
				for child in persist_dir.iterdir():
					child.unlink()
			else:
				persist_dir.mkdir(parents=True, exist_ok=True)

			index.storage_context.persist(persist_dir=str(persist_dir))

			print(f"Index created for {rag_name} with {len(docs)} documents, generating summary...")

			# Generate and save project summary
			summary_llm = OpenAI(
				api_key=OPENAI_API_KEY,
				model="o4-mini",
				reasoning_effort="high",
			)
			query_engine = index.as_query_engine(
				llm=summary_llm,
				response_mode=ResponseMode.COMPACT_ACCUMULATE,
				similarity_top_k=30,
			)

			summary_prompt = """
				Summarize the project based on the provided documents. Focus on key functionalities, architecture, and purpose. Pin any important information.
				Use markdown formatting, be exhaustive and complete.
			"""
			summary_response = query_engine.query(textwrap.dedent(summary_prompt).strip())
			summary_path = self._RESUMES_DIR / f'{rag_name}.md'
			summary_path.write_text(str(summary_response), encoding='utf-8')

			print(f"Generated and saved summary for {rag_name} at {summary_path}")

		finally:
			# Restore original embedding model
			Settings.embed_model = original_embed_model


	def create_symlink(self, rag_name: str, target_path: str, link_name: str) -> Path:
		"""
		Create a symbolic link in the RAG's document directory.

		:param rag_name: Name of the RAG instance
		:param target_path: Path to the target file or directory
		:param link_name: Name for the symbolic link
		:return: Path to the created symbolic link
		:raises FileNotFoundError: If target path doesn't exist
		:raises FileExistsError: If link name already exists
		"""
		files_path = self._FILES_DIR / rag_name
		files_path.mkdir(parents=True, exist_ok=True)

		target = Path(target_path)
		if not target.exists():
			raise FileNotFoundError(f'Target path "{target_path}" does not exist.')

		link_path = files_path / link_name
		if link_path.exists():
			raise FileExistsError(f'Link "{link_name}" already exists in RAG "{rag_name}".')

		# Create symbolic link
		if os.name == 'nt':  # Windows
			if target.is_dir():
				link_path.symlink_to(target, target_is_directory=True)
			else:
				link_path.symlink_to(target)
		else:  # Unix-like systems
			link_path.symlink_to(target)

		return link_path


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

		summary_path = self._RESUMES_DIR / f'{rag_name}.md'
		if summary_path.exists():
			summary_path.unlink()


	def get_rag_config(self, rag_name: str) -> RAGConfig:
		"""
		Get the configuration for a specific RAG.

		:param rag_name: Name of the RAG instance
		:return: RAGConfig instance
		"""
		return self._load_rag_config(rag_name)


	def list_files(self, rag_name: str) -> list[dict]:
		"""
		List all files and directories in the RAG's document directory.

		:param rag_name: Name of the RAG instance
		:return: List of file/directory info with name, type, and link target (if symlink)
		:raises FileNotFoundError: If the files directory doesn't exist
		"""
		files_path = self._FILES_DIR / rag_name
		if not files_path.exists():
			raise FileNotFoundError(f'Files directory for RAG "{rag_name}" not found.')

		items = []
		for item in files_path.iterdir():
			item_info = {
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
						file_count, total_size = self._get_dir_stats(resolved_target)
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
					file_count, total_size = self._get_dir_stats(item)
					item_info['file_count'] = file_count
					item_info['size'] = total_size
				else:
					try:
						item_info['size'] = item.stat().st_size
					except OSError:
						item_info['size'] = None

			items.append(item_info)

		return sorted(items, key=lambda x: (x['type'], x['name'].lower()))


	def list_rags(self) -> list[str]:
		"""
		Return every available RAG name.

		:return: List of RAG names (directory names under data/indices)
		"""
		return [p.name for p in self._INDICES_DIR.iterdir() if p.is_dir()]


	def get_agent(self, rag_name: str):
		"""
		Return a FunctionAgent for the given rag_name, with tools for local RAG, DuckDuckGo search, file read, and file list.
		"""
		config = self._load_rag_config(rag_name)

		summary_path = self._RESUMES_DIR / f'{rag_name}.md'
		project_summary = ''
		if summary_path.exists():
			project_summary = summary_path.read_text(encoding='utf-8')

		return get_agent(
			rag_name=rag_name,
			config=config,
			project_summary=project_summary,
			load_index=self._load_index,
		)


	def save_directory(self, rag_name: str, directory_name: str, directory_content: dict) -> Path:
		"""
		Save a directory structure to the RAG's document directory.

		:param rag_name: Name of the RAG instance
		:param directory_name: Name for the saved directory
		:param directory_content: Dictionary representing directory structure with file contents
		:return: Path to the saved directory
		"""
		files_path = self._FILES_DIR / rag_name
		files_path.mkdir(parents=True, exist_ok=True)

		dir_path = files_path / directory_name
		dir_path.mkdir(exist_ok=True)

		def _create_structure(base_path: Path, structure: dict):
			for name, content in structure.items():
				item_path = base_path / name
				if isinstance(content, dict):
					# It's a subdirectory
					item_path.mkdir(exist_ok=True)
					_create_structure(item_path, content)
				else:
					# It's a file
					item_path.write_bytes(content)

		_create_structure(dir_path, directory_content)
		return dir_path


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
		file_path.parent.mkdir(parents=True, exist_ok=True)
		file_path.write_bytes(content)
		return file_path

	def create_folder(self, rag_name: str, folder_name: str) -> Path:
		"""
		Create an empty folder in the RAG's document directory.

		:param rag_name: Name of the RAG instance
		:param folder_name: Name of the folder to create
		:return: Path to the created folder
		:raises FileExistsError: If the folder already exists
		"""
		files_path = self._FILES_DIR / rag_name
		files_path.mkdir(parents=True, exist_ok=True)

		folder_path = files_path / folder_name
		if folder_path.exists():
			raise FileExistsError(f'Folder "{folder_name}" already exists')

		folder_path.mkdir(parents=True, exist_ok=True)
		return folder_path


	def fetch_url_content(self, url: str) -> Document:
		"""
		Fetch content from a URL and convert it to a Document.

		:param url: The URL to fetch
		:return: Document with content and metadata
		:raises Exception: If fetching or conversion fails
		"""
		try:
			# Fetch the webpage
			headers = {
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
			}
			response = requests.get(url, headers=headers, timeout=30)
			response.raise_for_status()

			# Parse the HTML
			soup = BeautifulSoup(response.content, 'html.parser')

			# Remove script and style elements
			for script in soup(["script", "style"]):
				script.decompose()

			# Extract title
			title = soup.find('title')
			title_text = title.get_text().strip() if title else ''

			# Convert HTML to markdown
			h = html2text.HTML2Text()
			h.body_width = 0  # No line wrapping

			# Get the HTML content
			html_content = str(soup)
			markdown_content = h.handle(html_content)

			# Clean up the markdown content
			markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)  # Remove excessive newlines
			markdown_content = re.sub(r' {3,}', ' ', markdown_content)  # Remove excessive spaces

			# Create metadata
			parsed_url = urlparse(url)
			metadata = {
				'file_path': url,
				'url': url,
				'domain': parsed_url.netloc,
				'title': title_text,
				'source_type': 'web_page',
				'content_type': 'text/markdown'
			}

			# Create Document
			document = Document(
				text=markdown_content,
				metadata=metadata
			)

			return document

		except requests.RequestException as e:
			raise Exception(f"Failed to fetch URL {url}: {str(e)}")
		except Exception as e:
			raise Exception(f"Failed to process URL {url}: {str(e)}")


	def add_url_to_rag(self, rag_name: str, url: str) -> None:
		"""
		Add a URL as a document to a RAG index.

		:param rag_name: Name of the RAG instance
		:param url: The URL to add
		:raises Exception: If fetching or processing fails
		"""
		# Fetch and convert the URL to a document
		document = self.fetch_url_content(url)

		# Load or create configuration for this RAG
		config = self._load_rag_config(rag_name)

		# Configure embedding model for this specific RAG
		embed_model = OpenAIEmbedding(
			api_key=OPENAI_API_KEY,
			model=config.embedding_model,
		)

		# Load existing index or create new one
		try:
			index = self._load_index(rag_name)
		except FileNotFoundError:
			# Create new index if it doesn't exist
			index = VectorStoreIndex.from_documents([])

		# Add the new document to the index
		original_embed_model = Settings.embed_model
		Settings.embed_model = embed_model

		try:
			index.insert(document)

			# Persist the updated index
			persist_dir = self._INDICES_DIR / rag_name
			persist_dir.mkdir(parents=True, exist_ok=True)
			index.storage_context.persist(persist_dir=str(persist_dir))

		finally:
			# Restore original embedding model
			Settings.embed_model = original_embed_model


	def remove_url_from_rag(self, rag_name: str, url: str) -> None:
		"""
		Remove a URL document from a RAG index.

		:param rag_name: Name of the RAG instance
		:param url: The URL to remove
		:raises Exception: If removal fails
		"""
		try:
			index = self._load_index(rag_name)
			persist_dir = self._INDICES_DIR / rag_name
			# Get all documents from the index that match the URL
			for doc in index.docstore.docs.values():
				if isinstance(doc, Document) and doc.metadata.get('url') == url:
					index.delete_ref_doc(doc.id_, True)

			# Persist the updated index
			index.storage_context.persist(persist_dir=str(persist_dir))

		except FileNotFoundError:
			raise Exception(f"RAG '{rag_name}' not found")


	def list_urls_in_rag(self, rag_name: str) -> list[dict]:
		"""
		List all URLs in a RAG index.

		:param rag_name: Name of the RAG instance
		:return: List of URL documents with metadata
		:raises Exception: If listing fails
		"""
		try:
			index = self._load_index(rag_name)

			# Get all documents from the index
			documents = []
			for node in index.docstore.docs.values():
				if hasattr(node, 'metadata') and node.metadata.get('source_type') == 'web_page':
					documents.append({
						'url': node.metadata.get('url', ''),
						'title': node.metadata.get('title', ''),
						'domain': node.metadata.get('domain', ''),
						'content_type': node.metadata.get('content_type', '')
					})

			return documents

		except FileNotFoundError:
			raise Exception(f"RAG '{rag_name}' not found")


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


	def generate_system_prompt(self, description: str) -> str:
		"""
		Generate a system prompt based on a description.

		:param description: Description of the desired role or expertise
		:return: Generated system prompt
		"""
		# Use OpenAI to generate a system prompt based on the description
		client = openai.OpenAI(api_key=OPENAI_API_KEY)

		prompt = f"""You are an expert in writing system prompts for AI assistants.

Here is a description of a desired role for an AI assistant:
"{description}"

Generate a professional and detailed system prompt that clearly defines the role, expertise, and expected behavior of the assistant. The prompt should:

1. Clearly define the assistant's identity and expertise
2. Specify the communication style (formal, casual, technical, etc.)
3. Indicate the types of tasks the assistant can perform
4. Mention the expected level of detail in responses
5. Include guidelines on how to structure responses
6. Be written in English and be professional

Respond only with the generated system prompt, without additional explanations."""

		try:
			response = client.chat.completions.create(
				model='gpt-4.1-mini',
				messages=[
					{'role': 'system', 'content': 'You are an expert in writing system prompts.'},
					{'role': 'user', 'content': prompt}
				],
				max_tokens=500,
				temperature=0.7
			)

			content = response.choices[0].message.content
			return content.strip() if content else f"You are an AI assistant specialized in {description}. You can help with questions and tasks related to this domain."
		except Exception as e:
			# Fallback to a basic prompt if OpenAI call fails
			return f"You are an AI assistant specialized in {description}. You can help with questions and tasks related to this domain."


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
			return load_index_from_storage(storage_context, use_async=True)  # type: ignore[attr-defined]
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

	def _get_dir_stats(self, path: Path) -> tuple[int, int]:
		"""Return (file_count, total_size) for all files under path recursively."""
		file_count = 0
		total_size = 0
		for f in path.rglob('*'):
			if f.is_file():
				file_count += 1
				try:
					total_size += f.stat().st_size
				except OSError:
					pass
		return file_count, total_size

	def _filter_files_by_globs(self, files: list[str], include_globs: list[str], exclude_globs: list[str]) -> list[str]:
		"""
		Filter files list based on include and exclude glob patterns.
		If a file matches any exclude pattern, it is excluded. Otherwise, it is included
		if it matches any include pattern. If include_globs is ["**/*"], all files not excluded are included.

		:param files: List of file names to filter
		:param include_globs: List of glob patterns to include (files must match at least one). Defaults to ['**/*'] if not specified in config.
		:param exclude_globs: List of glob patterns to exclude. Defaults to [] if not specified in config.
		:return: Filtered list of file names
		"""
		import fnmatch

		filtered_files = []

		for file in files:
			# Check if file should be excluded
			excluded = False
			for exclude_pattern in exclude_globs:
				if fnmatch.fnmatch(file, exclude_pattern):
					excluded = True
					break

			if excluded:
				continue

			# Check if file should be included
			included = False
			for include_pattern in include_globs:
				if fnmatch.fnmatch(file, include_pattern):
					included = True
					break

			if included:
				filtered_files.append(file)

		return filtered_files

	def _filter_documents_by_include_globs(self, documents: list[Document], include_globs: list[str]) -> list[Document]:
		"""
		Filter documents list based on include glob patterns applied to their file paths.
		Documents are included if their file path or file name matches any include pattern.
		If include_globs is ["**/*"], all documents are included.

		:param documents: List of Document objects to filter
		:param include_globs: List of glob patterns to include (documents must match at least one). Defaults to ['**/*'] if not specified in config.
		:return: Filtered list of Document objects
		"""
		import fnmatch
		from pathlib import Path

		filtered_docs = []

		for doc in documents:
			# Get the file path from document metadata
			file_path = doc.metadata.get('file_path', '')
			if file_path:
				# Get just the filename for pattern matching
				file_name = Path(file_path).name

				# Check if file should be included
				included = False
				for include_pattern in include_globs:
					if fnmatch.fnmatch(file_name, include_pattern) or fnmatch.fnmatch(file_path, include_pattern):
						included = True
						break

				if included:
					filtered_docs.append(doc)

		return filtered_docs

	async def async_agent_stream(self, rag_name: str, query: str, history: list[ChatMessage] | None = None) -> AsyncGenerator[StreamEvent, None]:
		"""
		Stream agent events in real-time including tokens, sources, and documents.
		Ultra-robust streaming system with clear separation between text tokens and structured events.

		:param rag_name: Name of the RAG instance to query
		:param query: The user's query
		:param history: Optional conversation history
		:yield: Typed streaming events (tokens, sources, documents, chat_history, final)
		"""
		agent = self.get_agent(rag_name)
		history = history or []
		sources: list[SearchResultItem] = []
		documents: list[DocumentItem] = []
		chat_history: list[ChatMessage] = history[:]

		handler = agent.run(query, chat_history=history)
		async for event in handler.stream_events():
			# Stream text tokens - simple and clean, no filtering needed
			if hasattr(event, 'delta') and event.delta:
				token_content = str(event.delta)
				# Send as proper typed event
				token_event: TokenStreamEvent = {'type': 'token', 'data': token_content}
				yield token_event

			# Handle tool results as structured events
			if isinstance(event, ToolCallResult):
				print(f"Tool call: {event.tool_name}, params: {event.tool_kwargs}")

				if event.tool_name.startswith('search'):
					new_sources = event.tool_output.raw_output
					if isinstance(new_sources, dict) and 'content' in new_sources and 'urls' in new_sources:
						sources.append(new_sources)  # type: ignore
						sources_event: SourcesStreamEvent = {'type': 'sources', 'data': new_sources}  # type: ignore
						yield sources_event
					else:
						print(f"Warning: Invalid search result format: {new_sources}")

				elif 'rag' in event.tool_name:
					new_documents = event.tool_output.raw_output
					if isinstance(new_documents, list):
						valid_documents = []
						for doc in new_documents:
							if isinstance(doc, dict) and 'content' in doc and 'source' in doc:
								valid_documents.append(doc)  # type: ignore
							else:
								print(f"Warning: Invalid document format: {doc}")
						documents.extend(valid_documents)  # type: ignore
						if valid_documents:
							documents_event: DocumentsStreamEvent = {'type': 'documents', 'data': valid_documents}  # type: ignore
							yield documents_event
					else:
						print(f"Warning: Invalid documents format: {new_documents}")

				elif event.tool_name == 'read_file_tool':
					file_path = event.tool_kwargs.get('rel_path', 'unknown')
					file_content = event.tool_output.raw_output

					success = not file_content.startswith('File not found:') and not file_content.startswith('Error reading file:')
					error = None if success else file_content

					read_file_result: FileReadResult = {
						'content': file_content if success else '',
						'file_path': file_path,
						'success': success,
						'error': error
					}

					read_file_event: ReadFileStreamEvent = {'type': 'read_file', 'data': read_file_result}
					yield read_file_event

				elif event.tool_name == 'list_files_tool':
					dir_path = event.tool_kwargs.get('rel_dir', 'unknown')
					file_list = event.tool_output.raw_output

					success = not (isinstance(file_list, list) and len(file_list) == 1 and file_list[0].startswith('Directory not found:'))
					error = None if success else (file_list[0] if isinstance(file_list, list) and len(file_list) == 1 else 'Unknown error')

					list_files_result: FileListResult = {
						'files': file_list if success else [],
						'directory_path': dir_path,
						'success': success,
						'error': error
					}

					list_files_event: ListFilesStreamEvent = {'type': 'list_files', 'data': list_files_result}
					yield list_files_event

			# Handle chat history updates
			if isinstance(event, AgentOutput):
				chat_history.append(event.response)
				chat_data = event.response.model_dump()
				if isinstance(chat_data, dict) and 'role' in chat_data and 'content' in chat_data:
					stream_chat_item: ChatHistoryItem = {
						'content': str(chat_data['content']),
						'role': chat_data['role'] if chat_data['role'] in ['user', 'assistant'] else 'assistant'
					}
					chat_event: ChatHistoryStreamEvent = {'type': 'chat_history', 'data': stream_chat_item}
					yield chat_event

		# Final summary event with all collected data
		chat_history_items: list[ChatHistoryItem] = []
		for msg in chat_history:
			msg_data = msg.model_dump()
			if isinstance(msg_data, dict) and 'role' in msg_data and 'content' in msg_data:
				final_chat_item: ChatHistoryItem = {
					'content': str(msg_data['content']),
					'role': msg_data['role'] if msg_data['role'] in ['user', 'assistant'] else 'assistant'
				}
				chat_history_items.append(final_chat_item)

		final_event: FinalStreamEvent = {
			'type': 'final',
			'data': {
				'chat_history': chat_history_items,
				'documents': documents,
				'sources': sources
			}
		}
		yield final_event

	def _is_json_object(self, text: str) -> bool:
		"""
		Simple check for complete JSON objects only.
		Only filters obvious complete JSON, preserving all other content.
		This method is now unused but kept for compatibility.
		"""
		if not text or not text.strip():
			return False

		text = text.strip()

		# Only filter complete JSON objects that parse successfully
		if (text.startswith('{') and text.endswith('}')) or (text.startswith('[') and text.endswith(']')):
			try:
				json.loads(text)
				return True
			except:
				return False


		return False
