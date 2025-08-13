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

// Convenience helpers to avoid duplication across components
export type FileFilters = { include: string[]; exclude: string[] };

export async function getRagFileFilters(ragName: string, key: string): Promise<FileFilters> {
	const config = await fetchRagConfig(ragName);
	const fileFilters = (config as any).file_filters ?? {};
	return (fileFilters[key] as FileFilters) ?? { include: ['**/*'], exclude: [] };
}

export async function setRagFileFilters(
	ragName: string,
	key: string,
	filters: FileFilters
): Promise<RagConfig> {
	const current = await fetchRagConfig(ragName);
	const currentFilters = (current as any).file_filters ?? {};
	const nextFilters = { ...currentFilters, [key]: filters };
	return updateRagConfig(ragName, { ...current, file_filters: nextFilters });
}
