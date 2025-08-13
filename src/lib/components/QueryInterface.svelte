<script lang="ts">
	import ChatInput from '$lib/components/ChatInput.svelte';
	import Button from '$lib/components/common/Button.svelte';
	import Select from '$lib/components/common/Select.svelte';
	import DocumentsModal from '$lib/components/DocumentsModal.svelte';

    import ChatMessage from '$lib/components/messages/ChatMessage.svelte';
	import RagConfigModal from '$lib/components/RagConfigModal.svelte';
	import {type ChatMessage as StoredChatMessage, chatStorage} from '$lib/helpers/chat-storage';
	import {AgenticStreamingParser} from '$lib/helpers/streaming-parser';
	import {dispatchUI} from '$lib/helpers/ui-events';
	import {notifications} from '$lib/stores/notifications';
	import {openAIModels} from '$lib/stores/openai-models';
	import {selectedState} from '$lib/stores/selectedState';
	import type { OpenAIModel } from '$lib/types';
	import {Bot, FileText, MessageSquare, Settings, Trash2, ChevronDown} from '@lucide/svelte';
    import { fetchRagConfig, updateRagConfig } from '$lib/helpers/rag-api';
    import MessageStats from '$lib/components/common/MessageStats.svelte';

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
	let showDocumentsModal = $state(false);
	let showConfigModal = $state(false);

	let chatContainer: HTMLElement;

	// Chat sessions state
	let currentSessionId: string | null = $state(null);

	// Auto-scroll state
	let autoScroll = $state(true);
	let showScrollToBottom = $state(false);

	// Utilities
	function createAssistantMessage(): Message {
		return {
			id: crypto.randomUUID(),
			role: 'assistant',
			content: '',
			timestamp: new Date(),
			toolActivities: [],
			contentParts: [],
			fileLists: []
		};
	}

	function scheduleScrollToBottom() {
		if (chatContainer) {
			requestAnimationFrame(() => {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			});
		}
	}

    function getTotalText(msgs: Message[]): string {
        if (!msgs || msgs.length === 0) return '';
        return msgs.map(m => m.content).join('\n');
    }

	$effect(() => {
		let unsubSelectedState: (() => void) | undefined;
		const handleSessionSelected = (event: Event) => {
			const customEvent = event as CustomEvent;
			const { sessionId, messages: sessionMessages, ragName: eventRagName } = customEvent.detail;
			if (eventRagName === ragName) {
				currentSessionId = sessionId;
				messages = sessionMessages;
			}
		};

		if (ragName) {
			unsubSelectedState = selectedState.subscribe(state => {
				if (state.ragName === ragName && state.sessionId && !currentSessionId) {
					selectSession(state.sessionId);
				}
			});
		}

		window.addEventListener('sessionSelected', handleSessionSelected);
		return () => {
			unsubSelectedState?.();
			window.removeEventListener('sessionSelected', handleSessionSelected);
		};
	});

	// Update persistent state when session changes
	$effect(() => {
		if (currentSessionId) {
			selectedState.update(state => ({
				...state,
				ragName,
				sessionId: currentSessionId
			}));
		}
	});

	// Load config when ragName changes
	$effect(() => {
		if (ragName) {
			loadRagConfig();
		}
	});

	// Auto-scroll when streaming or new messages arrive
	$effect(() => {
		if (autoScroll && chatContainer && (streaming || messages.length > 0)) {
			scheduleScrollToBottom();
		}
	});

	// Handle scroll events to detect user scrolling
	function handleScroll() {
		if (!chatContainer) return;

		const { scrollTop, scrollHeight, clientHeight } = chatContainer;
		const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10; // 10px tolerance
		const scrollDistance = scrollHeight - clientHeight - scrollTop;

		if (isAtBottom) {
			autoScroll = true;
			showScrollToBottom = false;
		} else {
			autoScroll = false;
			// Show scroll to bottom button if scrolled up more than 100px
			showScrollToBottom = scrollDistance > 100;
		}
	}

	function scrollToBottom() {
		if (chatContainer) {
			chatContainer.scrollTop = chatContainer.scrollHeight;
			autoScroll = true;
			showScrollToBottom = false;
		}
	}

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

		const assistantMessage: Message = createAssistantMessage();

		messages = [...messages, userMessage, assistantMessage];
		const query = currentMessage.trim();
		currentMessage = '';

		// Force auto-scroll after adding messages
		if (autoScroll) scheduleScrollToBottom();

		// Save user message to storage
		if (currentSessionId) {
			await chatStorage.addMessage(currentSessionId, userMessage);
			dispatchUI('messageAdded', { ragName, sessionId: currentSessionId });
		}

		await streamResponse(query, assistantMessage);
	}

	async function streamResponse(query: string, assistantMessage: Message) {
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
			let buffer = '';

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const chunk = decoder.decode(value, { stream: true });
				buffer += chunk;

				// Process complete lines (each line is a JSON event)
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					if (line.trim()) {
						try {
							// Each line is a complete JSON event
							const event = JSON.parse(line.trim());
							const parsedMessage = parser.processEvent(event);

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
						} catch (e) {
							console.warn('Failed to parse streaming event:', e, line);
						}
					}
				}
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
		dispatchUI('messageAdded', { ragName, sessionId: currentSessionId });
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
			dispatchUI('messageAdded', { ragName, sessionId: currentSessionId });
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
		const messagesToDelete: string[] = [];

		if (messageToDelete.role === 'user') {
			// Delete user message and the assistant message that follows (if it exists)
			messagesToDelete.push(id);
			if (messageIndex + 1 < messages.length && messages[messageIndex + 1].role === 'assistant') {
				messagesToDelete.push(messages[messageIndex + 1].id);
			}
		} else if (messageToDelete.role === 'assistant') {
			// Delete assistant message and the user message that precedes (if it exists)
			if (messageIndex > 0 && messages[messageIndex - 1].role === 'user') {
				messagesToDelete.push(messages[messageIndex - 1].id);
			}
			messagesToDelete.push(id);
		}

		messages = messages.filter(m => !messagesToDelete.includes(m.id));

		// Delete from storage
		if (currentSessionId) {
			for (const messageId of messagesToDelete) {
				await chatStorage.deleteMessage(currentSessionId, messageId);
			}
			dispatchUI('messageDeleted', { ragName, sessionId: currentSessionId });
		}
	}

	async function handleEditMessage(id: string, newContent: string) {
		const messageIndex = messages.findIndex(m => m.id === id);
		if (messageIndex === -1 || messages[messageIndex].role !== 'user') return;

		// Get all messages that will be removed (all messages after this user message)
		const messagesToDelete = messages.slice(messageIndex + 1).map(m => m.id);

		// Update the message content
		messages[messageIndex] = { ...messages[messageIndex], content: newContent };

		// Remove all messages after this user message
		messages = messages.slice(0, messageIndex + 1);

		if (currentSessionId) {
			await chatStorage.updateMessage(currentSessionId, id, { content: newContent });
			// Delete all messages after this one from storage
			for (const messageId of messagesToDelete) {
				await chatStorage.deleteMessage(currentSessionId, messageId);
			}
			dispatchUI('messageEdited', { ragName, sessionId: currentSessionId });
		}

		// Create a new assistant message and regenerate response
		const assistantMessage: Message = createAssistantMessage();

		messages = [...messages, assistantMessage];
		const query = newContent.trim();

		try {
			await streamResponse(query, assistantMessage);
		} catch (err) {
			console.error('Failed to regenerate response:', err);
			notifications.error('Failed to regenerate response');
			// Remove the assistant message if there was an error
			messages = messages.slice(0, -1);
		}
	}

	async function handleRegenerateMessage(id: string) {
		const messageIndex = messages.findIndex(m => m.id === id);
		if (messageIndex === -1 || messages[messageIndex].role !== 'assistant') return;

		const userMessageIndex = messageIndex - 1;
		if (userMessageIndex < 0 || messages[userMessageIndex].role !== 'user') return;

		const userMessage = messages[userMessageIndex];

		const messagesToDelete = messages.slice(userMessageIndex + 1).map(m => m.id);

		messages = messages.slice(0, userMessageIndex + 1);

		if (currentSessionId && messagesToDelete.length > 0) {
			for (const messageId of messagesToDelete) {
				await chatStorage.deleteMessage(currentSessionId, messageId);
			}
			dispatchUI('messageDeleted', { ragName, sessionId: currentSessionId });
		}

		const assistantMessage: Message = createAssistantMessage();

		messages = [...messages, assistantMessage];

		try {
			await streamResponse(userMessage.content.trim(), assistantMessage);
		} catch (err) {
			console.error('Failed to regenerate response:', err);
			notifications.error('Failed to regenerate response');
			// Remove the assistant message if there was an error
			messages = messages.slice(0, -1);
		}
	}

	async function clearConversation() {
		if (confirm('Clear the current conversation?')) {
			messages = [];
			if (currentSessionId) {
				await chatStorage.clearSessionMessages(currentSessionId);
			dispatchUI('messagesCleared', { ragName, sessionId: currentSessionId });
			}
		}
	}



	async function loadRagConfig() {
		try {
			const config = await fetchRagConfig(ragName);
			selectedModel = config.chat_model;
		} catch (err) {
			console.error('Failed to load RAG config:', err);
			notifications.error(`Failed to load RAG config: ${err instanceof Error ? err.message : 'Unknown error'}`);
		}
	}

	async function updateModelConfig(newModel: string) {
		try {
			await updateRagConfig(ragName, { chat_model: newModel });
		} catch (err) {
			console.error('Failed to update RAG config:', err);
			notifications.error(`Failed to update chat model: ${err instanceof Error ? err.message : 'Unknown error'}`);
		}
	}




	async function createNewSession() {
		try {
			const session = await chatStorage.createSession(ragName);
			currentSessionId = session.id;
			messages = [];
			selectedState.set({
				ragName: ragName,
				sessionId: session.id
			});
			dispatchUI('sessionCreated', { ragName, sessionId: session.id });
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
				messages = session.messages || [];
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
				selectedState.set({
					ragName: ragName,
					sessionId: null
				});
			}
			dispatchUI('sessionDeleted', { ragName, sessionId });
			notifications.success('Session deleted');
		} catch (err) {
			console.error('Failed to delete session:', err);
			notifications.error('Failed to delete session');
		}
	}

	async function renameSession(sessionId: string, newTitle: string) {
		try {
			await chatStorage.updateSessionTitle(sessionId, newTitle);
			dispatchUI('sessionRenamed', { ragName, sessionId, newTitle });
			notifications.success('Session renamed');
		} catch (err) {
			console.error('Failed to rename session:', err);
			notifications.error('Failed to rename session');
		}
	}

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
			updateModelConfig(selectedModel);
		}
	});
