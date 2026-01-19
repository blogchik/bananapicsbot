// Profile Page Logic

function initProfilePage() {
    // Setup copy referral link button
    const copyBtn = document.getElementById('copy-referral-btn');
    copyBtn.addEventListener('click', () => {
        const linkInput = document.getElementById('referral-link');
        copyToClipboard(linkInput.value);
    });

    // Setup top-up button
    const topupBtn = document.getElementById('topup-btn');
    topupBtn.addEventListener('click', () => {
        // Close WebApp and go to bot
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.close();
        }
        showToast('Please use /topup command in thebot', 'info');
    });
}

async function loadProfileData() {
    try {
        const telegramId = getTelegramId();
        const user = getUserData();

        // Update profile info
        document.getElementById('profile-name').textContent = user.first_name || 'User';
        document.getElementById('profile-username').textContent = user.username ? `@${user.username}` : 'No username';
        document.getElementById('profile-id').textContent = telegramId;

        // Get balance
        const balanceData = await api.getUserBalance(telegramId);
        const balance = balanceData.balance || 0;
        appState.balance = balance;
        
        document.getElementById('profile-balance').textContent = `${formatNumber(balance)} credits`;
        document.getElementById('profile-generations').textContent = `~${estimateGenerations(balance)}`;

        // Get referral info
        const referralData = await api.getReferralInfo(telegramId);
        const botUsername = 'BananaPicsBot'; // This should come from config
        const referralLink = `https://t.me/${botUsername}?start=r_${referralData.referral_code || telegramId}`;
        
        document.getElementById('referral-link').value = referralLink;
        document.getElementById('referral-count').textContent = referralData.referral_count || 0;
        document.getElementById('referral-bonus').textContent = `${referralData.total_bonus || 0} credits`;

        updateBalanceDisplay();
    } catch (error) {
        console.error('Failed to load profile data:', error);
        showToast('Failed to load profile', 'error');
    }
}
