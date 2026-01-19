// Generation Page Logic

let t2iState = {
    selectedModel: null,
    parameters: {},
    price: null
};

let i2iState = {
    selectedModel: null,
    parameters: {},
    price: null,
    selectedFiles: []
};

function initGenerationPage() {
    // Setup tab switching
    setupGenerationTabs();
    
    // Load models into both tabs
    loadModelsIntoSelect('t2i-model');
    loadModelsIntoSelect('i2i-model');
    
    // Setup text-to-image
    setupT2I();
    
    // Setup image-to-image
    setupI2I();
}

function setupGenerationTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            
            // Update buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`tab-${tabName}`).classList.add('active');
        });
    });
}

function loadModelsIntoSelect(selectId) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">Select a model...</option>';
    
    appState.models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = ` ${model.name}`;
        select.appendChild(option);
    });
}

// ============ TEXT TO IMAGE ============
function setupT2I() {
    const promptTextarea = document.getElementById('t2i-prompt');
    const modelSelect = document.getElementById('t2i-model');
    const generateBtn = document.getElementById('t2i-generate-btn');
    
    // Model selection
    modelSelect.addEventListener('change', () => {
        const modelId = parseInt(modelSelect.value);
        t2iState.selectedModel = appState.models.find(m => m.id === modelId);
        renderT2IParameters();
        updateT2IPrice();
    });
    
    // Enable button when prompt and model are selected
    promptTextarea.addEventListener('input', () => {
        generateBtn.disabled = !promptTextarea.value.trim() || !t2iState.selectedModel;
    });
    
    generateBtn.addEventListener('click', handleT2IGeneration);
}

function renderT2IParameters() {
    const container = document.getElementById('t2i-parameters');
    container.innerHTML = '';
    
    if (!t2iState.selectedModel || !t2iState.selectedModel.options) return;
    
    const options = t2iState.selectedModel.options;
    
    // Size parameter
    if (options.sizes && options.sizes.length > 0) {
        container.appendChild(createParameterSelect('size', 'Size', options.sizes));
    }
    
    // Aspect ratio
    if (options.aspect_ratios && options.aspect_ratios.length > 0) {
        container.appendChild(createParameterSelect('aspect_ratio', 'Aspect Ratio', options.aspect_ratios));
    }
    
    // Resolution
    if (options.resolutions && options.resolutions.length > 0) {
        container.appendChild(createParameterSelect('resolution', 'Resolution', options.resolutions));
    }
    
    // Quality
    if (options.qualities && options.qualities.length > 0) {
        container.appendChild(createParameterSelect('quality', 'Quality', options.qualities));
    }
}

function createParameterSelect(paramName, label, options) {
    const formGroup = document.createElement('div');
    formGroup.className = 'form-group';
    
    const labelEl = document.createElement('label');
    labelEl.textContent = label;
    labelEl.htmlFor = `t2i-${paramName}`;
    
    const select = document.createElement('select');
    select.className = 'select';
    select.id = `t2i-${paramName}`;
    
    // Default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Default';
    select.appendChild(defaultOption);
    
    // Add options
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt;
        option.textContent = opt;
        select.appendChild(option);
    });
    
    select.addEventListener('change', () => {
        t2iState.parameters[paramName] = select.value || null;
        updateT2IPrice();
    });
    
    formGroup.appendChild(labelEl);
    formGroup.appendChild(select);
    return formGroup;
}

async function updateT2IPrice() {
    if (!t2iState.selectedModel) return;
    
    try {
        const priceData = await api.getGenerationPrice(
            getTelegramId(),
            t2iState.selectedModel.id,
            {
                ...t2iState.parameters,
                is_image_to_image: false
            }
        );
        
        t2iState.price = priceData.price_credits;
        document.getElementById('t2i-price').textContent = `${t2iState.price} cr`;
        
        // Update button text
        document.getElementById('t2i-generate-btn').innerHTML = `🚀 Generate Image (${t2iState.price} cr)`;
    } catch (error) {
        console.error('Failed to get price:', error);
        document.getElementById('t2i-price').textContent = '- cr';
    }
}

async function handleT2IGeneration() {
    const prompt =document.getElementById('t2i-prompt').value.trim();
    const statusDiv = document.getElementById('t2i-status');
    const resultsDiv = document.getElementById('t2i-results');
    const generateBtn = document.getElementById('t2i-generate-btn');
    
    if (!prompt || !t2iState.selectedModel) return;
    
    try {
        generateBtn.disabled = true;
        statusDiv.style.display = 'block';
        statusDiv.innerHTML = '<p>⏳ Submitting generation...</p>';
        resultsDiv.style.display = 'none';
        
        const response = await api.submitGeneration(
            getTelegramId(),
            t2iState.selectedModel.id,
            prompt,
            t2iState.parameters
        );
        
        statusDiv.innerHTML = '<p>⏳ Generating image...</p>';
        
        // Poll for results
        const results = await pollGenerationWithStatus(response.request_id, getTelegramId(), statusDiv);
        
        // Display results
        displayResults(results, resultsDiv);
        statusDiv.style.display = 'none';
        
        // Reload balance
        await loadUserBalance();
        showToast('Image generated successfully!', 'success');
    } catch (error) {
        console.error('Generation failed:', error);
        statusDiv.innerHTML = `<p style="color: var(--color-error);">❌ ${error.message}</p>`;
        showToast(error.message || 'Generation failed', 'error');
    } finally {
        generateBtn.disabled = false;
    }
}

