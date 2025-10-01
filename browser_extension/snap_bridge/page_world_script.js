// Use a global flag to ensure this logic only runs once.
if (!window.snapIsReadyChecker) {
    window.snapIsReadyChecker = true;

    let attempts = 0;
    const maxAttempts = 200; // 20 seconds max wait

    const checkerInterval = setInterval(() => {
        attempts++;
        // The most crucial object is IDE_Morph. If it exists, Snap's JS is loaded.
        if (window.IDE_Morph) {
            console.log('PAGE_WORLD_SCRIPT: Snap environment ready! Firing event.');
            clearInterval(checkerInterval);
            window.dispatchEvent(new CustomEvent('SnapIsReadyEvent'));
        } else if (attempts > maxAttempts) {
            console.error('PAGE_WORLD_SCRIPT: Timed out waiting for Snap environment.');
            clearInterval(checkerInterval);
        }
    }, 100);
}