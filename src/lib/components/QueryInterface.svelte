<script lang="ts">
	import { Send, Loader, FileText, Trash2, Upload, Zap } from '@lucide/svelte';

	interface Props {
		ragName: string;
	}

	let { ragName }: Props = $props();

	let query = $state('');
	let response = $state('');
	let loading = $state(false);
	let streaming = $state(false);
	let files: string[] = $state([]);
	let loadingFiles = $state(false);
	let uploadingFile = $state(false);

	async function submitQuery(useStream = false) {
		if (!query.trim() || loading) return;

		try {
			loading = true;
			streaming = useStream;
			response = '';

			if (useStream) {
				const res = await fetch(`/api/rag/${ragName}/stream`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ query: query.trim() })
				});

				if (!res.ok) throw new Error('Failed to stream response');

				const reader = res.body?.getReader();
				if (!reader) throw new Error('No response body');

				const decoder = new TextDecoder();

				while (true) {
					const { done, value } = await reader.read();
					if (done) break;

					const chunk = decoder.decode(value);
					response += chunk;
				}
			} else {
				const res = await fetch(`/api/rag/${ragName}/query`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ query: query.trim() })
				});

				if (!res.ok) throw new Error('Failed to get response');
				const data = await res.json();
				response = data.response || data.answer || 'No response received';
			}
		} catch (err) {
			response = `Error: ${err instanceof Error ? err.message : 'Unknown error'}`;
		} finally {
			loading = false;
			streaming = false;
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

			// Rebuild the RAG index
			const rebuildRes = await fetch(`/api/rag/${ragName}`, { method: 'POST' });
			if (!rebuildRes.ok) throw new Error('Failed to rebuild RAG index');

			loadFiles();
		} catch (err) {
			alert(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			uploadingFile = false;
			input.value = '';
		}
	}

	async function deleteFile(filename: string) {
		if (!confirm(`Delete ${filename}?`)) return;

		try {
			const res = await fetch(`/api/rag/${ragName}/files/${filename}`, { method: 'DELETE' });
			if (!res.ok) throw new Error('Failed to delete file');

			// Rebuild the RAG index
			const rebuildRes = await fetch(`/api/rag/${ragName}`, { method: 'POST' });
			if (!rebuildRes.ok) throw new Error('Failed to rebuild RAG index');

			loadFiles();
		} catch (err) {
			alert(`Delete failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
		}
	}

	// Load files when component mounts or ragName changes
	$effect(() => {
		if (ragName) {
			loadFiles();
		}
	});
</script>

<div class="space-y-8">
	<!-- Query Section -->
	<div class="glass rounded-2xl shadow-2xl overflow-hidden">
		<div class="p-6 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
			<h2 class="text-xl font-bold text-slate-100">
				Query RAG: <span class="text-cyan-400">{ragName}</span>
			</h2>
		</div>
		<div class="p-6">
			<div class="space-y-6">
				<div>
					<label for="query" class="block text-sm font-medium text-slate-200 mb-3">
						Ask a question about your documents
					</label>
					<textarea
						id="query"
						bind:value={query}
						placeholder="What would you like to know about your documents?"
						class="w-full px-4 py-4 bg-slate-700 border border-slate-600 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent resize-none transition-all duration-200"
						rows="4"
						onkeydown={(e) => {
							if (e.key === 'Enter' && !e.shiftKey) {
								e.preventDefault();
								submitQuery();
							}
						}}
					></textarea>
				</div>

				<div class="flex space-x-4">
					<button
						onclick={() => submitQuery(false)}
						disabled={!query.trim() || loading}
						class="group flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-cyan-500/25 cursor-pointer"
					>
						{#if loading && !streaming}
							<Loader class="w-5 h-5 animate-spin" />
						{:else}
							<Send class="w-5 h-5 group-hover:translate-x-1 transition-transform duration-200" />
						{/if}
						<span>Ask</span>
					</button>

					<button
						onclick={() => submitQuery(true)}
						disabled={!query.trim() || loading}
						class="group flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-green-500/25 cursor-pointer"
					>
						{#if loading && streaming}
							<Loader class="w-5 h-5 animate-spin" />
						{:else}
							<Zap class="w-5 h-5 group-hover:scale-110 transition-transform duration-200" />
						{/if}
						<span>Stream</span>
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- Response Section -->
	{#if response}
		<div class="glass rounded-2xl shadow-2xl overflow-hidden">
			<div class="p-6 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
				<h3 class="text-xl font-bold text-slate-100">Response</h3>
			</div>
			<div class="p-6">
				<div class="bg-slate-800/50 rounded-xl p-6 border border-slate-600">
					<pre class="whitespace-pre-wrap text-slate-200 font-mono text-sm leading-relaxed">{response}</pre>
				</div>
			</div>
		</div>
	{/if}

	<!-- Files Management -->
	<div class="glass rounded-2xl shadow-2xl overflow-hidden">
		<div class="p-6 border-b border-slate-600 bg-gradient-to-r from-slate-800 to-slate-700">
			<div class="flex justify-between items-center">
				<h3 class="text-xl font-bold text-slate-100 flex items-center space-x-3">
					<FileText class="w-6 h-6 text-cyan-400" />
					<span>Documents</span>
				</h3>
				<label class="group flex items-center space-x-3 px-4 py-2 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white rounded-xl cursor-pointer text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-cyan-500/25">
					{#if uploadingFile}
						<Loader class="w-5 h-5 animate-spin" />
						<span>Uploading...</span>
					{:else}
						<Upload class="w-5 h-5 group-hover:-translate-y-1 transition-transform duration-200" />
						<span>Add File</span>
					{/if}
					<input
						type="file"
						class="hidden"
						onchange={uploadFile}
						accept=".txt,.pdf,.docx,.md"
						disabled={uploadingFile}
					/>
				</label>
			</div>
		</div>
		<div class="divide-y divide-slate-600">
			{#if loadingFiles}
				<div class="p-8 text-center">
					<Loader class="w-8 h-8 animate-spin text-cyan-400 mx-auto mb-3" />
					<p class="text-slate-400">Loading files...</p>
				</div>
			{:else if files.length === 0}
				<div class="p-8 text-center">
					<FileText class="w-16 h-16 text-slate-600 mx-auto mb-4" />
					<p class="text-slate-300 font-medium">No documents in this RAG</p>
					<p class="text-slate-500 text-sm mt-1">Upload some files to get started</p>
				</div>
			{:else}
				{#each files as file (file)}
					<div class="p-4 flex items-center justify-between hover:bg-slate-700/30 transition-all duration-200 group">
						<div class="flex items-center space-x-4">
							<FileText class="w-6 h-6 text-cyan-400" />
							<span class="text-slate-200 group-hover:text-cyan-300 transition-colors">{file}</span>
						</div>
						<button
							onclick={() => deleteFile(file)}
							class="p-2 text-slate-500 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-all duration-200 cursor-pointer"
							title="Delete file"
						>
							<Trash2 class="w-5 h-5" />
						</button>
					</div>
				{/each}
			{/if}
		</div>
	</div>
</div>
