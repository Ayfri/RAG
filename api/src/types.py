"""
Shared type definitions for the RAG API.

This module contains all TypedDict definitions and type aliases used across
the RAG service for consistent typing and better code organization.
"""

from typing import Literal, TypedDict


class ChatHistoryItem(TypedDict):
	"""
	Represents a single chat message in conversation history.

	:param content: The message content
	:param role: The role of the message sender
	"""
	content: str
	role: Literal['assistant', 'user']


class DocumentItem(TypedDict):
	"""
	Represents a document retrieved from the RAG index.

	:param content: The document content/text
	:param source: The source file path of the document
	"""
	content: str
	source: str


class SearchResultUrl(TypedDict):
	"""
	Represents a URL from web search results.

	:param title: The title of the web page
	:param url: The URL of the web page
	"""
	title: str
	url: str


class SearchResultItem(TypedDict):
	"""
	Represents a web search result.

	:param content: The search result content
	:param urls: List of related URLs
	"""
	content: str
	urls: list[SearchResultUrl]


type StreamEventType = Literal[
	'chat_history',
	'documents',
	'final',
	'list_files',
	'read_file',
	'sources',
	'tool_call',
	'token'
]


class StreamEventBase(TypedDict):
	"""
	Base structure for all streaming events.

	Concrete events include a discriminant 'type' field.
	"""


class TokenStreamEvent(StreamEventBase):
	"""
	Streaming event for text tokens.

	:param data: The text token
	:param type: Always 'token'
	"""
	data: str
	type: Literal['token']


class ToolCallInfo(TypedDict):
	"""
	Information about a tool invocation about to run.

	:param tool_name: Name of the tool being called
	:param params: Parameters provided to the tool
	"""
	params: dict[str, object]
	tool_name: str


class ToolCallStreamEvent(StreamEventBase):
	"""
	Streaming event emitted when the agent invokes a tool.

	:param data: Tool call information
	:param type: Always 'tool_call'
	"""
	data: ToolCallInfo
	type: Literal['tool_call']


class SourcesStreamEvent(StreamEventBase):
	"""
	Streaming event for search sources.

	:param data: The search result data
	:param type: Always 'sources'
	"""
	data: SearchResultItem
	type: Literal['sources']


class DocumentsStreamEvent(StreamEventBase):
	"""
	Streaming event for RAG documents.

	:param data: List of document items
	:param type: Always 'documents'
	"""
	data: list[DocumentItem]
	type: Literal['documents']


class FileReadResult(TypedDict):
	"""
	Result from reading a file.

	:param content: The file content
	:param file_path: Path to the file that was read
	:param success: Whether the operation was successful
	:param error: Error message if operation failed
	"""
	content: str
	file_path: str
	success: bool
	error: str | None


class ReadFileStreamEvent(StreamEventBase):
	"""
	Streaming event for file read operations.

	:param data: File read result
	:param type: Always 'read_file'
	"""
	data: FileReadResult
	type: Literal['read_file']


class FileListResult(TypedDict):
	"""
	Result from listing files in a directory.

	:param files: List of files in the directory
	:param directory_path: Path to the directory that was listed
	:param success: Whether the operation was successful
	:param error: Error message if operation failed
	"""
	files: list[str]
	directory_path: str
	success: bool
	error: str | None


class ListFilesStreamEvent(StreamEventBase):
	"""
	Streaming event for file listing operations.

	:param data: File list result
	:param type: Always 'list_files'
	"""
	data: FileListResult
	type: Literal['list_files']


class ChatHistoryStreamEvent(StreamEventBase):
	"""
	Streaming event for chat history updates.

	:param data: Chat history item
	:param type: Always 'chat_history'
	"""
	data: ChatHistoryItem
	type: Literal['chat_history']


class FinalStreamEventData(TypedDict):
	"""
	Data structure for the final streaming event.

	:param chat_history: Complete conversation history
	:param documents: All retrieved documents
	:param sources: All search sources
	"""
	chat_history: list[ChatHistoryItem]
	documents: list[DocumentItem]
	sources: list[SearchResultItem]


class FinalStreamEvent(StreamEventBase):
	"""
	Final streaming event with complete session data.

	:param data: Complete session data
	:param type: Always 'final'
	"""
	data: FinalStreamEventData
	type: Literal['final']


type StreamEvent = (
	ChatHistoryStreamEvent |
	DocumentsStreamEvent |
	FinalStreamEvent |
	ListFilesStreamEvent |
	ReadFileStreamEvent |
	SourcesStreamEvent |
	ToolCallStreamEvent |
	TokenStreamEvent
)
