"""
RAG related utilities built on top of LlamaIndex.

All indices and source documents are stored on the local filesystem:
- data/files/<rag_name>/ : raw files to embed
- data/indices/<rag_name>/ : vector indices & metadata
- data/configs/<rag_name>.json : configuration per RAG
"""

import textwrap
from pathlib import Path
from collections.abc import AsyncGenerator

import openai
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.agent.workflow import AgentOutput, ToolCall, ToolCallResult
from llama_index.core.llms import ChatMessage
from llama_index.core.readers.json import JSONReader
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.schema import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from typing import Any, cast

from src.agent import get_agent
from src.config import OPENAI_API_KEY
from src.document_manager import RAGDocumentManager
from src.logger import get_logger, log_step
from src.rag_config import RAGConfig
from src.utils import (
	filter_documents_by_include_globs,
	filter_files_by_globs
)
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
	ToolCallStreamEvent,
	FileReadResult,
	FileListResult
)

openai.api_key = OPENAI_API_KEY

logger = get_logger(__name__)


class RAGService:
	def __init__(self):
		# Initialize document manager - it handles its own directory setup
		self.document_manager = RAGDocumentManager()


	def add_url_to_rag(self, rag_name: str, url: str) -> None:
		"""Add a URL as a document to a RAG index."""
		config = self.document_manager.get_rag_config(rag_name)
		self.document_manager.add_url_to_rag(rag_name, url, config)


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

		# Diagnostics: track simple counters for visibility
		tokens_count = 0
		documents_events = 0
		sources_events = 0
		chat_events = 0

		logger.info(f"stream-start rag={rag_name} qlen={len(query)} history={len(history)}")

		handler = agent.run(query, chat_history=history)
		logger.debug(handler)
		async for event in handler.stream_events():
			logger.info(f"stream-event rag={rag_name} event={type(event)}")
			if hasattr(event, 'delta') and event.delta:
				token_content = str(event.delta)
				token_event: TokenStreamEvent = {'type': 'token', 'data': token_content}
				yield token_event
				tokens_count += 1

			if isinstance(event, ToolCall):
				safe_params = cast(dict[str, object], dict(getattr(event, 'tool_kwargs', {}) or {}))
				logger.info(f"tool-call rag={rag_name} tool={event.tool_name}, params={safe_params}")
				try:
					tool_event: ToolCallStreamEvent = {
						'type': 'tool_call',
						'data': {
							'tool_name': event.tool_name,
							'params': safe_params,
						}
					}
					yield tool_event
				except Exception as e:
					logger.warning(f"failed to emit tool_call event: {e}")

			if isinstance(event, ToolCallResult):
				try:
					if event.tool_name.startswith('search'):
						new_sources = event.tool_output.raw_output
						if isinstance(new_sources, dict) and 'content' in new_sources and 'urls' in new_sources:
							validated_source: SearchResultItem = cast(SearchResultItem, new_sources)
							sources.append(validated_source)
							sources_event: SourcesStreamEvent = {'type': 'sources', 'data': validated_source}
							yield sources_event
							sources_events += 1
						else:
							logger.warning(f"invalid search result format: {new_sources}")

					elif 'rag' in event.tool_name:
						new_documents = event.tool_output.raw_output
						if isinstance(new_documents, list):
							valid_documents = []
							for doc in new_documents:
								if isinstance(doc, dict) and 'content' in doc and 'source' in doc:
									valid_documents.append(doc)
								else:
									logger.warning(f"invalid document format: {doc}")
							documents.extend(valid_documents)
							if valid_documents:
								documents_event: DocumentsStreamEvent = {'type': 'documents', 'data': valid_documents}
								yield documents_event
								documents_events += 1
						else:
							logger.warning(f"invalid documents format: {new_documents}")

					elif event.tool_name == 'read_file_tool':
						file_path = cast(str, event.tool_kwargs.get('rel_path', 'unknown'))
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
						dir_path = cast(str, event.tool_kwargs.get('rel_dir', 'unknown'))
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
				except Exception as e:
					logger.exception(f"tool processing failed: {e}")

			if isinstance(event, AgentOutput):
				chat_history.append(event.response)
				chat_data = event.response.model_dump()
				if 'role' in chat_data and 'content' in chat_data:
					stream_chat_item: ChatHistoryItem = {
						'content': str(chat_data['content']),
						'role': chat_data['role'] if chat_data['role'] in ['user', 'assistant'] else 'assistant'
					}
					chat_event: ChatHistoryStreamEvent = {'type': 'chat_history', 'data': stream_chat_item}
					yield chat_event
					chat_events += 1

		if handler.is_done() and handler.exception():
			logger.error(f"stream failed rag={rag_name} error={handler.exception()}")

		chat_history_items: list[ChatHistoryItem] = []
		for msg in chat_history:
			msg_data = msg.model_dump()
			if 'role' in msg_data and 'content' in msg_data:
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
		if tokens_count == 0 and sources_events == 0 and documents_events == 0 and chat_events == 0:
			logger.warning(f"stream produced no tokens or tool/chat events for rag={rag_name}; check OpenAI API key, model availability, and index contents")
		logger.info(
			f"stream-end rag={rag_name} tokens={tokens_count} sources_events={sources_events} documents_events={documents_events} chat_events={chat_events} final_chat_items={len(chat_history_items)}"
		)


	def create_folder(self, rag_name: str, folder_name: str) -> Path:
		"""Create an empty folder in the RAG's document directory."""
		return self.document_manager.create_folder(rag_name, folder_name)


	def create_rag(self, rag_name: str) -> None:
		"""
		Create or recreate an index from documents in data/files/<rag_name>/.
		Handles symlinks, file filtering, and generates project summary.
		"""
		files_path = self.document_manager.files_dir / rag_name
		files_path.mkdir(parents=True, exist_ok=True)

		config = self.document_manager.get_rag_config(rag_name)
		embed_model = OpenAIEmbedding(
			api_key=OPENAI_API_KEY,
			model=config.embedding_model,
		)

		docs: list[Document] = []
		files = self.document_manager.get_files(files_path)
		symlinks = self.document_manager.get_symlinks(files_path)

		# Also include previously saved web URLs so reindexing keeps them
		try:
			existing_index = self.document_manager.load_index(rag_name)
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
				filtered_docs = filter_documents_by_include_globs(loaded_docs, filters['include'])
				docs.extend(filtered_docs)

		if files:
			base_filters = config.get_file_filters_for_path('_base')
			if all(file.endswith(".json") for file in files):
				filtered_files = filter_files_by_globs(files, base_filters['include'], base_filters['exclude'])
				for file in filtered_files:
					docs.extend(JSONReader().load_data(input_file=str(files_path / file)))
			else:
				loaded_docs = SimpleDirectoryReader(
					input_dir=str(files_path),
					exclude=base_filters['exclude'] or None,
					recursive=True,
					encoding='utf-8'
				).load_data(show_progress=True)
				filtered_docs = filter_documents_by_include_globs(loaded_docs, base_filters['include'])
				docs.extend(filtered_docs)

		original_embed_model = Settings.embed_model
		Settings.embed_model = embed_model

		try:
			with log_step(logger, f"create-index rag={rag_name} docs={len(docs)}"):
				index = VectorStoreIndex.from_documents(docs, show_progress=True)
				self.document_manager.save_index(rag_name, index)

			with log_step(logger, f"generate-summary rag={rag_name} from=index"):
				summary_llm = OpenAI(
					api_key=OPENAI_API_KEY,
					model="o4-mini",
					reasoning_effort="high",
				)
				summary_prompt = """
					Summarize the project based on the provided documents. Focus on key functionalities, architecture, and purpose. Pin any important information.
					Use markdown formatting, be exhaustive and complete.
				"""
				query_engine: BaseQueryEngine
				if len(docs) > 0:
					query_engine = index.as_query_engine(
						llm=summary_llm,
						response_mode=ResponseMode.COMPACT_ACCUMULATE,
						similarity_top_k=30,
					)
				else:
					# If there are no local files/symlinks but URLs exist in the existing index, generate summary from that index
					try:
						existing_index = self.document_manager.load_index(rag_name)
						if existing_index.docstore.docs:
							query_engine = existing_index.as_query_engine(
								llm=summary_llm,
								response_mode=ResponseMode.COMPACT_ACCUMULATE,
								similarity_top_k=30,
							)
						else:
							logger.info("no documents found, skipping summary generation")
							return
					except FileNotFoundError:
						logger.info("no documents found, skipping summary generation")
						return
				
				summary_response = query_engine.query(textwrap.dedent(summary_prompt).strip())
				self.document_manager.save_summary(rag_name, str(summary_response.response or ''))
		finally:
			Settings.embed_model = original_embed_model


	def create_symlink(self, rag_name: str, target_path: str, link_name: str) -> Path:
		"""Create a symbolic link in the RAG's document directory."""
		return self.document_manager.create_symlink(rag_name, target_path, link_name)


	def delete_file(self, rag_name: str, filename: str) -> None:
		"""Delete a specific file from the RAG's document directory."""
		self.document_manager.delete_file(rag_name, filename)


	def delete_rag(self, rag_name: str) -> None:
		"""Delete a RAG index and all its associated files."""
		index_path = self.document_manager.indices_dir / rag_name
		files_path = self.document_manager.files_dir / rag_name
		config_path = self.document_manager.configs_dir / f'{rag_name}.json'

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

		summary_path = self.document_manager.get_summary_path(rag_name)
		if summary_path.exists():
			summary_path.unlink()

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
			response = client.responses.create(
				model='gpt-5-mini',
				input=prompt,
				max_output_tokens=500,
				reasoning={
					"effort": "low",
				},
				text={
					"verbosity": "medium"
				}
			)

			return response.output_text.strip()
		except Exception as e:
			logger.exception(f"error generating system prompt: {e}")
			return f"You are an AI assistant specialized in {description}. You can help with questions and tasks related to this domain."


	def get_agent(self, rag_name: str):
		"""Return a FunctionAgent for the given rag_name with tools for local RAG, search, file read, and file list."""
		config = self.document_manager.get_rag_config(rag_name)
		summary_path = self.document_manager.get_summary_path(rag_name)
		project_summary = ''
		if summary_path.exists():
			project_summary = summary_path.read_text(encoding='utf-8')

		return get_agent(
			rag_name=rag_name,
			config=config,
			project_summary=project_summary,
			load_index=self.document_manager.load_index,
		)


	def get_files(self, input_path: Path) -> list[str]:
		"""Return list of file names (not directories or symlinks) in input_path."""
		return self.document_manager.get_files(input_path)


	def get_rag_config(self, rag_name: str) -> RAGConfig:
		"""Get the configuration for a specific RAG."""
		return self.document_manager.get_rag_config(rag_name)


	def get_symlinks(self, input_path: Path) -> list[Path]:
		"""Return list of symlink Paths in input_path."""
		return self.document_manager.get_symlinks(input_path)


	def list_files(self, rag_name: str) -> list[dict[str, Any]]:
		"""List all files and directories in the RAG's document directory with metadata."""
		return self.document_manager.list_files(rag_name)


	def list_rags(self) -> list[str]:
		"""Return every available RAG name."""
		return [p.name for p in self.document_manager.indices_dir.iterdir() if p.is_dir()]


	def list_urls_in_rag(self, rag_name: str) -> list[dict[str, str]]:
		"""List all URLs in a RAG index."""
		config = self.document_manager.get_rag_config(rag_name)
		return self.document_manager.list_urls_in_rag(rag_name, config)


	def remove_url_from_rag(self, rag_name: str, url: str) -> None:
		"""Remove a URL document from a RAG index."""
		config = self.document_manager.get_rag_config(rag_name)
		self.document_manager.remove_url_from_rag(rag_name, url, config)


	def save_directory(self, rag_name: str, directory_name: str, directory_content: dict[str, Any]) -> Path:
		"""Save a directory structure to the RAG's document directory."""
		return self.document_manager.save_directory(rag_name, directory_name, directory_content)


	def save_file(self, rag_name: str, filename: str, content: bytes) -> Path:
		"""Save a file to the RAG's document directory."""
		return self.document_manager.save_file(rag_name, filename, content)


	def update_rag_config(self, rag_name: str, config: RAGConfig) -> None:
		"""Update the configuration for a specific RAG."""
		self.document_manager.update_rag_config(rag_name, config)
