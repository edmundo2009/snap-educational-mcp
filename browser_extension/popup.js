/**
 * Popup script for Snap! Educational Assistant
 */

document.addEventListener('DOMContentLoaded', async () => {
    const statusElement = document.getElementById('status');
    const statusText = document.getElementById('status-text');
    const openSnapButton = document.getElementById('open-snap');
    const openOptionsButton = document.getElementById('open-options');
    const helpButton = document.getElementById('help');

    // Token entry elements
    const tokenSection = document.getElementById('token-section');
    const showTokenButton = document.getElementById('show-token-input');
    const tokenInput = document.getElementById('token-input');
    const connectButton = document.getElementById('connect-btn');
    const tokenError = document.getElementById('token-error');

    // Check if we're currently on a Snap! page
    async function checkSnapStatus() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            if (tab && (tab.url.includes('snap.berkeley.edu') || tab.url.includes('extensions.snap.berkeley.edu'))) {
                statusElement.className = 'status active';
                statusText.textContent = 'Connected to Snap!';
                openSnapButton.textContent = 'Refresh Page';
            } else {
                statusElement.className = 'status inactive';
                statusText.textContent = 'Not connected to Snap!';
                openSnapButton.textContent = 'Open Snap!';
            }
        } catch (error) {
            console.error('Error checking Snap status:', error);
            statusElement.className = 'status inactive';
            statusText.textContent = 'Status unknown';
        }
    }

    // Initialize status check
    await checkSnapStatus();

    // Open Snap! button handler
    openSnapButton.addEventListener('click', async () => {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            if (tab && (tab.url.includes('snap.berkeley.edu') || tab.url.includes('extensions.snap.berkeley.edu'))) {
                // Refresh current Snap! page
                await chrome.tabs.reload(tab.id);
            } else {
                // Open new Snap! tab
                await chrome.tabs.create({
                    url: 'https://snap.berkeley.edu/snap/snap.html'
                });
            }
            
            window.close();
        } catch (error) {
            console.error('Error opening Snap!:', error);
        }
    });

    // Open options button handler
    openOptionsButton.addEventListener('click', () => {
        chrome.runtime.openOptionsPage();
        window.close();
    });

    // Help button handler
    helpButton.addEventListener('click', async () => {
        try {
            await chrome.tabs.create({
                url: 'https://snap.berkeley.edu/about'
            });
            window.close();
        } catch (error) {
            console.error('Error opening help:', error);
        }
    });

    // Show token input handler
    showTokenButton.addEventListener('click', () => {
        tokenSection.style.display = tokenSection.style.display === 'none' ? 'block' : 'none';
        if (tokenSection.style.display === 'block') {
            tokenInput.focus();
        }
    });

    // Token input formatting (uppercase, 8 chars max)
    tokenInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
        tokenError.style.display = 'none';
    });

    // Connect button handler
    connectButton.addEventListener('click', async () => {
        const token = tokenInput.value.trim();

        if (!token) {
            showTokenError('Please enter a token');
            return;
        }

        if (token.length !== 8) {
            showTokenError('Token must be exactly 8 characters');
            return;
        }

        try {
            connectButton.textContent = 'Connecting...';
            connectButton.disabled = true;

            // Send token to content script
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            console.log('🔍 Current tab:', tab);

            if (!tab || !tab.url.includes('snap.berkeley.edu')) {
                showTokenError('Please open Snap! first');
                return;
            }

            console.log('📤 Sending message to content script:', { action: 'connect_with_token', token: token });

            // Check if content script is ready (with timeout)
            try {
                const pingPromise = chrome.tabs.sendMessage(tab.id, { action: 'ping' });
                const timeoutPromise = new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('Ping timeout')), 3000)
                );

                const readyCheck = await Promise.race([pingPromise, timeoutPromise]);
                console.log('🏓 Content script ping response:', readyCheck);
            } catch (pingError) {
                console.warn('⚠️ Content script not responding to ping:', pingError);
                showTokenError('Extension not ready. Please refresh the Snap! page and try again.');
                return;
            }

            // Send message to content script to connect with token
            const response = await chrome.tabs.sendMessage(tab.id, {
                action: 'connect_with_token',
                token: token
            });

            console.log('📥 Response from content script:', response);

            if (response && response.success) {
                statusElement.className = 'status active';
                statusText.textContent = 'Connected to MCP Server!';
                tokenSection.style.display = 'none';
                tokenInput.value = '';
                showTokenButton.textContent = '✅ Connected';
                showTokenButton.disabled = true;
            } else {
                showTokenError(response?.error || 'Connection failed');
            }

        } catch (error) {
            console.error('Connection error:', error);
            showTokenError('Connection failed. Check console for details.');
        } finally {
            connectButton.textContent = 'Connect';
            connectButton.disabled = false;
        }
    });

    // Helper function to show token errors
    function showTokenError(message) {
        tokenError.textContent = message;
        tokenError.style.display = 'block';
        setTimeout(() => {
            tokenError.style.display = 'none';
        }, 5000);
    }

    // Listen for tab updates to refresh status
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
        if (changeInfo.status === 'complete') {
            checkSnapStatus();
        }
    });
});