// ============ IMAGE TO IMAGE ============
function setupI2I() {
    const uploadArea = document.getElementById('i2i-upload-area');
    const fileInput = document.getElementById('i2i-file-input');
    const previewDiv = document.getElementById('i2i-preview');
    const promptTextarea = document.getElementById('i2i-prompt');
    const modelSelect = document.getElementById('i2i-model');
    const generateBtn = document.getElementById('i2i-generate-btn');
    
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 10) {
            showToast('Maximum 10 images allowed', 'error');
            return;
        }
        
        i2iState.selectedFiles = files.filter(validateImageFile);
        displayI2IPreview();
        checkI2IEnabled();
    });
    
    modelSelect.addEventListener('change', () => {
        const modelId = parseInt(modelSelect.value);
        i2iState.selectedModel = appState.models.find(m => m.id === modelId);
        checkI2IEnabled();
    });
    
    promptTextarea.addEventListener('input', checkI2IEnabled);
    generateBtn.addEventListener('click', handleI2IGeneration);
}

function displayI2IPreview() {
    const previewDiv = document.getElementById('i2i-preview');
    previewDiv.innerHTML = '';
    
    i2iState.selectedFiles.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const item = document.createElement('div');
            item.className = 'preview-item';
            item.innerHTML = `
                <img src="${e.target.result}" alt="Preview ${index + 1}">
                <button class="preview-remove" data-index="${index}">×</button>
            `;
            
            item.querySelector('.preview-remove').addEventListener('click', () => {
                i2iState.selectedFiles.splice(index, 1);
                displayI2IPreview();
                checkI2IEnabled();
            });
            
            previewDiv.appendChild(item);
        };
        reader.readAsDataURL(file);
    });
}

function checkI2IEnabled() {
    const prompt = document.getElementById('i2i-prompt').value.trim();
    const hasFiles = i2iState.selectedFiles.length > 0;
    const hasModel = i2iState.selectedModel !== null;
    
    document.getElementById('i2i-generate-btn').disabled = !prompt || !hasFiles || !hasModel;
}

async function handleI2IGeneration() {
    const prompt = document.getElementById('i2i-prompt').value.trim();
    const statusDiv = document.getElementById('i2i-status');
    const resultsDiv = document.getElementById('i2i-results');
    const generateBtn = document.getElementById('i2i-generate-btn');
    
    try {
        generateBtn.disabled = true;
        statusDiv.style.display = 'block';
        statusDiv.innerHTML = '<p>⏳ Uploading images...</p>';
        resultsDiv.style.display = 'none';
        
        // Upload all images
        const uploadPromises = i2iState.selectedFiles.map(file => api.uploadMedia(file, file.name));
        const uploadedUrls = await Promise.all(uploadPromises);
        
        statusDiv.innerHTML = '<p>⏳ Submitting generation...</p>';
        
        const response = await api.submitGeneration(
            getTelegramId(),
            i2iState.selectedModel.id,
            prompt,
            { ...i2iState.parameters, is_image_to_image: true },
            uploadedUrls
        );
        
        statusDiv.innerHTML = '<p>⏳ Generating image...</p>';
        
        // Poll for results
        const results = await pollGenerationWithStatus(response.request_id, getTelegramId(), statusDiv);
        
        // Display results
        displayResults(results, resultsDiv);
        statusDiv.style.display = 'none';
        
        // Reload balance
        await loadUserBalance();
        showToast('Image generated successfully!', 'success');
    } catch (error) {
        console.error('Generation failed:', error);
        statusDiv.innerHTML = `<p style="color: var(--color-error);">❌ ${error.message}</p>`;
        showToast(error.message || 'Generation failed', 'error');
    } finally {
        generateBtn.disabled = false;
    }
}

// ============ HELPERS ============
async function pollGenerationWithStatus(requestId, telegramId, statusDiv) {
    const maxAttempts = 60;
    
    for (let i = 0; i < maxAttempts; i++) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const status = await api.getGenerationStatus(requestId, telegramId);
        
        // Update status display
        if (status.status === 'processing') {
            statusDiv.innerHTML = '<p>🎨 Processing...</p>';
        } else if (status.status === 'queue') {
            statusDiv.innerHTML = '<p>⏳ In queue...</p>';
        }
        
        if (status.status === 'completed') {
            return await api.getGenerationResults(requestId, telegramId);
        } else if (status.status === 'failed') {
            throw new Error(status.error || 'Generation failed');
        }
    }
    
    throw new Error('Generation timeout');
}

function displayResults(results, container) {
    container.innerHTML = '';
    container.style.display = 'grid';
    
    results.forEach(url => {
        const item = document.createElement('div');
        item.className = 'result-item';
        item.innerHTML = `<img src="${url}" alt="Generated image">`;
        container.appendChild(item);
    });
}
