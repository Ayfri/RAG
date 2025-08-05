import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { API_BASE_URL } from '$lib/constants';

export const POST: RequestHandler = async ({ params, request }) => {
	try {
		const body = await request.json();

		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/symlink`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(body)
		});

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to create symbolic link');
		}

		const data = await response.json();
		return json(data);
	} catch (err) {
		console.error('Error creating symbolic link:', err);
		return error(500, 'Internal server error');
	}
};
