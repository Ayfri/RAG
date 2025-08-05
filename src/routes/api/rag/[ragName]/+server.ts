import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { API_BASE_URL } from '$lib/constants';

export const POST: RequestHandler = async ({ params }) => {
	try {
		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}`, {
			method: 'POST'
		});

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to create RAG');
		}

		const data = await response.json();
		return json(data);
	} catch (err) {
		console.error('Error creating RAG:', err);
		return error(500, 'Internal server error');
	}
};

export const DELETE: RequestHandler = async ({ params }) => {
	try {
		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}`, {
			method: 'DELETE'
		});

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to delete RAG');
		}

		const data = await response.json();
		return json(data);
	} catch (err) {
		console.error('Error deleting RAG:', err);
		return error(500, 'Internal server error');
	}
};
