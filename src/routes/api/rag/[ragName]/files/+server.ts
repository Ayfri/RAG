import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const API_BASE_URL = 'http://localhost:8000';

export const GET: RequestHandler = async ({ params }) => {
	try {
		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/files`);

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to list files');
		}

		const data = await response.json();
		return json(data);
	} catch (err) {
		console.error('Error listing files:', err);
		return error(500, 'Internal server error');
	}
};

export const POST: RequestHandler = async ({ params, request }) => {
	try {
		const contentType = request.headers.get('content-type');
		let response;

		if (contentType?.includes('application/json')) {
			// This is a folder creation request
			const body = await request.json();
			response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/files`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(body)
			});
		} else if (contentType?.includes('multipart/form-data')) {
			// This is a file upload request
			const formData = await request.formData();

			// Forward FormData directly to the backend
			response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/files`, {
				method: 'POST',
				// SvelteKit automatically sets Content-Type for FormData, including boundary
				body: formData
			});
		} else {
			return error(400, 'Unsupported Content-Type');
		}

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to process request');
		}

		const data = await response.json();
		return json(data);
	} catch (err) {
		console.error('Error in POST /api/rag/[ragName]/files:', err);
		return error(500, 'Internal server error');
	}
};
