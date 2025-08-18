// Shared types for RAG chat components

export interface SearchResultUrl {
	title: string;
	url: string;
}

export interface SearchResult {
	content: string;
	urls: SearchResultUrl[];
}

export interface RagDocument {
	content: string;
	source: string;
}

export interface OpenAIModel {
	id: string;
	name: string;
	created: string;
	is_reasoning: boolean;
	year: number;
}

export interface FileItem {
	name: string;
	type: 'file' | 'directory';
	is_symlink: boolean;
	target?: string;
	resolved_target_type?: 'file' | 'directory' | 'unknown';
	file_count?: number;
	size?: number;
	last_modified?: number;
}

// Agentic streaming events
export type StreamEventType = 'token' | 'sources' | 'documents' | 'read_file' | 'list_files' | 'chat_history' | 'tool_call' | 'final';

export interface StreamEventBase {
	type: StreamEventType;
}

export interface TokenStreamEvent extends StreamEventBase {
	type: 'token';
	data: string;
}

export interface SourcesStreamEvent extends StreamEventBase {
	type: 'sources';
	data: SearchResult;
}

export interface DocumentsStreamEvent extends StreamEventBase {
	type: 'documents';
	data: RagDocument[];
}

export interface ToolCallInfo {
	tool_name: string;
	params: Record<string, unknown>;
}

export interface ToolCallStreamEvent extends StreamEventBase {
	type: 'tool_call';
	data: ToolCallInfo;
}

export interface ReadFileStreamEvent extends StreamEventBase {
	type: 'read_file';
	data: FileReadResult;
}

export interface ListFilesStreamEvent extends StreamEventBase {
	type: 'list_files';
	data: FileListResult;
}

export interface ChatHistoryItem {
	content: string;
	role: 'user' | 'assistant';
}

export interface ChatHistoryStreamEvent extends StreamEventBase {
	type: 'chat_history';
	data: ChatHistoryItem;
}

export interface FinalStreamEventData {
	chat_history: ChatHistoryItem[];
	documents: RagDocument[];
	sources: SearchResult[];
}

export interface FinalStreamEvent extends StreamEventBase {
	type: 'final';
	data: FinalStreamEventData;
}

export type StreamEvent = TokenStreamEvent | SourcesStreamEvent | DocumentsStreamEvent | ReadFileStreamEvent | ListFilesStreamEvent | ChatHistoryStreamEvent | ToolCallStreamEvent | FinalStreamEvent;

// Tool activity for inline display
export interface ToolActivity {
	id: string;
	type: 'sources' | 'documents' | 'read_file' | 'list_files' | 'chat_history' | 'tool_call';
	timestamp: Date;
	data: SearchResult | RagDocument[] | FileReadResult | FileListResult | ChatHistoryItem | ToolCallInfo;
	// tool-call specific metadata
	status?: 'running' | 'completed';
	startedAt?: Date;
	endedAt?: Date;
	durationMs?: number;
	toolName?: string;
	params?: Record<string, unknown>;
}

export interface FileReadResult {
	content: string;
	file_path: string;
	success: boolean;
	error?: string;
}

export interface FileListResult {
	files: string[];
	directory_path: string;
	success: boolean;
	error?: string;
}


export interface ChatMessage {
	content: string;
	contentParts?: Array<{ content: string; activity?: ToolActivity; type: 'text' | 'tool' }>;
	documents?: RagDocument[];
	fileLists?: FileListResult[];
	id: string;
	isError?: boolean;
	responseMs?: number;
	role: 'user' | 'assistant';
	sources?: SearchResult[];
	timestamp: Date;
	toolActivities?: ToolActivity[];
	ttftMs?: number;
}


// Rag config
export interface RagConfig {
	chat_model: string;
	embedding_model: string;
	system_prompt: string;
	file_filters?: Record<string, Record<string, string[]>>;
}
