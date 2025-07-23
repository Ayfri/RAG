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

<div class="prose prose-invert prose-sm max-w-none
	prose-h1:text-slate-100 prose-h2:text-slate-100 prose-h3:text-slate-100 prose-h4:text-slate-100
	prose-a:text-cyan-400 prose-a:no-underline hover:prose-a:underline
	prose-p:text-slate-300
	prose-ul:text-slate-300 prose-ol:text-slate-300
	prose-li:marker:text-cyan-400
	prose-strong:text-slate-200
	prose-code:bg-slate-700 prose-code:text-cyan-400 prose-code:font-normal prose-code:rounded-md prose-code:px-1.5 prose-code:py-1
	prose-pre:hidden
	prose-blockquote:border-l-4 prose-blockquote:border-slate-500 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-slate-400
">
	{@html htmlContent}
</div>
