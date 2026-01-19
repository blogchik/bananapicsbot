// Main Application Logic

// State management
const appState = {
    currentPage: 'generation',
    userData: null,
    balance: 0,
    models: [],
};

// Initialize the application
async function initApp() {
    // Authenticate user
    const authSuccess = await initAuth();
    
    if (!authSuccess) {
        document.getElementById('loading-screen').innerHTML = 
            '<p style="color: #EF4444;">❌ Authentication Failed</p><p>Please reopen from Telegram bot</p>';
        return;
    }

    // Get user data
    appState.userData = getUserData();
    
    // Load models
    try {
        appState.models = await api.getModels();
    } catch (error) {
        console.error('Failed to load models:', error);
        showToast('Failed to load models', 'error');
    }

    // Load user balance
    await loadUserBalance();

    // Initialize pages
    initGenerationPage();
    initToolsPage();
    initProfilePage();

    // Set up navigation
    setupNavigation();

    // Hide loading screen and show app
    document.getElementById('loading-screen').style.display = 'none';
    document.getElementById('app').style.display = 'flex';
}

// Load user balance
async function loadUserBalance() {
    try {
        const telegramId = getTelegramId();
        const balanceData = await api.getUserBalance(telegramId);
        appState.balance = balanceData.balance || 0;
        updateBalanceDisplay();
    } catch (error) {
        console.error('Failed to load balance:', error);
    }
}

// Update balance display
function updateBalanceDisplay() {
    document.getElementById('header-balance').textContent = formatNumber(appState.balance);
}

// Navigation setup
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const pageName = item.dataset.page;
            
            // Update nav items
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Update pages
            pages.forEach(page => page.classList.remove('active'));
            document.getElementById(`page-${pageName}`).classList.add('active');

            appState.currentPage = pageName;

            // Reload page data if needed
            if (pageName === 'profile') {
                loadProfileData();
            }
        });
    });
}

// Start the app when DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);
