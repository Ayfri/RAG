import { json, error } from '@sveltejs/kit';

const API_BASE_URL = 'http://localhost:8000';

export async function DELETE({ params }: { params: { ragName: string; filename: string } }) {
	try {
		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/files/${params.filename}`, {
			method: 'DELETE'
		});

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to delete file');
		}

		const data = await response.json();
		return json(data);
	} catch (err) {
		console.error('Error deleting file:', err);
		return error(500, 'Internal server error');
	}
}
