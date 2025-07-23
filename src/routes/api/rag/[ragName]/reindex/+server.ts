import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const API_BASE_URL = 'http://localhost:8000';

export const POST: RequestHandler = async ({ params }) => {
	try {
		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/reindex`, {
			method: 'POST'
		});

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to reindex RAG');
		}

		const data = await response.json();
		return json(data);
	} catch (err) {
		console.error('Error reindexing RAG:', err);
		return error(500, 'Internal server error');
	}
};
