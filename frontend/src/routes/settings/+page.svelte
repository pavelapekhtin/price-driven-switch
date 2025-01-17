<script lang="ts">
	import {
		checkApiKeyStatus,
		getApiKey,
		getPowerLimit,
		setApiKey,
		setPowerLimit
	} from '$lib/api/client';
	import { onMount } from 'svelte';

	let tibber_api_token = '';
	let auth_status: 'pending' | 'authorized' | 'unauthorized' = 'pending';
	let loading = false;
	let error = '';

	let power_limit = 0;
	let power_limit_error = '';
	let power_limit_loading = false;

	onMount(async () => {
		try {
			const [key, limit] = await Promise.all([getApiKey(), getPowerLimit()]);
			tibber_api_token = key;
			power_limit = limit;
			await validateApiKey();
		} catch (e) {
			error = 'Failed to load settings';
		}
	});

	// FIXME: this one should only run again if the value of tibber_api_token has changed
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

	async function handlePowerLimitSave() {
		power_limit_loading = true;
		power_limit_error = '';

		try {
			await setPowerLimit(power_limit);
		} catch (e) {
			power_limit_error = 'Failed to save power limit';
		} finally {
			power_limit_loading = false;
		}
	}
</script>

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

<div class="settings-section">
	<h2>Power Limit (kW)</h2>
	<div class="input-group">
		<div class="number-input">
			<button
				on:click={() => (power_limit = Math.max(0, power_limit - 1))}
				class="stepper"
				disabled={power_limit_loading}>-</button
			>
			<input
				type="number"
				bind:value={power_limit}
				min="0"
				step="1"
				class="power-input"
				disabled={power_limit_loading}
			/>
			<button
				on:click={() => (power_limit = power_limit + 1)}
				class="stepper"
				disabled={power_limit_loading}>+</button
			>
		</div>
		<button on:click={handlePowerLimitSave} disabled={power_limit_loading}> Save </button>
	</div>

	{#if power_limit_error}
		<p class="error">{power_limit_error}</p>
	{/if}
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

	.number-input {
		display: flex;
		align-items: center;
		flex: 1;
	}

	.power-input {
		flex: 1;
		border: 1px solid #ccc;
		border-radius: 4px;
		text-align: center;
		font-size: 1.5rem;
		font-family: monospace;
	}

	.stepper {
		padding: 0.5rem 1.9rem;
		background: #f5f5f5;
		color: #333;
		border: 1px solid #ccc;
		cursor: pointer;
	}

	.stepper:first-child {
		border-radius: 4px;
		background-color: #9ddeb2;
	}

	.stepper:last-child {
		border-radius: 4px;
		background-color: #f3898d;
	}

	.stepper:hover:not(:disabled) {
		background: #e0e0e0;
	}

	input[type='number']::-webkit-inner-spin-button,
	input[type='number']::-webkit-outer-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}
</style>
