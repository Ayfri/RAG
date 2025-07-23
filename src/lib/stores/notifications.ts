import { writable } from 'svelte/store';

export interface Notification {
	id: string;
	message: string;
	type: 'info' | 'success' | 'warning' | 'error';
	duration?: number;
}

const { subscribe, update } = writable<Notification[]>([]);

function addNotification(notification: Omit<Notification, 'id'>) {
	const id = crypto.randomUUID();
	update(notifications => [...notifications, { ...notification, id }]);
}

function removeNotification(id: string) {
	update(notifications => notifications.filter(n => n.id !== id));
}

export const notifications = {
	subscribe,
	add: addNotification,
	remove: removeNotification,
	info: (message: string, duration?: number) => addNotification({ message, type: 'info', duration }),
	success: (message: string, duration?: number) => addNotification({ message, type: 'success', duration }),
	warning: (message: string, duration?: number) => addNotification({ message, type: 'warning', duration }),
	error: (message: string, duration?: number) => addNotification({ message, type: 'error', duration }),
};
