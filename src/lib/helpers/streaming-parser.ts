import type {FileListResult, StreamEvent, ToolActivity} from '$lib/types.d.ts';

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
	private currentTextContent = '';
	private contentParts: ContentPart[] = [];
	private toolActivities: ToolActivity[] = [];
	private documents: any[] = [];
	private sources: any[] = [];
	private fileLists: FileListResult[] = [];

	/**
	 * Ultra-robust streaming parser that works directly with typed events
	 * NO text parsing, NO markers, NO filtering - just pure event handling
	 */
	processEvent(event: StreamEvent): ParsedMessage {
		switch (event.type) {
			case 'token':
				// Pure text token - add directly to content
				this.currentTextContent += event.data;
				this.updateTextPart();
				break;

			case 'sources':
				const sourceActivity: ToolActivity = {
					id: crypto.randomUUID(),
					type: 'sources',
					timestamp: new Date(),
					data: event.data
				};
				this.toolActivities.push(sourceActivity);
				this.contentParts.push({
					type: 'tool',
					content: '',
					activity: sourceActivity
				});

				if (Array.isArray(event.data)) {
					this.sources.push(...event.data);
				} else {
					this.sources.push(event.data);
				}
				break;

			case 'documents':
				const docActivity: ToolActivity = {
					id: crypto.randomUUID(),
					type: 'documents',
					timestamp: new Date(),
					data: event.data
				};
				this.toolActivities.push(docActivity);
				this.contentParts.push({
					type: 'tool',
					content: '',
					activity: docActivity
				});

				if (Array.isArray(event.data)) {
					this.documents.push(...event.data);
				} else {
					this.documents.push(event.data);
				}
				break;

			case 'read_file':
				const readFileActivity: ToolActivity = {
					id: crypto.randomUUID(),
					type: 'read_file',
					timestamp: new Date(),
					data: event.data
				};
				this.toolActivities.push(readFileActivity);
				this.contentParts.push({
					type: 'tool',
					content: '',
					activity: readFileActivity
				});
				break;

			case 'list_files':
				const listFilesActivity: ToolActivity = {
					id: crypto.randomUUID(),
					type: 'list_files',
					timestamp: new Date(),
					data: event.data
				};
				this.toolActivities.push(listFilesActivity);
				this.contentParts.push({
					type: 'tool',
					content: '',
					activity: listFilesActivity
				});
				this.fileLists.push(event.data);
				break;

			case 'chat_history':
				const chatActivity: ToolActivity = {
					id: crypto.randomUUID(),
					type: 'chat_history',
					timestamp: new Date(),
					data: event.data
				};
				this.toolActivities.push(chatActivity);
				break;

			case 'final':
				// Update final data
				if (event.data.documents) {
					this.documents = Array.isArray(event.data.documents) ? event.data.documents : [event.data.documents];
				}
				if (event.data.sources) {
					this.sources = Array.isArray(event.data.sources) ? event.data.sources : [event.data.sources];
				}
				break;

			default:
				console.warn(`Unknown event type: ${(event as any).type}`);
		}

		return this.getCurrentState();
	}

	/**
	 * Legacy method for backward compatibility - converts chunk to event
	 * @deprecated Use processEvent directly instead
	 */
	processChunk(chunk: string): ParsedMessage {
		// For backward compatibility, treat chunk as a token
		const tokenEvent: StreamEvent = { type: 'token', data: chunk };
		return this.processEvent(tokenEvent);
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
	 * No need for finalize with direct event processing
	 */
	finalize(): ParsedMessage {
		return this.getCurrentState();
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
		this.currentTextContent = '';
		this.contentParts = [];
		this.toolActivities = [];
		this.documents = [];
		this.sources = [];
		this.fileLists = [];
	}
}
