import type { RagDocument, SearchResult, ToolActivity, FileListResult } from '$lib/types.d.ts';

export interface ChatMessage {
	content: string;
	contentParts?: Array<{type: 'text' | 'tool'; content: string; activity?: ToolActivity}>;
	documents?: RagDocument[];
	fileLists?: FileListResult[];
	id: string;
	role: 'user' | 'assistant';
	sources?: SearchResult[];
	timestamp: Date;
	toolActivities?: ToolActivity[];
}

export interface ChatSession {
	id: string;
	messages: ChatMessage[];
	ragName: string;
	title: string;
	createdAt: Date;
	updatedAt: Date;
}

interface ChatDB extends IDBDatabase {
	objectStoreNames: DOMStringList;
}

class ChatStorageService {
	private dbName = 'rag-chat-storage';
	private dbVersion = 1;
	private storeName = 'chat-sessions';
	private db: ChatDB | null = null;

	async init(): Promise<void> {
		return new Promise((resolve, reject) => {
			const request = indexedDB.open(this.dbName, this.dbVersion);

			request.onerror = () => reject(request.error);
			request.onsuccess = () => {
				this.db = request.result as ChatDB;
				resolve();
			};

			request.onupgradeneeded = (event) => {
				const db = (event.target as IDBOpenDBRequest).result as ChatDB;

				if (!db.objectStoreNames.contains(this.storeName)) {
					const store = db.createObjectStore(this.storeName, { keyPath: 'id' });
					store.createIndex('ragName', 'ragName', { unique: false });
					store.createIndex('updatedAt', 'updatedAt', { unique: false });
				}
			};
		});
	}

	private async ensureDB(): Promise<ChatDB> {
		if (!this.db) {
			await this.init();
		}
		if (!this.db) {
			throw new Error('Failed to initialize database');
		}
		return this.db;
	}

	async createSession(ragName: string, title?: string): Promise<ChatSession> {
		const db = await this.ensureDB();
		const session: ChatSession = {
			id: crypto.randomUUID(),
			ragName,
			title: title || `Chat ${new Date().toLocaleDateString()}`,
			messages: [],
			createdAt: new Date(),
			updatedAt: new Date()
		};

		return new Promise((resolve, reject) => {
			const transaction = db.transaction([this.storeName], 'readwrite');
			const store = transaction.objectStore(this.storeName);
			const request = store.add(session);

			request.onsuccess = () => resolve(session);
			request.onerror = () => reject(request.error);
		});
	}

	async getSession(sessionId: string): Promise<ChatSession | null> {
		const db = await this.ensureDB();

		return new Promise((resolve, reject) => {
			const transaction = db.transaction([this.storeName], 'readonly');
			const store = transaction.objectStore(this.storeName);
			const request = store.get(sessionId);

			request.onsuccess = () => {
				const result = request.result;
				if (result) {
					// Convert date strings back to Date objects
					result.createdAt = new Date(result.createdAt);
					result.updatedAt = new Date(result.updatedAt);
					result.messages = result.messages.map((msg: any) => ({
						...msg,
						timestamp: new Date(msg.timestamp)
					}));
				}
				resolve(result || null);
			};
			request.onerror = () => reject(request.error);
		});
	}

	async getSessionsByRag(ragName: string): Promise<ChatSession[]> {
		const db = await this.ensureDB();

		return new Promise((resolve, reject) => {
			const transaction = db.transaction([this.storeName], 'readonly');
			const store = transaction.objectStore(this.storeName);
			const index = store.index('ragName');
			const request = index.getAll(ragName);

			request.onsuccess = () => {
				const results = request.result.map((session: any) => ({
					...session,
					createdAt: new Date(session.createdAt),
					updatedAt: new Date(session.updatedAt),
					messages: session.messages.map((msg: any) => ({
						...msg,
						timestamp: new Date(msg.timestamp)
					}))
				}));

				// Sort by updatedAt desc
				results.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
				resolve(results);
			};
			request.onerror = () => reject(request.error);
		});
	}

	async updateSession(session: ChatSession): Promise<void> {
		const db = await this.ensureDB();
		session.updatedAt = new Date();

		return new Promise((resolve, reject) => {
			const transaction = db.transaction([this.storeName], 'readwrite');
			const store = transaction.objectStore(this.storeName);
			const request = store.put(session);

			request.onsuccess = () => resolve();
			request.onerror = () => reject(request.error);
		});
	}

	async addMessage(sessionId: string, message: ChatMessage): Promise<void> {
		const session = await this.getSession(sessionId);
		if (!session) {
			throw new Error('Session not found');
		}

		session.messages.push(message);
		await this.updateSession(session);
	}

	async updateMessage(sessionId: string, messageId: string, updates: Partial<ChatMessage>): Promise<void> {
		const session = await this.getSession(sessionId);
		if (!session) {
			throw new Error('Session not found');
		}

		const messageIndex = session.messages.findIndex(m => m.id === messageId);
		if (messageIndex === -1) {
			throw new Error('Message not found');
		}

		session.messages[messageIndex] = { ...session.messages[messageIndex], ...updates };
		await this.updateSession(session);
	}

	async deleteMessage(sessionId: string, messageId: string): Promise<void> {
		const session = await this.getSession(sessionId);
		if (!session) {
			throw new Error('Session not found');
		}

		session.messages = session.messages.filter(m => m.id !== messageId);
		await this.updateSession(session);
	}

	async deleteSession(sessionId: string): Promise<void> {
		const db = await this.ensureDB();

		return new Promise((resolve, reject) => {
			const transaction = db.transaction([this.storeName], 'readwrite');
			const store = transaction.objectStore(this.storeName);
			const request = store.delete(sessionId);

			request.onsuccess = () => resolve();
			request.onerror = () => reject(request.error);
		});
	}

	async updateSessionTitle(sessionId: string, title: string): Promise<void> {
		const session = await this.getSession(sessionId);
		if (!session) {
			throw new Error('Session not found');
		}

		session.title = title;
		await this.updateSession(session);
	}

	async clearSessionMessages(sessionId: string): Promise<void> {
		const session = await this.getSession(sessionId);
		if (!session) {
			throw new Error('Session not found');
		}

		session.messages = [];
		await this.updateSession(session);
	}

	async getAllSessions(): Promise<ChatSession[]> {
		const db = await this.ensureDB();

		return new Promise((resolve, reject) => {
			const transaction = db.transaction([this.storeName], 'readonly');
			const store = transaction.objectStore(this.storeName);
			const request = store.getAll();

			request.onsuccess = () => {
				const results = request.result.map((session: any) => ({
					...session,
					createdAt: new Date(session.createdAt),
					updatedAt: new Date(session.updatedAt),
					messages: session.messages.map((msg: any) => ({
						...msg,
						timestamp: new Date(msg.timestamp)
					}))
				}));

				// Sort by updatedAt desc
				results.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
				resolve(results);
			};
			request.onerror = () => reject(request.error);
		});
	}
}

export const chatStorage = new ChatStorageService();
