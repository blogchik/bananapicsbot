// API Client for Banana Pics WebApp

class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL || 'http://localhost:9000/api/v1';
        this.initData = null;
    }

    setInitData(initData) {
        this.initData = initData;
    }

    async request(method, endpoint, data = null) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
        };

        // Add initData for authentication
        if (this.initData) {
            headers['X-Telegram-Init-Data'] = this.initData;
        }

        const options = {
            method,
            headers,
        };

        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Validate Telegram initData
    async validateInitData(initData) {
        return await this.request('POST', '/webapp/validate', { init_data: initData });
    }

    // User endpoints
    async getUserProfile(telegramId) {
        return await this.request('GET', `/users/${telegramId}/profile`);
    }

    async getUserBalance(telegramId) {
        return await this.request('GET', `/users/${telegramId}/balance`);
    }

    async getReferralInfo(telegramId) {
        return await this.request('GET', `/referrals/${telegramId}`);
    }

    // Models
    async getModels() {
        return await this.request('GET', '/models');
    }

    // Generation
    async getGenerationPrice(telegramId, modelId, params) {
        return await this.request('POST', '/generations/price', {
            telegram_id: telegramId,
            model_id: modelId,
            ...params
        });
    }

    async submitGeneration(telegramId, modelId, prompt, params, referenceUrls = []) {
        return await this.request('POST', '/generations/submit', {
            telegram_id: telegramId,
            model_id: modelId,
            prompt,
            reference_urls: referenceUrls,
            reference_file_ids: [],
            ...params
        });
    }

    async getGenerationStatus(requestId, telegramId) {
        return await this.request('POST', `/generations/${requestId}/refresh`, {
            telegram_id: telegramId
        });
    }

    async getGenerationResults(requestId, telegramId) {
        return await this.request('GET', `/generations/${requestId}/results?telegram_id=${telegramId}`);
    }

    // Media upload
    async uploadMedia(fileBytes, filename) {
        const formData = new FormData();
        formData.append('file', fileBytes, filename);

        const url = `${this.baseURL}/media/upload`;
        const headers = {};

        if (this.initData) {
            headers['X-Telegram-Init-Data'] = this.initData;
        }

        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const data = await response.json();
        return data.download_url;
    }
}

// Global API client instance
const api = new APIClient();
