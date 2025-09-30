/**
 * Options page script for Snap! Educational Assistant
 */

// Default settings
const DEFAULT_SETTINGS = {
    serverUrl: 'ws://localhost:8080',
    autoConnect: true,
    assistanceLevel: 'intermediate',
    showNotifications: true,
    visualFeedback: true,
    theme: 'auto',
    language: 'en'
};

// DOM elements
let elements = {};

document.addEventListener('DOMContentLoaded', async () => {
    // Get DOM elements
    elements = {
        serverUrl: document.getElementById('server-url'),
        autoConnect: document.getElementById('auto-connect'),
        assistanceLevel: document.getElementById('assistance-level'),
        showNotifications: document.getElementById('show-notifications'),
        visualFeedback: document.getElementById('visual-feedback'),
        theme: document.getElementById('theme'),
        language: document.getElementById('language'),
        saveButton: document.getElementById('save-settings'),
        resetButton: document.getElementById('reset-settings'),
        statusMessage: document.getElementById('status-message')
    };

    // Load current settings
    await loadSettings();

    // Add event listeners
    elements.saveButton.addEventListener('click', saveSettings);
    elements.resetButton.addEventListener('click', resetSettings);

    // Auto-save on certain changes
    elements.serverUrl.addEventListener('blur', saveSettings);
    elements.autoConnect.addEventListener('change', saveSettings);
    elements.assistanceLevel.addEventListener('change', saveSettings);
    elements.showNotifications.addEventListener('change', saveSettings);
    elements.visualFeedback.addEventListener('change', saveSettings);
    elements.theme.addEventListener('change', saveSettings);
    elements.language.addEventListener('change', saveSettings);
});

/**
 * Load settings from storage
 */
async function loadSettings() {
    try {
        const result = await chrome.storage.sync.get(DEFAULT_SETTINGS);
        
        elements.serverUrl.value = result.serverUrl;
        elements.autoConnect.checked = result.autoConnect;
        elements.assistanceLevel.value = result.assistanceLevel;
        elements.showNotifications.checked = result.showNotifications;
        elements.visualFeedback.checked = result.visualFeedback;
        elements.theme.value = result.theme;
        elements.language.value = result.language;
        
        console.log('Settings loaded:', result);
    } catch (error) {
        console.error('Error loading settings:', error);
        showStatus('Error loading settings', 'error');
    }
}

/**
 * Save settings to storage
 */
async function saveSettings() {
    try {
        const settings = {
            serverUrl: elements.serverUrl.value.trim(),
            autoConnect: elements.autoConnect.checked,
            assistanceLevel: elements.assistanceLevel.value,
            showNotifications: elements.showNotifications.checked,
            visualFeedback: elements.visualFeedback.checked,
            theme: elements.theme.value,
            language: elements.language.value
        };

        // Validate server URL
        if (settings.serverUrl && !isValidWebSocketUrl(settings.serverUrl)) {
            showStatus('Invalid WebSocket URL format', 'error');
            return;
        }

        await chrome.storage.sync.set(settings);
        
        console.log('Settings saved:', settings);
        showStatus('Settings saved successfully!', 'success');
        
        // Notify background script of settings change
        chrome.runtime.sendMessage({
            type: 'SETTINGS_UPDATED',
            settings: settings
        });
        
    } catch (error) {
        console.error('Error saving settings:', error);
        showStatus('Error saving settings', 'error');
    }
}

/**
 * Reset settings to defaults
 */
async function resetSettings() {
    if (confirm('Are you sure you want to reset all settings to their default values?')) {
        try {
            await chrome.storage.sync.set(DEFAULT_SETTINGS);
            await loadSettings();
            showStatus('Settings reset to defaults', 'success');
            
            // Notify background script of settings change
            chrome.runtime.sendMessage({
                type: 'SETTINGS_UPDATED',
                settings: DEFAULT_SETTINGS
            });
            
        } catch (error) {
            console.error('Error resetting settings:', error);
            showStatus('Error resetting settings', 'error');
        }
    }
}

/**
 * Show status message
 */
function showStatus(message, type) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = `status ${type}`;
    elements.statusMessage.style.display = 'block';
    
    // Hide after 3 seconds
    setTimeout(() => {
        elements.statusMessage.style.display = 'none';
    }, 3000);
}

/**
 * Validate WebSocket URL format
 */
function isValidWebSocketUrl(url) {
    try {
        const parsed = new URL(url);
        return parsed.protocol === 'ws:' || parsed.protocol === 'wss:';
    } catch {
        return false;
    }
}
