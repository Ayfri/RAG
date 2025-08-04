import type { ToolActivity, StreamEvent, FileReadResult, FileListResult } from '$lib/types.d.ts';

export interface ContentPart {
	type: 'text' | 'tool';
	content: string;
	activity?: ToolActivity;
}

export interface ParsedMessage {
	content: string;
	contentParts: ContentPart[];
	toolActivities: ToolActivity[];
	documents?: any[];
	sources?: any[];
	fileLists?: FileListResult[];
}

export class AgenticStreamingParser {
	private buffer = '';
	private currentTextContent = '';
	private contentParts: ContentPart[] = [];
	private toolActivities: ToolActivity[] = [];
	private documents: any[] = [];
	private sources: any[] = [];
	private fileLists: FileListResult[] = [];

	/**
	 * Process a chunk of streaming data
	 * @param chunk - The text chunk received from the stream
	 * @returns Updated message data
	 */
	processChunk(chunk: string): ParsedMessage {
		this.buffer += chunk;

		// Process any complete events in the buffer (look for ---eventtype--- patterns)
		while (this.buffer.includes('---')) {
			const eventStart = this.buffer.indexOf('---');

			// Extract any text tokens before the event and add as text part
			const textPart = this.buffer.slice(0, eventStart);
			if (textPart) {
				this.currentTextContent += textPart;
				this.updateTextPart();
			}

			// Find the end of the event marker (next ---)
			const eventLineEnd = this.buffer.indexOf('---', eventStart + 3);
			if (eventLineEnd === -1) break; // Incomplete event marker

			const eventType = this.buffer.slice(eventStart + 3, eventLineEnd); // Extract event type

			// Find the start of JSON data (after the closing ---)
			const jsonStart = eventLineEnd + 3;

			// Find the end of the JSON data (next event or end of buffer)
			const nextEventStart = this.buffer.indexOf('\n---', jsonStart);
			const jsonEnd = nextEventStart !== -1 ? nextEventStart : this.buffer.length;
			const jsonPart = this.buffer.slice(jsonStart, jsonEnd).trim();

			if (jsonPart) {
				try {
					const eventData = JSON.parse(jsonPart);
					this.processEvent(eventType, eventData);
				} catch (e) {
					console.warn('Failed to parse event JSON:', e);
				}
			}

			// Remove the processed part from buffer
			this.buffer = this.buffer.slice(jsonEnd);
		}

		// Update content with any remaining text tokens (but ignore JSON at the end)
		if (this.buffer && !this.buffer.includes('---')) {
			const trimmedBuffer = this.buffer.trim();
			const looksLikeJson = (
				(trimmedBuffer.startsWith('{') && trimmedBuffer.endsWith('}')) ||
				trimmedBuffer.includes('"chat_history"') ||
				trimmedBuffer.includes('"documents"') ||
				trimmedBuffer.includes('"sources"') ||
				trimmedBuffer.includes('"files"') ||
				trimmedBuffer.includes('"file_path"') ||
				trimmedBuffer.includes('"directory_path"')
			);

			if (!looksLikeJson) {
				this.currentTextContent += this.buffer;
				this.updateTextPart();
				this.buffer = '';
			}
		}

		return this.getCurrentState();
	}

	/**
	 * Process the final buffer when streaming is complete
	 */
	finalize(): ParsedMessage {
		// Process any remaining text in buffer (but ignore JSON at the end)
		if (this.buffer.trim() && !this.buffer.includes('---')) {
			const trimmedBuffer = this.buffer.trim();
			const looksLikeJson = (
				(trimmedBuffer.startsWith('{') && trimmedBuffer.endsWith('}')) ||
				trimmedBuffer.includes('"chat_history"') ||
				trimmedBuffer.includes('"documents"') ||
				trimmedBuffer.includes('"sources"') ||
				trimmedBuffer.includes('"files"') ||
				trimmedBuffer.includes('"file_path"') ||
				trimmedBuffer.includes('"directory_path"')
			);

			if (!looksLikeJson) {
				this.currentTextContent += this.buffer;
				this.updateTextPart();
			}
		}

		return this.getCurrentState();
	}

	/**
	 * Process a specific streaming event
	 */
	private processEvent(eventType: string, eventData: any): void {
		switch (eventType) {
			case 'sources':
				// Add source activity inline at current position
				const sourceActivity: ToolActivity = {
					id: crypto.randomUUID(),
					type: 'sources',
					timestamp: new Date(),
					data: eventData
				};
				this.toolActivities.push(sourceActivity);
				this.contentParts.push({
					type: 'tool',
					content: '',
					activity: sourceActivity
				});
				break;

			case 'documents':
				// Add document activity inline at current position
				const docActivity: ToolActivity = {
					id: crypto.randomUUID(),
					type: 'documents',
					timestamp: new Date(),
					data: eventData
				};
				this.toolActivities.push(docActivity);
				this.contentParts.push({
					type: 'tool',
					content: '',
					activity: docActivity
				});
				break;

			case 'read_file':
				// Add file read activity inline at current position
				const readFileActivity: ToolActivity = {
					id: crypto.randomUUID(),
					type: 'read_file',
					timestamp: new Date(),
					data: eventData as FileReadResult
				};
				this.toolActivities.push(readFileActivity);
				this.contentParts.push({
					type: 'tool',
					content: '',
					activity: readFileActivity
				});
				break;

			case 'list_files':
				// Add file list activity inline at current position
				const listFilesActivity: ToolActivity = {
					id: crypto.randomUUID(),
					type: 'list_files',
					timestamp: new Date(),
					data: eventData as FileListResult
				};
				this.toolActivities.push(listFilesActivity);
				this.contentParts.push({
					type: 'tool',
					content: '',
					activity: listFilesActivity
				});
				// Also collect for final display
				this.fileLists.push(eventData as FileListResult);
				break;

			case 'final':
				// Update final data (backward compatibility) and don't display JSON
				if (eventData.documents) this.documents = eventData.documents;
				if (eventData.sources) this.sources = eventData.sources;
				// Mark as processed to avoid showing JSON at the end
				this.buffer = '';
				break;
		}
	}

	/**
	 * Update the text part in contentParts
	 */
	private updateTextPart(): void {
		// Remove existing text parts and add the updated one
		this.contentParts = [
			...this.contentParts.filter(p => p.type !== 'text'),
			{
				type: 'text',
				content: this.currentTextContent
			}
		];
	}

	/**
	 * Get the current state of the parsed message
	 */
	private getCurrentState(): ParsedMessage {
		return {
			content: this.currentTextContent,
			contentParts: this.contentParts,
			toolActivities: this.toolActivities,
			documents: this.documents.length > 0 ? this.documents : undefined,
			sources: this.sources.length > 0 ? this.sources : undefined,
			fileLists: this.fileLists.length > 0 ? this.fileLists : undefined
		};
	}

	/**
	 * Reset the parser state for a new message
	 */
	reset(): void {
		this.buffer = '';
		this.currentTextContent = '';
		this.contentParts = [];
		this.toolActivities = [];
		this.documents = [];
		this.sources = [];
		this.fileLists = [];
	}
}
