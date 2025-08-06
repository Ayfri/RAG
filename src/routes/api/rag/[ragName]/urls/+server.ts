import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { API_BASE_URL } from '$lib/constants';

export const GET: RequestHandler = async ({ params }) => {
	try {
		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/urls`);

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to list URLs');
		}

		const data = await response.json();
		return json(data);
	} catch (err) {
		console.error('Error listing URLs:', err);
		return error(500, 'Internal server error');
	}
};

export const POST: RequestHandler = async ({ params, request }) => {
	try {
		const body = await request.json();

		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/urls`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(body)
		});

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to add URL');
		}

		const data = await response.json();
		return json(data, { status: 201 });
	} catch (err) {
		console.error('Error adding URL:', err);
		return error(500, 'Internal server error');
	}
};

export const DELETE: RequestHandler = async ({ params, request }) => {
	try {
		const body = await request.json();

		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/urls`, {
			method: 'DELETE',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(body)
		});

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to delete URL');
		}

		return new Response(null, { status: 204 });
	} catch (err) {
		console.error('Error deleting URL:', err);
		return error(500, 'Internal server error');
	}
};
