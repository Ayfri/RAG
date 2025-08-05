import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { API_BASE_URL } from '$lib/constants';

export const GET: RequestHandler = async () => {
	try {
		const response = await fetch(`${API_BASE_URL}/rag`);

		if (!response.ok) {
			return error(response.status, 'Failed to fetch RAGs from backend');
		}

		const data = await response.json();
		return json(data);
	} catch (err) {
		console.error('Error fetching RAGs:', err);
		return error(500, 'Internal server error');
	}
};
