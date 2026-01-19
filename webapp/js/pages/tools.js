// Tools Page Logic

let wmSelectedFile = null;

function initToolsPage() {
    // Watermark remover file upload
    const wmUploadArea = document.getElementById('wm-upload-area');
    const wmFileInput = document.getElementById('wm-file-input');
    const wmPreview = document.getElementById('wm-preview');
    const wmRemoveBtn = document.getElementById('wm-remove-btn');

    wmFileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file && validateImageFile(file)) {
            wmSelectedFile = file;
            displayWmPreview(file);
            wmRemoveBtn.disabled = false;
        }
    });

    wmRemoveBtn.addEventListener('click', handleWatermarkRemoval);
}

async function displayWmPreview(file) {
    const previewContainer = document.getElementById('wm-preview');
    const dataUrl = await readFileAsDataURL(file);
    
    previewContainer.innerHTML = `<img src="${dataUrl}" alt="Preview" style="max-width: 100%; border-radius: var(--radius-md);">`;
    previewContainer.style.display = 'block';
}

async function handleWatermarkRemoval() {
    if (!wmSelectedFile) return;

    const statusDiv = document.getElementById('wm-status');
    const resultDiv = document.getElementById('wm-result');
    const removeBtn = document.getElementById('wm-remove-btn');

    try {
        removeBtn.disabled = true;
        statusDiv.style.display = 'block';
        statusDiv.innerHTML = '<p>⏳ Removing watermark...</p>';
        resultDiv.style.display = 'none';

        // Upload image
        const url = await api.uploadMedia(wmSelectedFile, wmSelectedFile.name);

        // Submit watermark removal (same as image-to-image with specific model)
        const telegramId = getTelegramId();
        
        // For watermark removal, you might have a specific model or tool
        // This is a placeholder - adjust based on your actual watermark removal endpoint
        const response = await api.submitGeneration(
            telegramId,
            1, // Watermark remover model ID - adjust as needed
            'Remove watermark from this image',
            { is_image_to_image: true },
            [url]
        );

        // Poll for results
        const resultUrl = await pollGeneration(response.request_id, telegramId);

        // Show result
        statusDiv.style.display = 'none';
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <h4>✅ Watermark Removed</h4>
            <img src="${resultUrl}" alt="Result" style="max-width: 100%; border-radius: var(--radius-md); margin-top: var(--spacing-md);">
            <p style="margin-top: var(--spacing-md); color: var(--color-text-secondary);">Cost: 12 credits</p>
        `;

        // Reload balance
        await loadUserBalance();
        showToast('Watermark removed successfully!', 'success');
    } catch (error) {
        console.error('Watermark removal failed:', error);
        statusDiv.innerHTML = '<p style="color: var(--color-error);">❌ Failed to remove watermark</p>';
        showToast(error.message || 'Watermark removal failed', 'error');
    } finally {
        removeBtn.disabled = false;
    }
}

// Helper function to poll generation status
async function pollGeneration(requestId, telegramId, maxAttempts = 60) {
    for (let i = 0; i < maxAttempts; i++) {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
        
        const status = await api.getGenerationStatus(requestId, telegramId);
        
        if (status.status === 'completed') {
            const results = await api.getGenerationResults(requestId, telegramId);
            return results[0]; // Return first result URL
        } else if (status.status === 'failed') {
            throw new Error('Generation failed');
        }
    }
    
    throw new Error('Generation timeout');
}
