<script lang="ts">
	import { checkApiKeyStatus, getApiKey, setApiKey } from '$lib/api/client';
	import { onMount } from 'svelte';

	let tibber_api_token = '';
	let auth_status: 'pending' | 'authorized' | 'unauthorized' = 'pending';
	let loading = false;
	let error = '';

	onMount(async () => {
		try {
			const key = await getApiKey();
			tibber_api_token = key;
			await validateApiKey();
		} catch (e) {
			error = 'Failed to load API key';
		}
	});

	async function validateApiKey() {
		if (!tibber_api_token) {
			auth_status = 'pending';
			return;
		}

		loading = true;
		error = '';

		try {
			const status = await checkApiKeyStatus();
			auth_status = status.status === 'ok' ? 'authorized' : 'unauthorized';
		} catch (e) {
			error = 'Failed to validate API key';
			auth_status = 'unauthorized';
		} finally {
			loading = false;
		}
	}

	async function handleSave() {
		loading = true;
		error = '';

		try {
			await setApiKey(tibber_api_token);
			await validateApiKey();
		} catch (e) {
			error = 'Failed to save API key';
		} finally {
			loading = false;
		}
	}
</script>

<h1>Settings</h1>

<div class="settings-section">
	<h2>Tibber API Token</h2>
	<div class="input-group">
		<input
			type="text"
			bind:value={tibber_api_token}
			class="api-input"
			placeholder="Enter your Tibber API token"
		/>
		<button on:click={handleSave} disabled={loading}>Save</button>
	</div>

	{#if error}
		<p class="error">{error}</p>
	{/if}

	<div class="status">
		{#if loading}
			<p class="loading">Validating...</p>
		{:else if auth_status === 'pending'}
			<p class="pending">Input API key</p>
		{:else if auth_status === 'authorized'}
			<p class="authorized">✓ Authorized</p>
		{:else}
			<p class="unauthorized">✗ Unauthorized, check API key</p>
		{/if}
	</div>
</div>

<style>
	.settings-section {
		max-width: 600px;
		margin: 2rem 0;
	}

	.input-group {
		display: flex;
		gap: 1rem;
		margin: 1rem 0;
	}

	.api-input {
		flex: 1;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-family: monospace;
	}

	button {
		padding: 0.5rem 1rem;
		background: #007aff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}

	button:disabled {
		background: #ccc;
	}

	.status {
		margin-top: 0.5rem;
	}

	.error {
		color: red;
		margin: 0.5rem 0;
	}

	.loading {
		color: #666;
	}

	.pending {
		color: orange;
	}

	.authorized {
		color: green;
	}

	.unauthorized {
		color: red;
	}
</style>
