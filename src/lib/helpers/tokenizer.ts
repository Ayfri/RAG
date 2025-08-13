// Default import uses o200k_base which matches modern OpenAI models

import {encode} from 'gpt-tokenizer';

export function countTokensFromText(text: string): number {
	if (!text) return 0;
	try {
		return encode(text).length;
	} catch (err) {
		// Fallback: rough approximation ~4 chars per token
		const approx = Math.ceil(text.length / 4);
		return approx;
	}
}

export function countTokens(input: string | string[]): number {
	if (Array.isArray(input)) {
		const joined = input.join('\n');
		return countTokensFromText(joined);
	}
	return countTokensFromText(input);
}
