<script lang="ts">
	import { page } from '$app/stores';
	import '../app.css';
	let { children } = $props();
</script>

<div class="layout">
	<nav>
		<div class="nav-content">
			<a href="/" class:active={$page.url.pathname === '/'}>Home</a>
			<a href="/settings" class:active={$page.url.pathname === '/settings'}>Settings</a>
		</div>
	</nav>

	<main>
		{@render children()}
	</main>
</div>

<style>
	.layout {
		display: flex;
		min-height: 100vh;
	}

	nav {
		width: 180px;
		background-color: #f5f5f5;
		border-right: 1px solid #e0e0e0;
		padding: 2rem 0;
		position: fixed;
		height: 100vh;
	}

	.nav-content {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		padding: 0 2rem;
	}

	nav a {
		font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
		font-weight: bold;
		text-decoration: none;
		color: #333;
		padding: 0.5rem 1rem;
		margin: 0 -1rem;
		border-radius: 6px;
		transition: all 0.2s ease;
	}

	nav a:hover {
		color: #007aff;
		background-color: #eaeaea;
	}

	nav a.active {
		background-color: #e0e0e0;
		color: #007aff;
	}

	main {
		flex: 1;
		margin-left: 240px;
		padding: 2rem;
	}
</style>
