import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const API_BASE_URL = 'http://localhost:8000';

export const POST: RequestHandler = async ({ params, request }) => {
	try {
		const body = await request.json();

		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/query`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(body)
		});

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to query RAG');
		}

		const data = await response.json();
		return json(data);
	} catch (err) {
		console.error('Error querying RAG:', err);
		return error(500, 'Internal server error');
	}
};
