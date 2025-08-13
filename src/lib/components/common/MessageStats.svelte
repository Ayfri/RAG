<script lang="ts">
	import {countTokensFromText, decodeSingleToken, encodeText} from '$lib/helpers/tokenizer';

	interface Props {
		class?: string;
		text: string;
		hideWhenEmpty?: boolean;
		targetElement?: HTMLElement;
		onVisualizationChange?: (active: boolean) => void;
	}

	let { class: className, hideWhenEmpty = true, onVisualizationChange, targetElement, text }: Props = $props();

	const chars = $derived(text?.length ?? 0);
	const tokens = $derived(countTokensFromText(text || ''));
	const isEmpty = $derived(!text || text.length === 0);

	let isActive = $state(false);
	let hoverTimer: number | null = null;
	let originalTextAreaDisabled = false;
	let originalTextAreaReadOnly = false;
	let originalCaretColor = '';
	let originalTextAreaVisibility = '';
	let parentOriginalPosition = '';
	let parentPositionChanged = false;
	let overlayEl: HTMLDivElement | null = null;
	let storedChildren: DocumentFragment | null = null;
	let previewEl: HTMLDivElement | null = null;

	function getTokenSpans(sourceText: string): string {
		const ids = encodeText(sourceText);
		const palette = [
			'#b91c1c', // red
			'#b45309', // orange
			'#eab308', // yellow
			'#15803d', // green
			'#0e7490', // teal
			'#0369a1', // blue
			'#6d28d9', // purple
			'#a21caf', // violet
		];
		const parts: string[] = [];
		for (let i = 0; i < ids.length; i++) {
			const t = decodeSingleToken(ids[i]);
			const color = palette[i % palette.length];
			const safe = t
				.replace(/&/g, '&amp;')
				.replace(/</g, '&lt;')
				.replace(/>/g, '&gt;');
            // Render token span without trimming spaces/newlines
            // Use white-space: pre to preserve spaces; display inline-block for stable layout
            parts.push(`<span style="background:${color}11;border:1px solid ${color}77;padding:1px 2px;border-radius:5px;display:inline-block;white-space:pre;">${safe.replace(/\n/g, '\\n')}</span>`);
			// If token contains newlines, force a visual line break. For consecutive newlines (\n\n),
			// also insert a spacer to render empty lines between paragraphs.
			const newlineCount = (t.match(/\n/g) || []).length;
			if (newlineCount > 0) {
				// first break moves to next line
				parts.push('<span style="flex:0 0 100%;height:0"></span>');
				// additional consecutive breaks add visible empty lines
				if (newlineCount > 1) {
					const spacerEm = newlineCount - 1;
					parts.push(`<span style="flex:0 0 100%;height:${spacerEm}em"></span>`);
				}
			}
		}
		// Flex filler to stabilize last row width and avoid accidental wrapping
		parts.push('<span style="flex:1 1 auto"></span>');
		return parts.join('');
	}

    function activate() {
		if (isActive) return;
		isActive = true;
		onVisualizationChange?.(true);
		if (!targetElement) return;
		if (targetElement instanceof HTMLTextAreaElement) {
			// Avoid toggling disabled to prevent focus/re-render loops in parent components
			originalTextAreaDisabled = targetElement.disabled;
			originalTextAreaReadOnly = targetElement.readOnly;
			originalCaretColor = targetElement.style.caretColor;
			originalTextAreaVisibility = targetElement.style.visibility;
			// Immediately hide textarea to avoid flash, and make it readonly (don’t toggle disabled to avoid re-render loops)
			targetElement.style.visibility = 'hidden';
			targetElement.readOnly = true;
			targetElement.disabled = false;
			targetElement.style.caretColor = 'transparent';

			// Create and position overlay to match the textarea's box
			const parent = (targetElement.offsetParent as HTMLElement) || targetElement.parentElement as HTMLElement;
			if (parent) {
				const computedParentPos = getComputedStyle(parent).position;
				if (computedParentPos === 'static') {
					parentOriginalPosition = parent.style.position;
					parent.style.position = 'relative';
					parentPositionChanged = true;
				}
				const rect = targetElement.getBoundingClientRect();
				const parentRect = parent.getBoundingClientRect();
				const left = rect.left - parentRect.left;
				const top = rect.top - parentRect.top;
				overlayEl = document.createElement('div');
				overlayEl.className = 'token-preview-overlay absolute overflow-auto font-mono text-sm pointer-events-none';
				overlayEl.style.left = `${left}px`;
				overlayEl.style.top = `${top}px`;
				overlayEl.style.width = `${rect.width}px`;
				overlayEl.style.height = `${rect.height}px`;
				// match padding, border, radius, bg to mimic the textarea fully
				const cs = getComputedStyle(targetElement);
				overlayEl.style.padding = cs.padding;
				overlayEl.style.borderRadius = cs.borderRadius;
				overlayEl.style.backgroundColor = cs.backgroundColor;
				overlayEl.style.border = cs.border;
				overlayEl.style.borderColor = cs.borderColor;
				overlayEl.style.boxShadow = cs.boxShadow;
				overlayEl.style.color = cs.color;
				overlayEl.style.zIndex = String((parseInt(cs.zIndex || '0', 10) || 0) + 1);
				overlayEl.innerHTML = getTokenSpans(targetElement.value || '');
				parent.appendChild(overlayEl);
			}
			return;
		}
		// For non-textarea elements, replace children with a single preview child
		storedChildren = document.createDocumentFragment();
		while (targetElement.firstChild) {
			storedChildren.appendChild(targetElement.firstChild);
		}
		previewEl = document.createElement('div');
		previewEl.className = 'token-preview flex flex-row flex-wrap items-start content-start gap-0 font-mono text-xs';
		previewEl.innerHTML = getTokenSpans(text || (targetElement as HTMLElement).innerText || '');
		targetElement.appendChild(previewEl);
	}

    function deactivate() {
		if (!isActive) return;
		isActive = false;
		onVisualizationChange?.(false);
		if (!targetElement) return;
		if (targetElement instanceof HTMLTextAreaElement) {
            // Local component state only; no global store
			// Restore original readOnly/disabled/caret
			targetElement.readOnly = originalTextAreaReadOnly;
			targetElement.disabled = originalTextAreaDisabled;
			targetElement.style.caretColor = originalCaretColor;
			targetElement.style.visibility = originalTextAreaVisibility;
			if (overlayEl && overlayEl.parentElement) {
				overlayEl.parentElement.removeChild(overlayEl);
			}
			overlayEl = null;
			const parent = (targetElement.offsetParent as HTMLElement) || targetElement.parentElement as HTMLElement;
			if (parent && parentPositionChanged) {
				parent.style.position = parentOriginalPosition;
				parentPositionChanged = false;
				parentOriginalPosition = '';
			}
			return;
		}
		// Restore original children for non-textarea elements
		if (previewEl && previewEl.parentElement === targetElement) {
			targetElement.removeChild(previewEl);
		}
		previewEl = null;
		if (storedChildren) {
			targetElement.appendChild(storedChildren);
			storedChildren = null;
		}
	}

	function handleEnter() {
		if (hoverTimer) window.clearTimeout(hoverTimer);
		hoverTimer = window.setTimeout(() => activate(), 600);
	}

	function handleLeave() {
		if (hoverTimer) {
			window.clearTimeout(hoverTimer);
			hoverTimer = null;
		}
		deactivate();
	}

	// Keep preview in sync if text changes while active
	$effect(() => {
		if (isActive && previewEl && !(targetElement instanceof HTMLTextAreaElement)) {
			previewEl.innerHTML = getTokenSpans(text || '');
		}
		if (isActive && overlayEl && targetElement instanceof HTMLTextAreaElement) {
			overlayEl.innerHTML = getTokenSpans((targetElement as HTMLTextAreaElement).value || '');
			// update size and position in case of layout changes
			const parent = (targetElement.offsetParent as HTMLElement) || targetElement.parentElement as HTMLElement;
			if (parent) {
				const rect = targetElement.getBoundingClientRect();
				const parentRect = parent.getBoundingClientRect();
				overlayEl.style.left = `${rect.left - parentRect.left}px`;
				overlayEl.style.top = `${rect.top - parentRect.top}px`;
				overlayEl.style.width = `${rect.width}px`;
				overlayEl.style.height = `${rect.height}px`;
			}
		}
	});

	// Safety: on destroy, restore children if needed
	$effect(() => () => {
		if (isActive) {
			deactivate();
		}
	});
</script>


{#if !hideWhenEmpty || !isEmpty}
	<span class="inline-flex items-center gap-1 text-xs {className || ''}"
		onpointerenter={handleEnter}
		onpointerleave={handleLeave}
	>
		<span>{chars.toLocaleString()} chars</span>
		<span>•</span>
		<span class:cursor-help={targetElement !== undefined}>{tokens.toLocaleString()} tokens</span>
	</span>
{/if}
