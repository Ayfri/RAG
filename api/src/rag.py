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
import time
from pathlib import Path
import textwrap
from typing import AsyncGenerator
from urllib.parse import urlparse

import openai
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex, Settings, load_index_from_storage
from llama_index.core.agent.workflow import AgentOutput, ToolCallResult
from llama_index.core.llms import ChatMessage
from llama_index.core.readers.json import JSONReader
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.schema import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

import html2text
import requests
from bs4 import BeautifulSoup

from typing import Any, cast

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
	_FILES_DIR = Path('data/files')
	_INDICES_DIR = Path('data/indices')
	_CONFIGS_DIR = Path('data/configs')
	_RESUMES_DIR = Path('data/resumes')


	def __init__(self):
		self._FILES_DIR.mkdir(parents=True, exist_ok=True)
		self._INDICES_DIR.mkdir(parents=True, exist_ok=True)
		self._CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
		self._RESUMES_DIR.mkdir(parents=True, exist_ok=True)


	async def async_agent_stream(self, rag_name: str, query: str, history: list[ChatMessage] | None = None) -> AsyncGenerator[StreamEvent, None]:
		"""
		Stream agent events in real-time including tokens, sources, and documents.
		Handles tool calls, chat history updates, and final summary events.
		"""
		agent = self.get_agent(rag_name)
		history = history or []
		sources: list[SearchResultItem] = []
		documents: list[DocumentItem] = []
		chat_history: list[ChatMessage] = history[:]

		handler = agent.run(query, chat_history=history)
		async for event in handler.stream_events():
			if hasattr(event, 'delta') and event.delta:
				token_content = str(event.delta)
				token_event: TokenStreamEvent = {'type': 'token', 'data': token_content}
				yield token_event

			if isinstance(event, ToolCallResult):
				print(f"Tool call: {event.tool_name}, params: {event.tool_kwargs}")

				if event.tool_name.startswith('search'):
					new_sources = event.tool_output.raw_output
					if isinstance(new_sources, dict) and 'content' in new_sources and 'urls' in new_sources:
						validated_source: SearchResultItem = cast(SearchResultItem, new_sources)
						sources.append(validated_source)
						sources_event: SourcesStreamEvent = {'type': 'sources', 'data': validated_source}
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


	def add_url_to_rag(self, rag_name: str, url: str) -> None:
		"""Add a URL as a document to a RAG index."""
		existing_urls = self.list_urls_in_rag(rag_name)
		for existing_url in existing_urls:
			if existing_url['url'] == url:
				raise Exception(f"URL '{url}' already exists in RAG '{rag_name}'")

		document = self.fetch_url_content(url)
		config = self._load_rag_config(rag_name)
		embed_model = OpenAIEmbedding(
			api_key=OPENAI_API_KEY,
			model=config.embedding_model,
		)

		try:
			index = self._load_index(rag_name)
		except FileNotFoundError:
			index = VectorStoreIndex.from_documents([])

		original_embed_model = Settings.embed_model
		Settings.embed_model = embed_model

		try:
			index.insert(document)
			self.save(rag_name, index)
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


	def create_rag(self, rag_name: str) -> None:
		"""
		Create or recreate an index from documents in data/files/<rag_name>/.
		Handles symlinks, file filtering, and generates project summary.
		"""
		files_path = self._FILES_DIR / rag_name
		files_path.mkdir(parents=True, exist_ok=True)

		config = self._load_rag_config(rag_name)
		embed_model = OpenAIEmbedding(
			api_key=OPENAI_API_KEY,
			model=config.embedding_model,
		)

		docs: list[Document] = []
		files = self.get_files(files_path)
		symlinks = self.get_symlinks(files_path)

		# Also include previously saved web URLs so reindexing keeps them
		try:
			existing_index = self._load_index(rag_name)
			for node in existing_index.docstore.docs.values():
				if node.metadata.get('source_type') == 'web_page':
					text = getattr(node, 'text', '')
					if text:
						docs.append(Document(text=text, metadata=node.metadata))
		except FileNotFoundError:
			pass

		if symlinks:
			for link_path in symlinks:
				symlink_name = link_path.name
				filters = config.get_file_filters_for_path(symlink_name)
				loaded_docs = SimpleDirectoryReader(
					input_dir=str(link_path),
					exclude=filters['exclude'] or None,
					recursive=True,
					encoding='utf-8'
				).load_data(show_progress=True)
				filtered_docs = self._filter_documents_by_include_globs(loaded_docs, filters['include'])
				docs.extend(filtered_docs)

		if files:
			base_filters = config.get_file_filters_for_path('_base')
			if all(file.endswith(".json") for file in files):
				filtered_files = self._filter_files_by_globs(files, base_filters['include'], base_filters['exclude'])
				for file in filtered_files:
					docs.extend(JSONReader().load_data(input_file=str(files_path / file)))
			else:
				loaded_docs = SimpleDirectoryReader(
					input_dir=str(files_path),
					exclude=base_filters['exclude'] or None,
					recursive=True,
					encoding='utf-8'
				).load_data(show_progress=True)
				filtered_docs = self._filter_documents_by_include_globs(loaded_docs, base_filters['include'])
				docs.extend(filtered_docs)

		original_embed_model = Settings.embed_model
		Settings.embed_model = embed_model

		try:
			print(f"Creating index for {rag_name} with {len(docs)} documents")
			index = VectorStoreIndex.from_documents(docs, show_progress=True)
			self.save(rag_name, index)
			print(f"Index created for {rag_name} with {len(docs)} documents")

			if len(docs) > 0:
				print("Generating summary...")
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
			else:
				# If there are no local files/symlinks but URLs exist in the existing index, generate summary from that index
				try:
					existing_index = self._load_index(rag_name)
					if existing_index.docstore.docs:
						print("Generating summary from existing URL documents...")
						summary_llm = OpenAI(
							api_key=OPENAI_API_KEY,
							model="o4-mini",
							reasoning_effort="high",
						)
						query_engine = existing_index.as_query_engine(
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
					else:
						print("No documents found, skipping summary generation")
				except FileNotFoundError:
					print("No documents found, skipping summary generation")
		finally:
			Settings.embed_model = original_embed_model


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


	def delete_rag(self, rag_name: str) -> None:
		"""Delete a RAG index and all its associated files."""
		index_path = self._INDICES_DIR / rag_name
		files_path = self._FILES_DIR / rag_name
		config_path = self._CONFIGS_DIR / f'{rag_name}.json'

		if not index_path.exists():
			raise FileNotFoundError(f'RAG "{rag_name}" not found.')

		if index_path.exists():
			for child in index_path.rglob('*'):
				if child.is_file():
					child.unlink()
			index_path.rmdir()

		if files_path.exists():
			for child in files_path.rglob('*'):
				if child.is_file():
					child.unlink()
			files_path.rmdir()

		if config_path.exists():
			config_path.unlink()

		summary_path = self._RESUMES_DIR / f'{rag_name}.md'
		if summary_path.exists():
			summary_path.unlink()


	def fetch_url_content(self, url: str) -> Document:
		"""
		Fetch content from a URL and convert it to a Document.
		Handles HTML parsing, markdown conversion, and metadata extraction.
		"""
		try:
			parsed_url = urlparse(url)
			if not parsed_url.scheme or not parsed_url.netloc:
				raise Exception(f"Invalid URL format: {url}")
		except Exception:
			raise Exception(f"Invalid URL: {url}")

		try:
			with requests.Session() as session:
				session.headers.update({
					'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
					'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
					'Accept-Language': 'en-US,en;q=0.5',
					'Accept-Encoding': 'gzip, deflate',
					'Connection': 'keep-alive',
					'Upgrade-Insecure-Requests': '1',
				})

				timeout = (10, 30)
				max_retries = 3
				retry_delay = 1

				response: requests.Response | None = None
				for attempt in range(max_retries):
					try:
						response = session.get(
							url,
							timeout=timeout,
							allow_redirects=True,
							verify=True
						)
						response.raise_for_status()
						break

					except requests.exceptions.Timeout as e:
						if attempt == max_retries - 1:
							raise Exception(f"Request timeout after {max_retries} attempts: {url}")
						time.sleep(retry_delay * (attempt + 1))
						continue

					except requests.exceptions.ConnectionError as e:
						if attempt == max_retries - 1:
							raise Exception(f"Connection failed after {max_retries} attempts: {url}")
						time.sleep(retry_delay * (attempt + 1))
						continue

					except requests.exceptions.RequestException as e:
						raise e

				if response is None:
					raise Exception(f"No response received from {url}")

				content_type = response.headers.get('content-type', '').lower()
				if not any(ct in content_type for ct in ['text/html', 'text/plain', 'application/xhtml+xml']):
					raise Exception(f"Unsupported content type: {content_type}")

				content_length = response.headers.get('content-length')
				if content_length and int(content_length) > 10 * 1024 * 1024:
					raise Exception(f"Content too large: {content_length} bytes")

				soup = BeautifulSoup(response.content, 'html.parser')

			for script in soup(["script", "style"]):
				script.decompose()

			title = soup.find('title')
			title_text = title.get_text().strip() if title else ''

			h = html2text.HTML2Text()
			h.body_width = 0

			html_content = str(soup)
			markdown_content = h.handle(html_content)

			markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
			markdown_content = re.sub(r' {3,}', ' ', markdown_content)
			markdown_content = markdown_content.strip()

			metadata = {
				'file_path': url,
				'url': url,
				'domain': parsed_url.netloc,
				'title': title_text,
				'source_type': 'web_page',
				'content_type': 'text/markdown',
				'content_length': len(markdown_content),
				'response_status': response.status_code,
				'response_headers': dict(response.headers)
			}

			document = Document(
				text=markdown_content,
				metadata=metadata
			)

			return document

		except requests.exceptions.HTTPError as e:
			if e.response.status_code == 404:
				raise Exception(f"URL not found (404): {url}")
			elif e.response.status_code == 403:
				raise Exception(f"Access forbidden (403): {url}")
			elif e.response.status_code == 401:
				raise Exception(f"Unauthorized access (401): {url}")
			elif e.response.status_code >= 500:
				raise Exception(f"Server error ({e.response.status_code}): {url}")
			else:
				raise Exception(f"HTTP error {e.response.status_code}: {url}")
		except requests.exceptions.ConnectionError:
			raise Exception(f"Connection failed: {url}")
		except requests.exceptions.Timeout:
			raise Exception(f"Request timeout: {url}")
		except requests.exceptions.RequestException as e:
			raise Exception(f"Failed to fetch URL {url}: {str(e)}")
		except Exception as e:
			raise Exception(f"Failed to process URL {url}: {str(e)}")


	def generate_system_prompt(self, description: str) -> str:
		"""Generate a system prompt based on a description using OpenAI."""
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
			return f"You are an AI assistant specialized in {description}. You can help with questions and tasks related to this domain."


	def get_agent(self, rag_name: str):
		"""Return a FunctionAgent for the given rag_name with tools for local RAG, search, file read, and file list."""
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


	def get_files(self, input_path: Path) -> list[str]:
		"""Return list of file names (not directories or symlinks) in input_path."""
		return [f.name for f in input_path.iterdir() if f.is_file() and not f.is_symlink()]


	def get_rag_config(self, rag_name: str) -> RAGConfig:
		"""Get the configuration for a specific RAG."""
		return self._load_rag_config(rag_name)


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
		"""Return every available RAG name."""
		return [p.name for p in self._INDICES_DIR.iterdir() if p.is_dir()]


	def list_urls_in_rag(self, rag_name: str) -> list[dict]:
		"""List all URLs in a RAG index."""
		try:
			index = self._load_index(rag_name)
			documents = []
			seen_urls: set[str] = set()

			for node in index.docstore.docs.values():
				if node.metadata.get('source_type') == 'web_page':
					url = node.metadata.get('url', '')
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


	def remove_url_from_rag(self, rag_name: str, url: str) -> None:
		"""Remove a URL document from a RAG index."""
		try:
			index = self._load_index(rag_name)

			deleted_count = 0
			for doc_id, doc in index.docstore.docs.items():
				if doc.metadata.get('url') == url:
					index.delete_ref_doc(doc_id, delete_from_docstore=True)
					index.delete_nodes([doc.node_id], delete_from_docstore=True)
					deleted_count += 1

			if deleted_count == 0:
				raise Exception(f"URL '{url}' not found in RAG '{rag_name}'")

			self.save(rag_name, index)

		except FileNotFoundError:
			raise Exception(f"RAG '{rag_name}' not found")


	def save(self, rag_name: str, index: VectorStoreIndex) -> None:
		"""Save index to disk."""
		persist_dir = self._INDICES_DIR / rag_name
		if persist_dir.exists():
			for child in persist_dir.iterdir():
				child.unlink()
		else:
			persist_dir.mkdir(parents=True, exist_ok=True)
		index.storage_context.persist(persist_dir=str(persist_dir))


	def save_directory(self, rag_name: str, directory_name: str, directory_content: dict) -> Path:
		"""Save a directory structure to the RAG's document directory."""
		files_path = self._FILES_DIR / rag_name
		files_path.mkdir(parents=True, exist_ok=True)

		dir_path = files_path / directory_name
		dir_path.mkdir(exist_ok=True)

		def _create_structure(base_path: Path, structure: dict):
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


	def update_rag_config(self, rag_name: str, config: RAGConfig) -> None:
		"""Update the configuration for a specific RAG."""
		index_path = self._INDICES_DIR / rag_name
		if not index_path.exists():
			raise FileNotFoundError(f'RAG "{rag_name}" not found.')

		config_path = self._CONFIGS_DIR / f'{rag_name}.json'
		config_path.write_text(json.dumps(config.to_dict(), indent=2))


	def _filter_documents_by_include_globs(self, documents: list[Document], include_globs: list[str]) -> list[Document]:
		"""Filter documents list based on include glob patterns applied to their file paths."""
		import fnmatch
		from pathlib import Path

		filtered_docs = []

		for doc in documents:
			file_path = doc.metadata.get('file_path', '')
			if file_path:
				file_name = Path(file_path).name

				included = False
				for include_pattern in include_globs:
					if fnmatch.fnmatch(file_name, include_pattern) or fnmatch.fnmatch(file_path, include_pattern):
						included = True
						break

				if included:
					filtered_docs.append(doc)

		return filtered_docs


	def _filter_files_by_globs(self, files: list[str], include_globs: list[str], exclude_globs: list[str]) -> list[str]:
		"""Filter files list based on include and exclude glob patterns."""
		import fnmatch

		filtered_files = []

		for file in files:
			excluded = False
			for exclude_pattern in exclude_globs:
				if fnmatch.fnmatch(file, exclude_pattern):
					excluded = True
					break

			if excluded:
				continue

			included = False
			for include_pattern in include_globs:
				if fnmatch.fnmatch(file, include_pattern):
					included = True
					break

			if included:
				filtered_files.append(file)

		return filtered_files


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


	def _is_json_object(self, text: str) -> bool:
		"""Simple check for complete JSON objects only."""
		if not text or not text.strip():
			return False

		text = text.strip()

		if (text.startswith('{') and text.endswith('}')) or (text.startswith('[') and text.endswith(']')):
			try:
				json.loads(text)
				return True
			except:
				return False

		return False


	def _load_index(self, rag_name: str) -> VectorStoreIndex:
		"""Load a persisted RAG index from disk."""
		persist_dir = self._INDICES_DIR / rag_name
		if not persist_dir.exists():
			raise FileNotFoundError(f'No index found for RAG "{rag_name}".')

		config = self._load_rag_config(rag_name)
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
				config_data = json.loads(config_path.read_text())
				return RAGConfig.from_dict(config_data)
			except (json.JSONDecodeError, KeyError) as e:
				print(f'Warning: Invalid config file for RAG "{rag_name}": {e}. Using defaults.')

		default_config = RAGConfig()
		config_path.write_text(json.dumps(default_config.to_dict(), indent=2))
		return default_config
