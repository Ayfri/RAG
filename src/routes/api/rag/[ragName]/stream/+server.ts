import { error } from '@sveltejs/kit';

const API_BASE_URL = 'http://localhost:8000';

export async function POST({ params, request }: { params: { ragName: string }; request: Request }) {
	try {
		const body = await request.json();

		const response = await fetch(`${API_BASE_URL}/rag/${params.ragName}/stream`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(body)
		});

		if (!response.ok) {
			const errorText = await response.text();
			return error(response.status, errorText || 'Failed to stream from RAG');
		}

		// Return the streaming response as-is
		return new Response(response.body, {
			headers: {
				'Content-Type': 'text/plain',
				'Cache-Control': 'no-cache',
			}
		});
	} catch (err) {
		console.error('Error streaming from RAG:', err);
		return error(500, 'Internal server error');
	}
};
