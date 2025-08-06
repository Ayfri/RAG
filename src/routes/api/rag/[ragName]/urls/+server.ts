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
			let errorMessage = 'Failed to add URL';

			try {
				// Try to parse as JSON first (FastAPI returns JSON errors)
				const errorData = await response.json();
				errorMessage = errorData.detail || errorMessage;
			} catch {
				// If JSON parsing fails, try to get text
				try {
					const errorText = await response.text();
					errorMessage = errorText || errorMessage;
				} catch {
					// If all else fails, use status text
					errorMessage = response.statusText || errorMessage;
				}
			}

			// Return error with just the message text, not wrapped in JSON
			return new Response(errorMessage, {
				status: response.status,
				headers: { 'Content-Type': 'text/plain' }
			});
		}

		const data = await response.json();
		return json(data, { status: 201 });
	} catch (err) {
		// Don't catch HttpError from SvelteKit's error() function
		if (err && typeof err === 'object' && 'status' in err && 'body' in err) {
			throw err; // Re-throw HttpError
		}
		return new Response('Internal server error', {
			status: 500,
			headers: { 'Content-Type': 'text/plain' }
		});
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
			let errorMessage = 'Failed to delete URL';

			try {
				// Try to parse as JSON first (FastAPI returns JSON errors)
				const errorData = await response.json();
				errorMessage = errorData.detail || errorMessage;
			} catch {
				// If JSON parsing fails, try to get text
				try {
					const errorText = await response.text();
					errorMessage = errorText || errorMessage;
				} catch {
					// If all else fails, use status text
					errorMessage = response.statusText || errorMessage;
				}
			}

			return error(response.status, errorMessage);
		}

		return new Response(null, { status: 204 });
	} catch (err) {
		console.error('Error deleting URL:', err);
		return error(500, 'Internal server error');
	}
};
