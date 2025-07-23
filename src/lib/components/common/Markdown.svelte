<script lang="ts">
	import { marked, type RendererObject } from 'marked';
	import DOMPurify from 'dompurify';

	interface Props {
		content: string;
	}

	let { content }: Props = $props();

	let htmlContent = $state('');
	const copyButtonId = `copy-button-${crypto.randomUUID()}`;

	function copyToClipboard(code: string, id: string) {
		navigator.clipboard.writeText(code);
		const button = document.getElementById(id);
		if (button) {
			const initialHTML = button.innerHTML;
			button.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
			setTimeout(() => {
				button.innerHTML = initialHTML;
			}, 2000);
		}
	}

	const renderer: Partial<RendererObject> = {
		code({ text, lang }) {
			const language = lang || 'plaintext';
			const id = `${copyButtonId}-${Math.random().toString(36).substring(2, 9)}`;

			const code = text.replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

			return `
			<div class="code-block rounded-lg bg-slate-900 border border-slate-700 overflow-hidden my-4">
				<div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
					<span class="text-xs font-mono text-slate-400">${language}</span>
					<button id="${id}" title="Copy code" class="p-1 rounded-md hover:bg-slate-700 cursor-pointer">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
					</button>
				</div>
				<pre class="p-4 text-sm overflow-x-auto"><code>${code}</code></pre>
			</div>
		`;
		}
	};

	$effect(() => {
		async function renderMarkdown() {
			if (content) {
				marked.use({ renderer });
				const parsed = await marked.parse(content, { breaks: true, gfm: true });
				htmlContent = DOMPurify.sanitize(parsed);

				setTimeout(() => {
					const buttons = document.querySelectorAll(`[id^="${copyButtonId}"]`);
					buttons.forEach(button => {
						const pre = button.closest('.code-block')?.querySelector('pre');
						if (pre && pre.textContent) {
							const code = pre.textContent;
							button.addEventListener('click', () => copyToClipboard(code, button.id));
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
	}
</style>
