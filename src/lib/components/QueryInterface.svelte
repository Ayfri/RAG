<script lang="ts">
	import ChatInput from '$lib/components/ChatInput.svelte';
	import Button from '$lib/components/common/Button.svelte';
	import Select from '$lib/components/common/Select.svelte';
	import DocumentsModal from '$lib/components/DocumentsModal.svelte';
	import ChatMessage from '$lib/components/messages/ChatMessage.svelte';
	import {type ChatMessage as StoredChatMessage, chatStorage} from '$lib/helpers/chat-storage';
	import {AgenticStreamingParser} from '$lib/helpers/streaming-parser';
	import {notifications} from '$lib/stores/notifications';
	import {openAIModels} from '$lib/stores/openai-models';
	import type {FileItem, OpenAIModel} from '$lib/types.d.ts';
	import {Bot, FileText, MessageSquare, Trash2} from '@lucide/svelte';

	interface Props {
		ragName: string;
	}

	type Message = StoredChatMessage;

	let { ragName }: Props = $props();
	let allOpenAIModels: OpenAIModel[] = $state([]);
	let selectedModel = $state('');

	let currentMessage = $state('');
	let messages: Message[] = $state([]);
	let loading = $state(false);
	let streaming = $state(false);
	let files: FileItem[] = $state([]);
	let loadingFiles = $state(false);
	let uploadingFile = $state(false);
	let reindexing = $state(false);
	let showDocumentsModal = $state(false);
	let chatContainer: HTMLElement;

	// Chat sessions state
	let currentSessionId: string | null = $state(null);

	async function sendMessage() {
		if (!currentMessage.trim() || loading) return;

		// Create a new session if none exists
		if (!currentSessionId) {
			await createNewSession();
		}

		const userMessage: Message = {
			id: crypto.randomUUID(),
			role: 'user',
			content: currentMessage.trim(),
			timestamp: new Date()
		};

		const assistantMessage: Message = {
			id: crypto.randomUUID(),
			role: 'assistant',
			content: '',
			timestamp: new Date(),
			toolActivities: [],
			contentParts: [],
			fileLists: []
		};

		messages = [...messages, userMessage, assistantMessage];
		const query = currentMessage.trim();
		currentMessage = '';

		// Save user message to storage
		if (currentSessionId) {
			await chatStorage.addMessage(currentSessionId, userMessage);
			// Dispatch event to notify ChatSessions component
			window.dispatchEvent(new CustomEvent('messageAdded', {
				detail: { ragName, sessionId: currentSessionId }
			}));
		}

		try {
			loading = true;
			streaming = true;

			const res = await fetch(`/api/rag/${ragName}/stream`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					query,
					history: messages.slice(0, -2).map(({ role, content }) => ({ role, content }))
				})
			});

			if (!res.ok) throw new Error('Failed to stream response');

			const reader = res.body?.getReader();
			if (!reader) throw new Error('No response body');

			const decoder = new TextDecoder();
			const parser = new AgenticStreamingParser();

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const chunk = decoder.decode(value, { stream: true });
				const parsedMessage = parser.processChunk(chunk);

				// Update the assistant message with parsed data
				messages = messages.map((msg, index) =>
					index === messages.length - 1
						? {
							...msg,
							content: parsedMessage.content,
							contentParts: parsedMessage.contentParts,
							toolActivities: parsedMessage.toolActivities,
							documents: parsedMessage.documents,
							sources: parsedMessage.sources,
							fileLists: parsedMessage.fileLists
						}
						: msg
				);

				// Auto-scroll to bottom as we receive data
				setTimeout(() => {
					if (chatContainer) {
						chatContainer.scrollTop = chatContainer.scrollHeight;
					}
				}, 0);
			}

			// Finalize parsing
			const finalMessage = parser.finalize();
			const finalAssistantMessage = {
				...assistantMessage,
				content: finalMessage.content,
				contentParts: finalMessage.contentParts,
				toolActivities: finalMessage.toolActivities,
				documents: finalMessage.documents,
				sources: finalMessage.sources,
				fileLists: finalMessage.fileLists
			};

			messages = messages.map((msg, index) =>
				index === messages.length - 1 ? finalAssistantMessage : msg
			);

			// Save assistant message to storage
			if (currentSessionId) {
				await chatStorage.addMessage(currentSessionId, finalAssistantMessage);
				// Dispatch event to notify ChatSessions component
				window.dispatchEvent(new CustomEvent('messageAdded', {
					detail: { ragName, sessionId: currentSessionId }
				}));
			}

		} catch (err) {
			const errorMessage = `Error: ${err instanceof Error ? err.message : 'Unknown error'}`;
			const finalAssistantMessage = { ...assistantMessage, content: errorMessage };

			// Update the last assistant message with error
			messages = messages.map((msg, index) =>
				index === messages.length - 1 ? finalAssistantMessage : msg
			);

			// Save error message to storage
			if (currentSessionId) {
				await chatStorage.addMessage(currentSessionId, finalAssistantMessage);
				// Dispatch event to notify ChatSessions component
				window.dispatchEvent(new CustomEvent('messageAdded', {
					detail: { ragName, sessionId: currentSessionId }
				}));
			}
		} finally {
			loading = false;
			streaming = false;
		}
	}

	async function handleDeleteMessage(id: string) {
		const messageIndex = messages.findIndex(m => m.id === id);
		if (messageIndex === -1) return;

		const messageToDelete = messages[messageIndex];

		if (messageToDelete.role === 'assistant' && messageIndex > 0) {
			// Also delete the preceding user message
			const userMessageId = messages[messageIndex - 1].id;
			messages = messages.filter((_, i) => i !== messageIndex && i !== messageIndex - 1);

			// Delete from storage
			if (currentSessionId) {
				await chatStorage.deleteMessage(currentSessionId, userMessageId);
				await chatStorage.deleteMessage(currentSessionId, id);
				// Dispatch event to notify ChatSessions component
				window.dispatchEvent(new CustomEvent('messageDeleted', {
					detail: { ragName, sessionId: currentSessionId }
				}));
			}
		} else {
			messages = messages.filter(m => m.id !== id);

			// Delete from storage
			if (currentSessionId) {
				await chatStorage.deleteMessage(currentSessionId, id);
				// Dispatch event to notify ChatSessions component
				window.dispatchEvent(new CustomEvent('messageDeleted', {
					detail: { ragName, sessionId: currentSessionId }
				}));
			}
		}
	}

	async function handleRegenerateMessage(id: string) {
		const messageIndex = messages.findIndex(m => m.id === id);
		if (messageIndex === -1 || messages[messageIndex].role !== 'assistant') return;

		const userMessageIndex = messageIndex - 1;
		if (userMessageIndex < 0 || messages[userMessageIndex].role !== 'user') return;

		const userMessage = messages[userMessageIndex];
		messages = messages.slice(0, userMessageIndex); // Remove all messages from the user message to regenerate

		currentMessage = userMessage.content;
		await sendMessage();
	}

	async function clearConversation() {
		if (confirm('Vider la conversation actuelle ?')) {
			messages = [];
			if (currentSessionId) {
				await chatStorage.clearSessionMessages(currentSessionId);
				// Dispatch event to notify ChatSessions component
				window.dispatchEvent(new CustomEvent('messagesCleared', {
					detail: { ragName, sessionId: currentSessionId }
				}));
			}
		}
	}

	async function loadFiles() {
		try {
			loadingFiles = true;
			const res = await fetch(`/api/rag/${ragName}/files`);
			if (!res.ok) throw new Error('Failed to load files');
			files = await res.json();
		} catch (err) {
			console.error('Failed to load files:', err);
		} finally {
			loadingFiles = false;
		}
	}

	async function uploadFile(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		try {
			uploadingFile = true;
			const formData = new FormData();
			formData.append('file', file);

			const res = await fetch(`/api/rag/${ragName}/files`, {
				method: 'POST',
				body: formData
			});

			if (!res.ok) throw new Error('Failed to upload file');

			notifications.success('File uploaded successfully!');
			loadFiles();
		} catch (err) {
			notifications.error(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			uploadingFile = false;
			input.value = '';
		}
	}

	async function uploadFolder(event: Event) {
		const input = event.target as HTMLInputElement;
		const files_list = input.files;
		if (!files_list || files_list.length === 0) return;

		try {
			uploadingFile = true;

			// Upload each file individually
			for (const file of files_list) {
				const formData = new FormData();
				formData.append('file', file);

				const res = await fetch(`/api/rag/${ragName}/files`, {
					method: 'POST',
					body: formData
				});

				if (!res.ok) throw new Error(`Failed to upload ${file.name}`);
			}

			notifications.success('Folder uploaded successfully!');
			loadFiles();
		} catch (err) {
			notifications.error(`Folder upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			uploadingFile = false;
			input.value = '';
		}
	}

	async function deleteFile(filename: string) {
		try {
			const res = await fetch(`/api/rag/${ragName}/files/${filename}`, { method: 'DELETE' });
			if (!res.ok) throw new Error('Failed to delete file');

			notifications.success(`Deleted ${filename}`);
			loadFiles();
		} catch (err) {
			notifications.error(`Delete failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		}
	}

	async function reindexRAG() {
		try {
			reindexing = true;
			const res = await fetch(`/api/rag/${ragName}/reindex`, { method: 'POST' });
			if (!res.ok) throw new Error('Failed to reindex RAG');

			notifications.success('RAG reindexed successfully!');
			loadFiles(); // Reload files after successful reindex
		} catch (err) {
			notifications.error(`Reindex failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			reindexing = false;
		}
	}

	async function loadRagConfig() {
		try {
			const res = await fetch(`/api/rag/${ragName}/config`);
			if (!res.ok) throw new Error('Failed to load RAG config');
			const config = await res.json();
			selectedModel = config.chat_model;
		} catch (err) {
			console.error('Failed to load RAG config:', err);
			notifications.error(`Failed to load RAG config: ${err instanceof Error ? err.message : 'Unknown error'}`);
		}
	}

	async function updateRagConfig(newModel: string) {
		try {
			const res = await fetch(`/api/rag/${ragName}/config`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ chat_model: newModel })
			});
			if (!res.ok) throw new Error('Failed to update RAG config');
		} catch (err) {
			console.error('Failed to update RAG config:', err);
			notifications.error(`Failed to update chat model: ${err instanceof Error ? err.message : 'Unknown error'}`);
		}
	}

	function handleSymlinkCreated() {
		loadFiles();
	}


	async function createNewSession() {
		try {
			const session = await chatStorage.createSession(ragName);
			currentSessionId = session.id;
			messages = [];
			// Dispatch event to notify ChatSessions component
			window.dispatchEvent(new CustomEvent('sessionCreated', {
				detail: { ragName, sessionId: session.id }
			}));
			notifications.success('New session created');
		} catch (err) {
			console.error('Failed to create session:', err);
			notifications.error('Failed to create session');
		}
	}

	async function selectSession(sessionId: string) {
		try {
			const session = await chatStorage.getSession(sessionId);
			if (session) {
				currentSessionId = sessionId;
				messages = session.messages;
			}
		} catch (err) {
			console.error('Failed to load session:', err);
			notifications.error('Failed to load session');
		}
	}

	async function deleteSession(sessionId: string) {
		try {
			await chatStorage.deleteSession(sessionId);
			if (currentSessionId === sessionId) {
				currentSessionId = null;
				messages = [];
			}
			// Dispatch event to notify ChatSessions component
			window.dispatchEvent(new CustomEvent('sessionDeleted', {
				detail: { ragName, sessionId }
			}));
			notifications.success('Session supprimée');
		} catch (err) {
			console.error('Failed to delete session:', err);
			notifications.error('Failed to delete session');
		}
	}

	async function renameSession(sessionId: string, newTitle: string) {
		try {
			await chatStorage.updateSessionTitle(sessionId, newTitle);
			// Dispatch event to notify ChatSessions component
			window.dispatchEvent(new CustomEvent('sessionRenamed', {
				detail: { ragName, sessionId, newTitle }
			}));
			notifications.success('Session renommée');
		} catch (err) {
			console.error('Failed to rename session:', err);
			notifications.error('Failed to rename session');
		}
	}

	// Load files and RAG config when component mounts or ragName changes
	$effect(() => {
		if (ragName) {
			loadFiles();
			loadRagConfig();
		}
	});

	// Auto-scroll when new messages arrive
	$effect(() => {
		if (messages.length > 0 && chatContainer) {
			setTimeout(() => {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			}, 100);
		}
	});

	// Subscribe to OpenAI models store
	$effect(() => {
		const unsubscribe = openAIModels.subscribe(models => {
			allOpenAIModels = [...models.chat, ...models.thinking].filter(model =>
				model.id.startsWith('gpt') ||
				model.id.startsWith('o') && !model.id.includes('deep-research')
			);
		});
		return unsubscribe;
	});

	$effect(() => {
		if (selectedModel) {
			updateRagConfig(selectedModel);
		}
	});

	// Listen for session selection events from sidebar
	$effect(() => {
		const handleSessionSelected = (event: Event) => {
			const customEvent = event as CustomEvent;
			const { sessionId, messages: sessionMessages, ragName: eventRagName } = customEvent.detail;
			if (eventRagName === ragName) {
				currentSessionId = sessionId;
				messages = sessionMessages;
			}
		};

		window.addEventListener('sessionSelected', handleSessionSelected);
		return () => window.removeEventListener('sessionSelected', handleSessionSelected);
	});
</script>

<div class="h-full max-h-screen flex flex-col gap-2 md:gap-4 overflow-hidden">
	<!-- Header -->
	<header class="glass border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700 p-2 md:p-2.5 rounded-xl flex-shrink-0">
		<div class="flex flex-col space-y-2 md:space-y-0 md:flex-row md:items-center md:justify-between">
			<!-- Title section -->
			<div class="flex items-center space-x-3">
				<MessageSquare size={18} class="text-cyan-400 md:w-6 md:h-6" />
				<h2 class="text-base md:text-lg font-bold text-slate-100 truncate">
					Chat with <span class="text-cyan-400">{ragName}</span>
				</h2>
			</div>

			<!-- Controls section -->
			<div class="flex flex-col space-y-2 md:space-y-0 md:flex-row md:items-center md:space-x-3">
				<!-- Model selector -->
				<div class="w-full md:w-48">
					<Select
						options={allOpenAIModels.map(model => ({ label: model.name, value: model.id }))}
						bind:value={selectedModel}
						placeholder="Select Chat Model"
						class="w-full"
					/>
				</div>

				<!-- Buttons -->
				<div class="flex items-center justify-between space-x-2 md:space-x-3">
					<Button
						onclick={() => showDocumentsModal = true}
						class="flex items-center space-x-1.5 px-2 py-1.5 md:px-2.5 md:py-2 bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 text-white rounded-lg text-xs md:text-sm font-medium transition-all duration-200 shadow-lg flex-1 md:flex-initial justify-center md:justify-start min-h-[36px] md:min-h-0 whitespace-nowrap"
						title="Toggle documents panel"
					>
						<FileText size={16} class="md:w-[18px] md:h-[18px]" />
						<span>Documents ({files.length})</span>
					</Button>
					<Button
						onclick={clearConversation}
						disabled={messages.length === 0}
						class="flex items-center space-x-1.5 px-2 py-1.5 md:px-2.5 md:py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-lg text-xs md:text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-red-500/25 flex-1 md:flex-initial justify-center md:justify-start min-h-[36px] md:min-h-0"
						title="Clear conversation"
					>
						<Trash2 size={16} class="md:w-[18px] md:h-[18px]" />
						<span>Clear</span>
					</Button>
				</div>
			</div>
		</div>
	</header>

	<main class="flex-1 flex flex-col min-h-0 overflow-hidden">
		<!-- Messages -->
		<div
			bind:this={chatContainer}
			class="flex-1 overflow-y-auto overflow-x-hidden p-1 md:p-3 space-y-2 md:space-y-4 min-h-0"
		>
			{#if messages.length === 0}
				<div class="flex flex-col items-center justify-center h-full text-center px-4">
					<Bot size={40} class="text-slate-600 mb-2 md:mb-3 md:w-12 md:h-12" />
					<h3 class="text-sm md:text-lg font-bold text-slate-300 mb-1">
						{currentSessionId ? 'Active session' : 'Start a conversation'}
					</h3>
					<p class="text-slate-500 max-w-md text-xs md:text-sm">
						{currentSessionId
							? 'Ask a question about your documents in this session.'
							: 'Ask a question about your documents. A new session will be created automatically.'}
					</p>
				</div>
			{:else}
				{#each messages as message (message.id)}
					<ChatMessage
						{message}
						isStreaming={streaming}
						isLastMessage={message === messages[messages.length - 1]}
						onDelete={handleDeleteMessage}
						onRegenerate={handleRegenerateMessage}
					/>
				{/each}

				<!-- Total characters count -->
				{#if messages.length > 0}
					{@const totalChars = messages.reduce((sum, msg) => sum + msg.content.length, 0)}
					<div class="text-center py-1">
						<span class="text-xs text-slate-500 bg-slate-800/50 px-3 py-1 rounded-full border border-slate-700">
							{messages.length} message{messages.length > 1 ? 's' : ''} • {totalChars.toLocaleString()} characters
						</span>
					</div>
				{/if}
			{/if}
		</div>

		<!-- Input Area -->
		<div class="px-1 flex-shrink-0">
			<ChatInput
				bind:value={currentMessage}
				loading={loading}
				onSubmit={sendMessage}
			/>
		</div>
	</main>
</div>

<DocumentsModal
	{ragName}
	{files}
	bind:open={showDocumentsModal}
	loading={loadingFiles}
	uploading={uploadingFile}
	reindexing={reindexing}
	onUploadFile={uploadFile}
	onUploadFolder={uploadFolder}
	onDeleteFile={deleteFile}
	onReindex={reindexRAG}
	onSymlinkCreated={handleSymlinkCreated}
/>
