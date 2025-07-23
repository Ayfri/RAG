import { json } from '@sveltejs/kit';

/**
 * GET /api/models
 *
 * Fetches available OpenAI models from the backend API, categorized by type.
 * Returns models organized into chat, embedding, and thinking categories.
 */
export async function GET() {
	try {
		const response = await fetch('http://localhost:8000/rag/models');

		if (!response.ok) {
			throw new Error(`Backend API error: ${response.status}`);
		}

		const models = await response.json();

		return json(models, {
			headers: {
				'Cache-Control': 'public, max-age=3600' // Cache for 1 hour
			}
		});
	} catch (error) {
		console.error('Failed to fetch OpenAI models:', error);

		return json(
			{ error: 'Failed to fetch OpenAI models' },
			{ status: 500 }
		);
	}
}
