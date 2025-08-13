<script lang="ts">
	import { Check, ChevronDown } from '@lucide/svelte';
	import type { Snippet } from 'svelte';

	interface Option {
		label: string;
		value: string;
	}

	interface Props {
		class?: string;
		disabled?: boolean;
		id?: string;
		item?: Snippet<[Option, { highlighted: boolean; selected: boolean }]>;
		onchange?: (e: Event) => void;
		options: Option[];
		placeholder?: string;
		value?: string;
	}

	let {
		class: className = '',
		disabled,
		id,
		item,
		onchange,
		options,
		placeholder,
		value = $bindable()
	}: Props = $props();

	let isOpen = $state(false);
	let highlightedIndex = $state(-1);
	let rootEl: HTMLDivElement | null = null;

	const sortedOptions = () => options.toSorted((a, b) => a.label.localeCompare(b.label));

	function findIndexByValue(v: string | undefined) {
		return sortedOptions().findIndex(o => o.value === v);
	}

	function selectByIndex(index: number) {
		const opts = sortedOptions();
		if (index < 0 || index >= opts.length) return;
		const selected = opts[index];
		value = selected.value;
		emitChange();
		isOpen = false;
	}

	function emitChange() {
		const e = new Event('change') as Event & { target: { value: string } };
		(e as any).target = { value };
		onchange?.(e);
	}

	function toggleOpen() {
		if (disabled) return;
		isOpen = !isOpen;
		if (isOpen) highlightedIndex = Math.max(findIndexByValue(value), 0);
	}

	function close() {
		isOpen = false;
	}

	function onKeyDown(e: KeyboardEvent) {
		if (disabled) return;
		const opts = sortedOptions();
		switch (e.key) {
			case 'ArrowDown': {
				e.preventDefault();
				if (!isOpen) {
					isOpen = true;
					highlightedIndex = Math.max(findIndexByValue(value), 0);
					return;
				}
				highlightedIndex = Math.min((highlightedIndex < 0 ? -1 : highlightedIndex) + 1, opts.length - 1);
				break;
			}
			case 'ArrowUp': {
				e.preventDefault();
				if (!isOpen) {
					isOpen = true;
					highlightedIndex = Math.max(findIndexByValue(value), 0);
					return;
				}
				highlightedIndex = Math.max((highlightedIndex < 0 ? 0 : highlightedIndex) - 1, 0);
				break;
			}
			case 'Home':
				e.preventDefault();
				highlightedIndex = 0;
				break;
			case 'End':
				e.preventDefault();
				highlightedIndex = Math.max(opts.length - 1, 0);
				break;
			case 'Enter':
			case ' ': {
				e.preventDefault();
				if (!isOpen) {
					isOpen = true;
					highlightedIndex = Math.max(findIndexByValue(value), 0);
				} else if (highlightedIndex >= 0) {
					selectByIndex(highlightedIndex);
				}
				break;
			}
			case 'Escape':
				close();
				break;
		}
	}

	function onDocumentClick(e: MouseEvent) {
		if (!rootEl) return;
		if (!rootEl.contains(e.target as Node)) close();
	}

	$effect(() => {
		if (typeof window === 'undefined') return;
		window.addEventListener('click', onDocumentClick);
		return () => window.removeEventListener('click', onDocumentClick);
	});
</script>


<div class="relative w-full {className}" bind:this={rootEl}>
	<button
		aria-controls={id ? id + '-listbox' : undefined}
		aria-expanded={isOpen}
		aria-haspopup="listbox"
		class="w-full rounded-lg border border-slate-600 bg-slate-700/50 py-1.5 pl-3 text-left text-slate-100 transition-all duration-200 hover:bg-slate-700/80 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-cyan-500 disabled:cursor-not-allowed disabled:opacity-60"
		disabled={disabled}
		id={id}
		onclick={toggleOpen}
		onkeydown={onKeyDown}
		type="button"
	>
		<span>{sortedOptions().find(o => o.value === value)?.label ?? placeholder}</span>
		<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
			<ChevronDown size={18} />
		</div>
	</button>

	{#if isOpen}
		<ul
			id={id ? id + '-listbox' : undefined}
			class="absolute z-20 mt-1 max-h-92 w-full overflow-auto rounded-lg border border-slate-600 bg-slate-800 py-1 shadow-xl outline-none"
			role="listbox"
			tabindex="-1"
		>
			{#each sortedOptions() as option, i}
				<li role="none">
					<button
						aria-selected={option.value === value}
						class="flex w-full cursor-pointer select-none items-center gap-2 px-3 py-1.5 text-left text-slate-100 hover:bg-slate-700/60 {i === highlightedIndex ? 'bg-slate-700/60' : ''}"
						onclick={() => selectByIndex(i)}
						onkeydown={(e) => {
							if (e.key === 'Enter' || e.key === ' ') {
								e.preventDefault();
								selectByIndex(i);
							}
						}}
						onmousedown={(e) => e.preventDefault()}
						onmousemove={() => highlightedIndex = i}
						role="option"
						type="button"
					>
						{#if item}
							{@render item(option, { highlighted: i === highlightedIndex, selected: option.value === value })}
						{:else}
							<span class="truncate">{option.label}</span>
							{#if option.value === value}
								<Check class="ml-auto text-cyan-400" size={16} />
							{/if}
						{/if}
					</button>
				</li>
			{/each}
		</ul>
	{/if}
</div>
