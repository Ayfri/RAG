<script lang="ts">
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';

	interface Props {
		content: string;
	}

	let { content }: Props = $props();

	let htmlContent = $state('');

	$effect(() => {
		async function renderMarkdown() {
			if (content) {
				const parsed = await marked.parse(content);
				htmlContent = DOMPurify.sanitize(parsed);
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
	prose-code:bg-slate-700 prose-code:text-slate-100 prose-code:rounded-md prose-code:px-1 prose-code:py-0.5
	prose-pre:bg-slate-700 prose-pre:text-slate-100 prose-pre:rounded-lg prose-pre:p-4
	prose-blockquote:border-l-4 prose-blockquote:border-slate-500 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-slate-400
">
	{@html htmlContent}
</div>
