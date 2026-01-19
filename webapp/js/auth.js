// Authentication module for Telegram WebApp

let userData = null;

async function initAuth() {
    try {
        // Check if Telegram WebApp is available
        if (!window.Telegram || !window.Telegram.WebApp) {
            throw new Error('Telegram WebApp is not available');
        }

        const tg = window.Telegram.WebApp;
        
        // Get initData from Telegram
        const initData = tg.initData;
        
        if (!initData) {
            throw new Error('No initData available');
        }

        // Set initData in API client
        api.setInitData(initData);

        // Validate initData with backend
        try {
            const validationResponse = await api.validateInitData(initData);
            userData = validationResponse.user;
            
            // Telegram WebApp ready
            tg.ready();
            tg.expand();
            
            return true;
        } catch (error) {
            console.error('InitData validation failed:', error);
            showToast('Authentication failed', 'error');
            return false;
        }
    } catch (error) {
        console.error('Auth initialization failed:', error);
        showToast('Failed to initialize app', 'error');
        return false;
    }
}

function getUserData() {
    return userData;
}

function getTelegramId() {
    return userData?.id;
}
