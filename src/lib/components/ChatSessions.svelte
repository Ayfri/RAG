<script lang="ts">
	import Button from '$lib/components/common/Button.svelte';
	import type {ChatSession} from '$lib/helpers/chat-storage';
	import {chatStorage} from '$lib/helpers/chat-storage';
	import {dispatchUI} from '$lib/helpers/ui-events';
	import {notifications} from '$lib/stores/notifications';
	import {selectedState} from '$lib/stores/selectedState';
	import {Loader2, MessageSquare, Pencil, Plus, Trash2} from '@lucide/svelte';

	interface Props {
		ragName: string;
		onSessionSelected?: (sessionId: string, messages: ChatSession['messages']) => void;
	}

	let { ragName, onSessionSelected }: Props = $props();

	// Local state
	let sessions: ChatSession[] = $state([]);
	let currentSessionId: string | null = $state(null);
	let loading = $state(false);
	let editingSessionId = $state('');
	let editingTitle = $state('');



	function startEditing(session: ChatSession) {
		editingSessionId = session.id;
		editingTitle = session.title;
	}

	function cancelEditing() {
		editingSessionId = '';
		editingTitle = '';
	}

	function saveEditing() {
		if (editingTitle.trim()) {
			renameSession(editingSessionId, editingTitle.trim());
		}
		cancelEditing();
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			saveEditing();
		} else if (event.key === 'Escape') {
			cancelEditing();
		}
	}

	function formatDate(date: Date): string {
		const now = new Date();
		const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

		if (diffInHours < 1) {
			return 'Just now';
		} else if (diffInHours < 24) {
			return `${Math.floor(diffInHours)}h ago`;
		} else if (diffInHours < 48) {
			return 'Yesterday';
		} else {
			return date.toLocaleDateString('en-US', {
				day: 'numeric',
				month: 'short'
			});
		}
	}

	function getMessagePreview(session: ChatSession): string {
		const lastUserMessage = [...session.messages].reverse().find(m => m.role === 'user');
		return `${lastUserMessage?.content.slice(0, 50)}${(lastUserMessage?.content.length ?? 0) > 50 ? '...' : ''}` || 'No message';
	}

	// Session management functions
	async function loadSessions() {
		try {
			loading = true;
			await chatStorage.init();
			sessions = await chatStorage.getSessionsByRag(ragName);
		} catch (err) {
			console.error('Failed to load sessions:', err);
			notifications.error('Failed to load sessions');
		} finally {
			loading = false;
		}
	}

	async function createNewSession() {
		try {
			const session = await chatStorage.createSession(ragName);
			currentSessionId = session.id;
			await loadSessions();
			// Select the new session to trigger the callback
			await selectSession(session.id);
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
				// Call parent callback
				onSessionSelected?.(sessionId, session.messages);
                dispatchUI('sessionSelected', { ragName, sessionId, messages: session.messages });
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
			}
			await loadSessions();
			notifications.success('Session deleted');
		} catch (err) {
			console.error('Failed to delete session:', err);
			notifications.error('Failed to delete session');
		}
	}

	async function renameSession(sessionId: string, newTitle: string) {
		try {
			await chatStorage.updateSessionTitle(sessionId, newTitle);
			await loadSessions();
			notifications.success('Session renamed');
		} catch (err) {
			console.error('Failed to rename session:', err);
			notifications.error('Failed to rename session');
		}
	}

	// Load sessions when ragName changes
	$effect(() => {
		if (ragName) {
			loadSessions();
		}
	});

	// Restore selected session when sessions are loaded
	$effect(() => {
		if (sessions.length > 0 && !currentSessionId) {
			const unsubscribe = selectedState.subscribe(state => {
				if (state.ragName === ragName && state.sessionId) {
					const sessionExists = sessions.some(s => s.id === state.sessionId);
					if (sessionExists) {
						selectSession(state.sessionId);
					}
				}
			});
			return unsubscribe;
		}
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

	// Listen for session events from QueryInterface
	$effect(() => {
		const handleSessionCreated = (event: Event) => {
			const customEvent = event as CustomEvent;
			const { ragName: eventRagName } = customEvent.detail;
			if (eventRagName === ragName) {
				loadSessions();
			}
		};

		const handleSessionDeleted = (event: Event) => {
			const customEvent = event as CustomEvent;
			const { ragName: eventRagName } = customEvent.detail;
			if (eventRagName === ragName) {
				loadSessions();
			}
		};

		const handleSessionRenamed = (event: Event) => {
			const customEvent = event as CustomEvent;
			const { ragName: eventRagName } = customEvent.detail;
			if (eventRagName === ragName) {
				loadSessions();
			}
		};

		const handleMessageAdded = (event: Event) => {
			const customEvent = event as CustomEvent;
			const { ragName: eventRagName } = customEvent.detail;
			if (eventRagName === ragName) {
				loadSessions();
			}
		};

		const handleMessageDeleted = (event: Event) => {
			const customEvent = event as CustomEvent;
			const { ragName: eventRagName } = customEvent.detail;
			if (eventRagName === ragName) {
				loadSessions();
			}
		};

		const handleMessagesCleared = (event: Event) => {
			const customEvent = event as CustomEvent;
			const { ragName: eventRagName } = customEvent.detail;
			if (eventRagName === ragName) {
				loadSessions();
			}
		};

		window.addEventListener('sessionCreated', handleSessionCreated);
		window.addEventListener('sessionDeleted', handleSessionDeleted);
		window.addEventListener('sessionRenamed', handleSessionRenamed);
		window.addEventListener('messageAdded', handleMessageAdded);
		window.addEventListener('messageDeleted', handleMessageDeleted);
		window.addEventListener('messagesCleared', handleMessagesCleared);

		return () => {
			window.removeEventListener('sessionCreated', handleSessionCreated);
			window.removeEventListener('sessionDeleted', handleSessionDeleted);
			window.removeEventListener('sessionRenamed', handleSessionRenamed);
			window.removeEventListener('messageAdded', handleMessageAdded);
			window.removeEventListener('messageDeleted', handleMessageDeleted);
			window.removeEventListener('messagesCleared', handleMessagesCleared);
		};
	});
</script>

<div class="h-full flex flex-col">
	<!-- Header -->
	<div class="p-2 border-b border-slate-600 flex items-center justify-between">
		<h3 class="text-sm font-semibold text-slate-200">Chat Sessions</h3>
			<Button
				onclick={createNewSession}
				size="icon"
				variant="secondary"
				title="New session"
			>
			<Plus size={16} class="text-white" />
		</Button>
	</div>

	<!-- Sessions List -->
	<div class="flex-1 overflow-y-auto">
		{#if loading}
			<div class="p-4 text-center text-slate-400">
				<Loader2 size={32} class="mx-auto mb-2 text-slate-600" />
				<p class="text-sm">Loading sessions...</p>
			</div>
		{:else if sessions.length === 0}
			<div class="p-4 text-center text-slate-400">
				<MessageSquare size={32} class="mx-auto mb-2 text-slate-600" />
				<p class="text-sm">No sessions</p>
				<p class="text-xs text-slate-500 mt-1">Create your first session</p>
			</div>
		{:else}
			<div class="space-y-1 py-3 px-2 md:px-0">
				{#each sessions as session (session.id)}
					<div
						class="group relative rounded-lg border transition-all duration-200 {
							currentSessionId === session.id
								? 'bg-cyan-900/30 border-cyan-600'
								: 'bg-slate-800/50 border-slate-700 hover:bg-slate-700/50 hover:border-slate-600'
						}"
					>
						<div class="p-2">
							{#if editingSessionId === session.id}
								<input
									bind:value={editingTitle}
									onkeydown={handleKeydown}
									onblur={saveEditing}
									class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
								/>
							{:else}
								<div class="flex items-start justify-between">
									<button
										onclick={() => selectSession(session.id)}
										class="flex-1 min-w-0 text-left cursor-pointer"
									>
										<h4 class="text-sm font-medium text-slate-200 truncate">
											{session.title}
										</h4>
										<p class="text-xs text-slate-400 line-clamp-2">
											{getMessagePreview(session)}
										</p>
										<div class="flex items-center space-x-4 mt-1 text-[0.7rem] text-slate-500">
											<span>
												{formatDate(session.updatedAt)}
											</span>
											<span>
												{session.messages.length} message{session.messages.length !== 1 ? 's' : ''}
											</span>
										</div>
									</button>

									<div class="flex items-center space-x-1 lg:opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
										<Button
											onclick={() => startEditing(session)}
											size="icon"
											variant="secondary"
											title="Rename"
										>
											<Pencil size={14} />
										</Button>
										<Button
											onclick={() => {
												if (confirm('Delete this chat session?')) {
													deleteSession(session.id);
												}
											}}
											size="icon"
											variant="danger"
											title="Delete"
										>
											<Trash2 size={14} />
										</Button>
									</div>
								</div>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
