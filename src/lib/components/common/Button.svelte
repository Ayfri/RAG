<script lang="ts">
	interface Props {
		children?: any;
		class?: string;
		disabled?: boolean;
		onclick?: (e: MouseEvent) => void;
		size?: 'default' | 'icon';
		type?: 'button' | 'submit' | 'reset';
		title?: string;
		variant?: 'primary' | 'secondary' | 'danger' | 'default';
	}

	let { disabled, onclick, variant = 'primary', size = 'default', type = 'button', class: className, children, title, ...rest }: Props = $props();

	const baseClasses = 'transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed';

	const sizeClasses = {
		default: 'px-4 py-2 rounded-xl font-medium text-base group flex items-center justify-center gap-2',
		icon: 'p-1.5 rounded-lg group'
	};

	const variantClasses = {
		primary: 'bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white',
		secondary: 'text-slate-400 hover:text-slate-200 hover:bg-slate-700',
		danger: 'text-slate-500 hover:text-red-400 hover:bg-red-900/20',
		default: 'text-slate-500 hover:text-cyan-400 hover:bg-cyan-900/20'
	};
</script>

<button
	class="{baseClasses} {sizeClasses[size]} {variantClasses[variant]} {className ?? ''}"
	{disabled}
	{onclick}
	{type}
	{title}
	{...rest}
>
	{@render children?.()}
</button>
