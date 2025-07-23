<script lang="ts">
	import { Link, X, FolderOpen, FileText } from '@lucide/svelte';
	import Button from '$lib/components/common/Button.svelte';
	import Input from '$lib/components/common/Input.svelte';
	import Modal from '$lib/components/common/Modal.svelte';

	interface Props {
		ragName: string;
		isOpen: boolean;
		onClose: () => void;
		onSymlinkCreated: () => void;
	}

	let { ragName, isOpen, onClose, onSymlinkCreated }: Props = $props();

	let targetPath = $state('');
	let linkName = $state('');
	let loading = $state(false);
	let error = $state('');

	async function createSymlink() {
		if (!targetPath.trim() || !linkName.trim()) {
			error = 'Both target path and link name are required';
			return;
		}

		try {
			loading = true;
			error = '';

			const response = await fetch(`/api/rag/${ragName}/symlink`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					target_path: targetPath.trim(),
					link_name: linkName.trim()
				})
			});

			if (!response.ok) {
				const errorData = await response.text();
				throw new Error(errorData || 'Failed to create symbolic link');
			}

			// Reset form
			targetPath = '';
			linkName = '';

			onSymlinkCreated();
			onClose();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unknown error occurred';
		} finally {
			loading = false;
		}
	}

	function handleClose() {
		if (!loading) {
			targetPath = '';
			linkName = '';
			error = '';
			onClose();
		}
	}

	function suggestLinkName() {
		if (targetPath.trim()) {
			const path = targetPath.trim();
			const name = path.split(/[\\/]/).pop() || 'link';
			linkName = name;
		}
	}
</script>

{#if isOpen}
	<Modal onclose={handleClose} title="Create Symbolic Link">
	<div class="space-y-6">
		<div class="flex items-center space-x-3 text-slate-300 mb-4">
			<Link class="w-5 h-5 text-cyan-400" />
			<span class="text-sm">Create a symbolic link to an external file or directory</span>
		</div>

		{#if error}
			<div class="bg-red-900/20 border border-red-500 rounded-lg p-4">
				<p class="text-red-400 text-sm">{error}</p>
			</div>
		{/if}

		<div class="space-y-4">
			<div>
				<label for="target-path" class="block text-sm font-medium text-slate-200 mb-2">
					Target Path
				</label>
				<Input
					id="target-path"
					bind:value={targetPath}
					placeholder="C:\path\to\your\files or /path/to/your/files"
					class="w-full"
					onchange={suggestLinkName}
					disabled={loading}
				/>
				<p class="text-xs text-slate-400 mt-1">
					Absolute path to the file or directory you want to link to
				</p>
			</div>

			<div>
				<label for="link-name" class="block text-sm font-medium text-slate-200 mb-2">
					Link Name
				</label>
				<Input
					id="link-name"
					bind:value={linkName}
					placeholder="my-documents"
					class="w-full"
					disabled={loading}
				/>
				<p class="text-xs text-slate-400 mt-1">
					Name for the symbolic link in your RAG directory
				</p>
			</div>
		</div>

		<div class="bg-slate-800/50 border border-slate-600 rounded-lg p-4">
			<div class="flex items-start space-x-3">
				<FolderOpen class="w-5 h-5 text-cyan-400 mt-0.5 flex-shrink-0" />
				<div class="text-sm text-slate-300">
					<p class="font-medium mb-1">How symbolic links work:</p>
					<ul class="space-y-1 text-slate-400 list-disc list-inside text-xs">
						<li>Links reference files/folders outside your RAG directory</li>
						<li>LlamaIndex will automatically include linked content during indexing</li>
						<li>Changes to the original files will be reflected when you reindex</li>
						<li>Perfect for large document repositories or shared folders</li>
					</ul>
				</div>
			</div>
		</div>

		<div class="flex justify-end space-x-3 pt-4 border-t border-slate-600">
			<Button
				onclick={handleClose}
				disabled={loading}
				variant="secondary"
				class="cursor-pointer"
			>
				Cancel
			</Button>
			<Button
				onclick={createSymlink}
				disabled={loading || !targetPath.trim() || !linkName.trim()}
				variant="primary"
				class="cursor-pointer"
			>
				{loading ? 'Creating...' : 'Create Link'}
			</Button>
		</div>
	</div>
	</Modal>
{/if}
