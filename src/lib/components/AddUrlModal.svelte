<script lang="ts">
	import Button from '$lib/components/common/Button.svelte';
	import Input from '$lib/components/common/Input.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import {notifications} from '$lib/stores/notifications';
	import {AlertCircle, Check, Globe, Loader, Plus, X} from '@lucide/svelte';

	interface Props {
		ragName: string;
		onUrlAdded: () => void;
		open: boolean;
	}

	let { ragName, onUrlAdded, open = $bindable(false) }: Props = $props();

	let url = $state('');
	let loading = $state(false);
	let error = $state('');

	function reset() {
		url = '';
		error = '';
	}

	function validateUrl(urlString: string): boolean {
		try {
			const urlObj = new URL(urlString);
			return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
		} catch {
			return false;
		}
	}

	async function handleSubmit() {
		if (!url.trim()) {
			error = 'URL is required';
			return;
		}

		if (!validateUrl(url.trim())) {
			error = 'Please enter a valid HTTP or HTTPS URL';
			return;
		}

		try {
			loading = true;
			error = '';

			const response = await fetch(`/api/rag/${ragName}/urls`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ url: url.trim() })
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Failed to add URL');
			}

			notifications.success('URL added successfully!');
			onUrlAdded();
			open = false;
			reset();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to add URL';
		} finally {
			loading = false;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			handleSubmit();
		}
	}

	$effect(() => {
		if (open) {
			reset();
		}
	});
</script>

<Modal title="Add URL" bind:open size="lg">
	<div class="space-y-4">
		<div>
			<label for="url-input" class="block text-sm font-medium text-slate-300 mb-2">
				Website URL
			</label>
			<Input
				id="url-input"
				type="url"
				placeholder="https://example.com"
				bind:value={url}
				onkeydown={handleKeydown}
				disabled={loading}
				class="w-full"
			/>
			{#if error}
				<div class="flex items-center space-x-2 mt-2 text-red-400 text-sm">
					<AlertCircle size={16} />
					<span>{error}</span>
				</div>
			{/if}
		</div>

		<div class="flex items-center justify-end space-x-3 pt-4">
			<Button
				onclick={() => open = false}
				variant="secondary"
				disabled={loading}
			>
				<X size={16} />
				<span>Cancel</span>
			</Button>
			<Button
				onclick={handleSubmit}
				disabled={loading || !url.trim()}
				class="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
			>
				{#if loading}
					<Loader size={16} class="animate-spin" />
					<span>Adding...</span>
				{:else}
					<Globe size={16} />
					<span>Add URL</span>
				{/if}
			</Button>
		</div>
	</div>
</Modal>
