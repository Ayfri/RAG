import type { RagConfig } from '$lib/types.d.ts';

export async function fetchRagConfig(ragName: string): Promise<RagConfig> {
	const response = await fetch(`/api/rag/${ragName}/config`, {
		headers: {
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'Expires': '0'
		}
	});

	if (!response.ok) {
		throw new Error('Failed to load RAG config');
	}

	return await response.json() as RagConfig;
}

export async function updateRagConfig(ragName: string, config: Partial<RagConfig>): Promise<RagConfig> {
	const response = await fetch(`/api/rag/${ragName}/config`, {
		method: 'PUT',
		headers: {
			'Content-Type': 'application/json',
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'Expires': '0'
		},
		body: JSON.stringify(config)
	});

	if (!response.ok) {
		throw new Error('Failed to update RAG config');
	}

	return await response.json() as RagConfig;
}
