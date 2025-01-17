const API_BASE = 'http://localhost:8080';

export async function getApiKey() {
    const response = await fetch(`${API_BASE}/api/settings/api-key`);
    if (!response.ok) throw new Error('Failed to fetch API key');
    const data = await response.json();
    return data.api_key;
}

export async function setApiKey(api_key: string) {
    const response = await fetch(`${API_BASE}/api/settings/api-key`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ api_key }),
    });
    if (!response.ok) throw new Error('Failed to set API key');
    return response.json();
}

export async function checkApiKeyStatus() {
    const response = await fetch(`${API_BASE}/api/settings/api-key-status`);
    if (!response.ok) throw new Error('Failed to check API key status');
    return response.json();
}

export async function getPowerLimit() {
    const response = await fetch(`${API_BASE}/api/settings/power-limit`);
    if (!response.ok) throw new Error('Failed to fetch power limit');
    return await response.json();
}

export async function setPowerLimit(power_limit: number) {
    const response = await fetch(`${API_BASE}/api/settings/power-limit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ power_limit }),
    });
    if (!response.ok) throw new Error('Failed to set power limit');
    return response.json();
} 