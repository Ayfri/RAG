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
	year: number;
}

export interface FileItem {

}
