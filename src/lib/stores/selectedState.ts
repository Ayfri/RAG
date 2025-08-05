import { persistentStore } from './persistentStore';

// Store for selected RAG and session state
export interface SelectedState {
	ragName: string | null;
	sessionId: string | null;
}

export const selectedState = persistentStore<SelectedState>('selected-state', {
	ragName: null,
	sessionId: null
});
