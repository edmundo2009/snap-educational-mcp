/**
 * Popup script for Snap! Educational Assistant
 */

document.addEventListener('DOMContentLoaded', async () => {
    const statusElement = document.getElementById('status');
    const statusText = document.getElementById('status-text');
    const openSnapButton = document.getElementById('open-snap');
    const openOptionsButton = document.getElementById('open-options');
    const helpButton = document.getElementById('help');

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

    // Listen for tab updates to refresh status
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
        if (changeInfo.status === 'complete') {
            checkSnapStatus();
        }
    });
});
