import { createHighlighter, type Highlighter, type BundledLanguage, type BundledTheme } from 'shiki';

// Single, alphabetically sorted list of supported languages
const supportedLanguages: BundledLanguage[] = [
	'apache',
	'bash',
	'c',
	'cpp',
	'csharp',
	'css',
	'dart',
	'diff',
	'dockerfile',
	'go',
	'graphql',
	'html',
	'ini',
	'java',
	'javascript',
	'json',
	'jsx',
	'kotlin',
	'latex',
	'less',
	'markdown',
	'matlab',
	'nginx',
	'php',
	'postcss',
	'prisma',
	'python',
	'regex',
	'r',
	'ruby',
	'rust',
	'sass',
	'scss',
	'shell',
	'sql',
	'svelte',
	'swift',
	'stylus',
	'toml',
	'tsx',
	'typescript',
	'vue',
	'xml',
	'yaml',
	'git-commit'
];

const themes: BundledTheme[] = ['github-dark', 'github-light'];

let highlighterInstance: Highlighter | null = null;

export async function getHighlighter(): Promise<Highlighter> {
	if (!highlighterInstance) {
		highlighterInstance = await createHighlighter({
			langs: supportedLanguages,
			themes
		});
	}
	return highlighterInstance;
}

export function highlightCode(code: string, lang: string, theme: BundledTheme = 'github-dark'): string {
	if (!highlighterInstance) {
		throw new Error('Highlighter not initialized. Call getHighlighter() first.');
	}

	// Auto-detect language if not provided or empty
	const detectedLang = lang || detectLanguage(code);

	// Normalize language name
	const normalizedLang = normalizeLangName(detectedLang);

	// Check if language is supported
	const isSupported = supportedLanguages.includes(normalizedLang as BundledLanguage);

	if (!isSupported) {
		console.warn(`Language "${detectedLang}" not supported, falling back to plaintext`);
		return highlighterInstance.codeToHtml(code, {
			lang: 'text',
			theme
		});
	}

	return highlighterInstance.codeToHtml(code, {
		lang: normalizedLang as BundledLanguage,
		theme
	});
}

function detectLanguage(code: string): string {
	const trimmedCode = code.trim();

	// JSON detection
	if ((trimmedCode.startsWith('{') && trimmedCode.endsWith('}')) ||
		(trimmedCode.startsWith('[') && trimmedCode.endsWith(']'))) {
		try {
			JSON.parse(trimmedCode);
			return 'json';
		} catch {
			// Not valid JSON, continue detection
		}
	}

	// HTML detection
	if (trimmedCode.includes('<!DOCTYPE') ||
		trimmedCode.match(/<html|<head|<body|<div|<span|<p|<h[1-6]|<img|<a/i)) {
		return 'html';
	}

	// CSS detection
	if (trimmedCode.includes('{') && trimmedCode.includes('}') &&
		trimmedCode.match(/[.#][\w-]+\s*{|@media|@import|@keyframes/)) {
		return 'css';
	}

	// Python detection
	if (trimmedCode.match(/^(def |class |import |from |if __name__|print\()/m) ||
		trimmedCode.includes('def ') || trimmedCode.includes('import ')) {
		return 'python';
	}

	// JavaScript/TypeScript detection
	if (trimmedCode.match(/^(function |const |let |var |class |import |export)/m) ||
		trimmedCode.includes('console.log') || trimmedCode.includes('=>')) {
		// Check for TypeScript specific syntax
		if (trimmedCode.match(/:\s*(string|number|boolean|any|void|undefined|null)/)) {
			return 'typescript';
		}
		return 'javascript';
	}

	// Shell/Bash detection
	if (trimmedCode.match(/^#!/) || trimmedCode.match(/^\$\s/) ||
		trimmedCode.includes('echo ') || trimmedCode.includes('cd ') ||
		trimmedCode.includes('ls ') || trimmedCode.includes('grep ')) {
		return 'bash';
	}

	// SQL detection
	if (trimmedCode.match(/^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s/im)) {
		return 'sql';
	}

	// YAML detection
	if (trimmedCode.match(/^[\w-]+:\s*$/m) || trimmedCode.match(/^-\s+\w/m)) {
		return 'yaml';
	}

	// Dockerfile detection
	if (trimmedCode.match(/^(FROM|RUN|COPY|ADD|WORKDIR|EXPOSE|CMD|ENTRYPOINT)\s/im)) {
		return 'dockerfile';
	}

	// XML detection
	if (trimmedCode.match(/<\?xml|<\w+[^>]*>/)) {
		return 'xml';
	}

	// Markdown detection
	if (trimmedCode.match(/^#{1,6}\s|^```|^\*\s|^-\s|^\d+\.\s/m)) {
		return 'markdown';
	}

	// Default to text if no language detected
	return 'text';
}

// Map aliases to the canonical language names in supportedLanguages
const langMap: Record<string, BundledLanguage> = {
	'c#': 'csharp',
	'c++': 'cpp',
	'cs': 'csharp',
	'docker': 'dockerfile',
	'env': 'ini',
	'gitignore': 'ini',
	'js': 'javascript',
	'jsx': 'jsx',
	'kt': 'kotlin',
	'ps1': 'bash',
	'powershell': 'bash',
	'py': 'python',
	'rb': 'ruby',
	'react': 'jsx',
	'rs': 'rust',
	'sh': 'bash',
	'swift': 'swift',
	'tex': 'latex',
	'ts': 'typescript',
	'tsx': 'tsx',
	'yml': 'yaml',
	'zsh': 'bash',
};

function normalizeLangName(lang: string): string {
	return langMap[lang.toLowerCase()] || lang.toLowerCase();
}

export { supportedLanguages, themes, detectLanguage };
