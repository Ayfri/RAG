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
		const formData = await request.formData();

		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/files`, {
			method: 'POST',
			body: formData
		});

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to upload file');
		}

		const data = await response.json();
		return json(data);
	} catch (err) {
		console.error('Error uploading file:', err);
		return error(500, 'Internal server error');
	}
};