</script>

<div class="h-full max-h-screen flex flex-col overflow-hidden">
	<!-- Header -->
	<header class="glass border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700 py-2 px-3 rounded-xl flex-shrink-0">
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
						<span>Documents</span>
					</Button>
					<Button
						onclick={() => showConfigModal = true}
						class="flex items-center space-x-1.5 px-2 py-1.5 md:px-2.5 md:py-2 bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 text-white rounded-lg text-xs md:text-sm font-medium transition-all duration-200 shadow-lg flex-1 md:flex-initial justify-center md:justify-start min-h-[36px] md:min-h-0 whitespace-nowrap"
						title="Configure RAG"
					>
						<Settings size={16} class="md:w-[18px] md:h-[18px]" />
						<span>Settings</span>
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

	<main class="flex-1 flex flex-col min-h-0 overflow-hidden relative">
		<div class="absolute top-0 left-0 w-full px-4 h-6 bg-gradient-to-t from-transparent to-slate-900/80"></div>

		<!-- Scroll to bottom button -->
		{#if showScrollToBottom}
			<div class="absolute bottom-24 right-8 z-10">
				<Button
					onclick={scrollToBottom}
					class="flex items-center justify-center size-8 !p-0 bg-slate-600 hover:bg-slate-500 text-white shadow-xl hover:scale-110"
					title="Scroll to bottom"
					variant="secondary"
				>
					<ChevronDown size={20} />
				</Button>
			</div>
		{/if}

		<!-- Messages -->
		<div
			bind:this={chatContainer}
			class="flex-1 overflow-y-auto overflow-x-hidden p-1 md:p-3 space-y-2 md:space-y-4 min-h-0 scroll-smooth"
			onscroll={handleScroll}
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
						onEdit={handleEditMessage}
						onRegenerate={handleRegenerateMessage}
					/>
				{/each}

                <!-- Total characters/tokens count -->
				{#if messages.length > 0}
                    {@const totalText = getTotalText(messages)}
					<div class="text-center py-1">
						<span class="text-xs text-slate-500 bg-slate-800/50 px-3 py-1 rounded-full border border-slate-700">
                            {messages.length} message{messages.length > 1 ? 's' : ''} • <MessageStats hideWhenEmpty={false} text={totalText} />
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
	bind:open={showDocumentsModal}
/>

<RagConfigModal
	{ragName}
	bind:open={showConfigModal}
	onupdated={() => loadRagConfig()}
/>
