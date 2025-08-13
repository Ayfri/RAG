// Centralized UI event dispatch helpers

export type AppEventName =
	| 'messageAdded'
	| 'messageEdited'
	| 'messageDeleted'
	| 'messagesCleared'
	| 'sessionCreated'
	| 'sessionDeleted'
	| 'sessionRenamed'
	| 'sessionSelected';

export function dispatchUI(eventName: AppEventName, detail: any): void {
	window.dispatchEvent(new CustomEvent(eventName, { detail }));
}

export const uiEvents = {
	messageAdded: (ragName: string, sessionId: string) =>
		dispatchUI('messageAdded', { ragName, sessionId }),
	messageEdited: (ragName: string, sessionId: string) =>
		dispatchUI('messageEdited', { ragName, sessionId }),
	messageDeleted: (ragName: string, sessionId: string) =>
		dispatchUI('messageDeleted', { ragName, sessionId }),
	messagesCleared: (ragName: string, sessionId: string) =>
		dispatchUI('messagesCleared', { ragName, sessionId }),
	sessionCreated: (ragName: string, sessionId: string) =>
		dispatchUI('sessionCreated', { ragName, sessionId }),
	sessionDeleted: (ragName: string, sessionId: string) =>
		dispatchUI('sessionDeleted', { ragName, sessionId }),
	sessionRenamed: (ragName: string, sessionId: string, newTitle: string) =>
		dispatchUI('sessionRenamed', { ragName, sessionId, newTitle }),
	sessionSelected: (ragName: string, sessionId: string, messages: any) =>
		dispatchUI('sessionSelected', { ragName, sessionId, messages })
};
