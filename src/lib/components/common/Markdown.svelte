<script lang="ts">
	import { marked, type RendererObject } from 'marked';
	import DOMPurify from 'dompurify';
	import { getHighlighter, highlightCode, detectLanguage } from '$lib/stores/shiki-highlighter.js';
	import { onMount } from 'svelte';

	interface Props {
		content: string;
	}

	let { content }: Props = $props();

	let htmlContent = $state('');
	let highlighterReady = $state(false);

	onMount(async () => {
		try {
			await getHighlighter();
			highlighterReady = true;
		} catch (error) {
			console.error('Failed to initialize Shiki highlighter:', error);
		}
	});

	function copyToClipboard(code: string, buttonElement: HTMLElement) {
		navigator.clipboard.writeText(code);
		const initialHTML = buttonElement.innerHTML;
		buttonElement.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
		setTimeout(() => {
			buttonElement.innerHTML = initialHTML;
		}, 2000);
	}

	const renderer: Partial<RendererObject> = {
		code({ text, lang }) {
			const language = lang || detectLanguage(text);
			const buttonId = `copy-btn-${Math.random().toString(36).substring(2, 9)}`;

			if (!highlighterReady) {
				// Fallback for when highlighter is not ready
				const escapedCode = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
				return `
					<div class="code-block rounded-lg bg-slate-900 border border-slate-700 overflow-hidden my-4">
						<div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
							<span class="text-xs font-mono text-slate-400">${language}</span>
							<button data-copy-btn="${buttonId}" data-code="${text.replace(/"/g, '&quot;')}" title="Copy code" class="p-1 rounded-md hover:bg-slate-700 cursor-pointer">
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
							</button>
						</div>
						<pre class="p-4 text-sm overflow-x-auto"><code>${escapedCode}</code></pre>
					</div>
				`;
			}

			try {
				const highlighted = highlightCode(text, language);
				// Extract the code content from Shiki's output and wrap it with our UI
				const codeMatch = highlighted.match(/<pre[^>]*><code[^>]*>([\s\S]*?)<\/code><\/pre>/);
				const highlightedCode = codeMatch ? codeMatch[1] : text;

				return `
					<div class="code-block rounded-lg bg-slate-900 border border-slate-700 overflow-hidden my-4">
						<div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
							<span class="text-xs font-mono text-slate-400">${language}</span>
							<button data-copy-btn="${buttonId}" data-code="${text.replace(/"/g, '&quot;')}" title="Copy code" class="p-1 rounded-md hover:bg-slate-700 cursor-pointer">
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
							</button>
						</div>
						<div class="shiki-container">
							<pre class="p-4 text-sm overflow-x-auto !bg-transparent"><code>${highlightedCode}</code></pre>
						</div>
					</div>
				`;
			} catch (error) {
				console.error('Shiki highlighting failed:', error);
				// Fallback to plain code
				const escapedCode = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
				return `
					<div class="code-block rounded-lg bg-slate-900 border border-slate-700 overflow-hidden my-4">
						<div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
							<span class="text-xs font-mono text-slate-400">${language}</span>
							<button data-copy-btn="${buttonId}" data-code="${text.replace(/"/g, '&quot;')}" title="Copy code" class="p-1 rounded-md hover:bg-slate-700 cursor-pointer">
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
							</button>
						</div>
						<pre class="p-4 text-sm overflow-x-auto"><code>${escapedCode}</code></pre>
					</div>
				`;
			}
		}
	};

	$effect(() => {
		async function renderMarkdown() {
			if (content) {
				marked.use({ renderer });
				const parsed = await marked.parse(content, { breaks: true, gfm: true });
				htmlContent = DOMPurify.sanitize(parsed);

				// Setup copy button listeners after DOM update
				setTimeout(() => {
					const buttons = document.querySelectorAll('[data-copy-btn]');
					buttons.forEach(button => {
						const code = button.getAttribute('data-code');
						if (code) {
							button.addEventListener('click', () => copyToClipboard(code, button as HTMLElement));
						}
					});
				}, 0);
			} else {
				htmlContent = '';
			}
		}
		renderMarkdown();
	});
</script>

<div class="markdown-content">
	{@html htmlContent}
</div>

<style>
	:global {
		.markdown-content h1,
		.markdown-content h2,
		.markdown-content h3,
		.markdown-content h4 {
			color: var(--text-secondary);
		}

		.markdown-content a {
			color: var(--accent-cyan);
			text-decoration: none;
		}

		.markdown-content a:hover {
			text-decoration: underline;
		}

		.markdown-content li::marker {
			color: var(--accent-cyan);
		}

		.markdown-content strong {
			color: var(--text-secondary);
		}

		.markdown-content code {
			background-color: var(--bg-tertiary);
			color: var(--accent-cyan);
			border-radius: 0.375rem;
			padding: 0.125rem 0.25rem;
			font-size: 0.825rem;
		}

		.markdown-content pre code {
			background: none;
			color: unset;
		}

		.markdown-content blockquote {
			border-left: 1rem solid var(--border-color);
			padding-left: 1rem;
			font-style: italic;
			color: var(--text-muted);
		}

		/* Shiki specific styles */
		.markdown-content .shiki-container pre {
			margin: 0;
			background: transparent !important;
		}

		.markdown-content .shiki-container code {
			background: none !important;
			padding: 0 !important;
			border-radius: 0 !important;
		}
	}
</style>
