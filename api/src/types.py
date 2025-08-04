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


StreamEventType = Literal[
	'chat_history',
	'documents',
	'final',
	'sources',
	'token'
]


class StreamEventBase(TypedDict):
	"""
	Base structure for all streaming events.

	:param type: The type of streaming event
	"""
	type: StreamEventType


class TokenStreamEvent(StreamEventBase):
	"""
	Streaming event for text tokens.

	:param data: The text token
	:param type: Always 'token'
	"""
	data: str
	type: Literal['token']


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


StreamEvent = (
	ChatHistoryStreamEvent |
	DocumentsStreamEvent |
	FinalStreamEvent |
	SourcesStreamEvent |
	TokenStreamEvent
)
