import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const API_BASE = 'http://localhost:8000';

export const GET: RequestHandler = async ({ params, fetch }) => {
	const { ragName } = params;

	try {
		const response = await fetch(`${API_BASE}/rag/${ragName}/config`);

		if (!response.ok) {
			const error = await response.text();
			return json({ error }, { status: response.status });
		}

		const config = await response.json();
		return json(config);
	} catch (error) {
		console.error('Failed to get RAG config:', error);
		return json(
			{ error: 'Failed to get RAG configuration' },
			{ status: 500 }
		);
	}
};

export const PUT: RequestHandler = async ({ params, request, fetch }) => {
	const { ragName } = params;

	try {
		const config = await request.json();

		const response = await fetch(`${API_BASE}/rag/${ragName}/config`, {
			method: 'PUT',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(config),
		});

		if (!response.ok) {
			const error = await response.text();
			return json({ error }, { status: response.status });
		}

		const result = await response.json();
		return json(result);
	} catch (error) {
		console.error('Failed to update RAG config:', error);
		return json(
			{ error: 'Failed to update RAG configuration' },
			{ status: 500 }
		);
	}
};
