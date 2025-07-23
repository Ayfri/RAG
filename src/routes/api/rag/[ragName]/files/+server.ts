import { json, error } from '@sveltejs/kit';

const API_BASE_URL = 'http://localhost:8000';

export async function GET({ params }: { params: { ragName: string } }) {
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

export async function POST({ params, request }: { params: { ragName: string }; request: Request }) {
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
