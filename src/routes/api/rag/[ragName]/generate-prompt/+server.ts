import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { API_BASE_URL } from '$lib/constants';

export const POST: RequestHandler = async ({ params, request, fetch }) => {
	const { ragName } = params;

	try {
		const { description } = await request.json();

		if (!description || typeof description !== 'string') {
			return json(
				{ error: 'Description is required and must be a string' },
				{ status: 400 }
			);
		}

		// Call the backend API to generate the prompt
		const response = await fetch(`${API_BASE_URL}/rag/${ragName}/generate-prompt`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ description }),
		});

		if (!response.ok) {
			const error = await response.text();
			return json({ error }, { status: response.status });
		}

		const result = await response.json();
		return json(result);
	} catch (error) {
		console.error('Failed to generate prompt:', error);
		return json(
			{ error: 'Failed to generate system prompt' },
			{ status: 500 }
		);
	}
};
