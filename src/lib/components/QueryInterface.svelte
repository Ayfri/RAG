<script lang="ts">
	import { FileText, Trash2, MessageSquare, Bot } from '@lucide/svelte';
	import Button from '$lib/components/common/Button.svelte';
	import ChatMessage from '$lib/components/ChatMessage.svelte';
	import ChatInput from '$lib/components/ChatInput.svelte';
	import FilesModal from '$lib/components/FilesModal.svelte';
	import { notifications } from '$lib/stores/notifications';
	import type { SearchResult, RagDocument } from '$lib/types.d.ts';

	interface Props {
		ragName: string;
	}

	interface FileItem {
		name: string;
		type: 'file' | 'directory';
		is_symlink: boolean;
		target?: string;
		resolved_target_type?: 'file' | 'directory' | 'unknown';
		file_count?: number;
		size?: number;
		last_modified?: number;
	}

	interface Message {
		content: string;
		documents?: RagDocument[];
		id: string;
		role: 'user' | 'assistant';
		sources?: SearchResult[];
		timestamp: Date;
	}

	let { ragName }: Props = $props();

	let currentMessage = $state('');
	let messages: Message[] = $state([]);
	let loading = $state(false);
	let streaming = $state(false);
	let files: FileItem[] = $state([]);
	let loadingFiles = $state(false);
	let uploadingFile = $state(false);
	let reindexing = $state(false);
	let showFilesModal = $state(false);
	let chatContainer: HTMLElement;

	async function sendMessage() {
		if (!currentMessage.trim() || loading) return;

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
			timestamp: new Date()
		};

		messages = [...messages, userMessage, assistantMessage];
		const query = currentMessage.trim();
		currentMessage = '';

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
			let buffer = '';
			let doneReading = false;

			while (!doneReading) {
				const { done, value } = await reader.read();
				if (done) {
					doneReading = true;
				}
				if (value) {
					const chunk = decoder.decode(value);
					buffer += chunk;

					// Auto-scroll to bottom as we receive data
					setTimeout(() => {
						if (chatContainer) {
							chatContainer.scrollTop = chatContainer.scrollHeight;
						}
					}, 0);

					// While streaming, show the content up to the last separator (if any), otherwise all
					const lastSepIndex = buffer.lastIndexOf('\n---\n');
					if (lastSepIndex === -1) {
						// No separator yet, just show all as answer
						messages = messages.map((msg, index) =>
							index === messages.length - 1
								? { ...msg, content: buffer }
								: msg
						);
					} else {
						// Show only the answer part (before the last separator)
						const answer = buffer.slice(0, lastSepIndex);
						messages = messages.map((msg, index) =>
							index === messages.length - 1
								? { ...msg, content: answer }
								: msg
						);
					}
				}
			}

			// After the stream is done, process the last separator and JSON
			const lastSepIndex = buffer.lastIndexOf('\n---\n');
			if (lastSepIndex !== -1) {
				const answer = buffer.slice(0, lastSepIndex);
				const jsonPart = buffer.slice(lastSepIndex + 5);

				// Update the assistant message with the final answer
				messages = messages.map((msg, index) =>
					index === messages.length - 1
						? { ...msg, content: answer }
						: msg
				);

				// Try to parse the JSON part
				try {
					const data = JSON.parse(jsonPart);
					messages = messages.map((msg, index) =>
						index === messages.length - 1
							? {
								...msg,
								documents: data.documents,
								sources: data.sources
							}
							: msg
					);
				} catch (e) {
					// Ignore JSON parse errors for now
				}
			}
		} catch (err) {
			// Update the last assistant message with error
			messages = messages.map((msg, index) =>
				index === messages.length - 1
					? { ...msg, content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}` }
					: msg
			);
		} finally {
			loading = false;
			streaming = false;
		}
	}

	function handleDeleteMessage(id: string) {
		const messageIndex = messages.findIndex(m => m.id === id);
		if (messageIndex === -1) return;

		const messageToDelete = messages[messageIndex];

		if (messageToDelete.role === 'assistant' && messageIndex > 0) {
			// Also delete the preceding user message
			messages = messages.filter((_, i) => i !== messageIndex && i !== messageIndex - 1);
		} else {
			messages = messages.filter(m => m.id !== id);
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

	function clearConversation() {
		if (confirm('Clear the entire conversation?')) {
			messages = [];
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
		} catch (err) {
			notifications.error(`Reindex failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			reindexing = false;
		}
	}

	function handleSymlinkCreated() {
		loadFiles();
	}

	// Load files when component mounts or ragName changes
	$effect(() => {
		if (ragName) {
			loadFiles();
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
</script>

<div class="h-full max-h-screen flex flex-col gap-4 overflow-hidden">
	<!-- Header -->
	<header class="glass border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700 p-4 rounded-xl flex-shrink-0">
		<div class="flex items-center justify-between">
			<div class="flex items-center space-x-3">
				<MessageSquare class="w-6 h-6 text-cyan-400" />
				<h2 class="text-xl font-bold text-slate-100">
					Chat with <span class="text-cyan-400">{ragName}</span>
				</h2>
			</div>
			<div class="flex items-center space-x-3">
				<Button
					onclick={() => showFilesModal = true}
					class="group flex items-center space-x-2 px-3 py-2 bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 text-white rounded-xl cursor-pointer text-sm font-medium transition-all duration-200 shadow-lg"
					title="Toggle files panel"
				>
					<FileText class="w-4 h-4" />
					<span>Files ({files.length})</span>
				</Button>
				<Button
					onclick={clearConversation}
					disabled={messages.length === 0}
					class="group flex items-center space-x-2 px-3 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-xl cursor-pointer text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-red-500/25"
					title="Clear conversation"
				>
					<Trash2 class="w-4 h-4" />
					<span>Clear</span>
				</Button>
			</div>
		</div>
	</header>

	<main class="flex-1 flex flex-col min-h-0 overflow-hidden">
		<!-- Messages -->
		<div
			bind:this={chatContainer}
			class="flex-1 overflow-y-auto overflow-x-hidden p-6 space-y-6 min-h-0"
		>
			{#if messages.length === 0}
				<div class="flex flex-col items-center justify-center h-full text-center">
					<Bot class="w-16 h-16 text-slate-600 mb-4" />
					<h3 class="text-xl font-bold text-slate-300 mb-2">Start a conversation</h3>
					<p class="text-slate-500 max-w-md">
						Ask a question about your documents. The AI will analyze your content and provide a response based on available information.
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
			{/if}
		</div>

		<!-- Input Area -->
		<div class="px-4 pb-4 flex-shrink-0">
			<ChatInput
				bind:value={currentMessage}
				loading={loading}
				onSubmit={sendMessage}
			/>
		</div>
	</main>
</div>

<FilesModal
	{ragName}
	{files}
	bind:open={showFilesModal}
	loading={loadingFiles}
	uploading={uploadingFile}
	reindexing={reindexing}
	onUploadFile={uploadFile}
	onUploadFolder={uploadFolder}
	onDeleteFile={deleteFile}
	onReindex={reindexRAG}
	onSymlinkCreated={handleSymlinkCreated}
/>
