// snap_bridge/visual_feedback.js - Visual Feedback and Animations

/**
 * VisualFeedback
 * 
 * Provides visual feedback, animations, and educational hints
 * when blocks are created or manipulated.
 */

class VisualFeedback {
    constructor() {
        this.activeAnimations = new Map();
        this.animationId = 0;
    }

    /**
     * Highlight blocks with visual feedback
     */
    async highlightBlocks(payload) {
        try {
            const { block_ids, highlight_style, show_tooltip } = payload;
            const results = [];

            for (const blockId of block_ids) {
                const block = this.findBlockById(blockId);
                if (block) {
                    await this.highlightSingleBlock(block, highlight_style);
                    results.push({ block_id: blockId, highlighted: true });
                } else {
                    results.push({ block_id: blockId, highlighted: false, error: 'Block not found' });
                }
            }

            // Show tooltip if requested
            if (show_tooltip && show_tooltip.text) {
                this.showTooltip(show_tooltip.text, show_tooltip.position);
            }

            return {
                status: 'success',
                highlighted_blocks: results
            };

        } catch (error) {
            console.error('Highlight error:', error);
            throw error;
        }
    }

    /**
     * Highlight a single block
     */
    async highlightSingleBlock(block, style) {
        const animationId = ++this.animationId;
        
        try {
            // Store original appearance
            const originalColor = block.color;
            const originalBorder = block.border;
            
            // Apply highlight style
            const highlightColor = new Color(style.color || '#FFD700');
            const duration = style.duration_ms || 2000;
            const pulse = style.pulse || false;
            
            if (pulse) {
                // Pulsing animation
                await this.pulseBlock(block, highlightColor, duration, animationId);
            } else {
                // Simple highlight
                block.color = highlightColor;
                block.rerender();
                
                // Restore after duration
                setTimeout(() => {
                    if (this.activeAnimations.has(animationId)) {
                        block.color = originalColor;
                        block.border = originalBorder;
                        block.rerender();
                        this.activeAnimations.delete(animationId);
                    }
                }, duration);
            }
            
            this.activeAnimations.set(animationId, {
                block: block,
                originalColor: originalColor,
                originalBorder: originalBorder
            });

        } catch (error) {
            console.error('Block highlight error:', error);
        }
    }

    /**
     * Create pulsing animation for block
     */
    async pulseBlock(block, highlightColor, duration, animationId) {
        const originalColor = block.color;
        const pulseInterval = 500; // Pulse every 500ms
        const endTime = Date.now() + duration;
        
        const pulse = () => {
            if (!this.activeAnimations.has(animationId) || Date.now() > endTime) {
                // Restore original color
                block.color = originalColor;
                block.rerender();
                this.activeAnimations.delete(animationId);
                return;
            }
            
            // Toggle between highlight and original color
            const isHighlighted = block.color.eq && block.color.eq(highlightColor);
            block.color = isHighlighted ? originalColor : highlightColor;
            block.rerender();
            
            setTimeout(pulse, pulseInterval);
        };
        
        pulse();
    }

    /**
     * Show tooltip with educational information
     */
    showTooltip(text, position = 'center') {
        const tooltip = document.createElement('div');
        tooltip.className = 'snap-educational-tooltip';
        tooltip.style.cssText = `
            position: fixed;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            max-width: 300px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            animation: fadeIn 0.3s ease-in;
        `;
        
        // Add fade-in animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }
        `;
        document.head.appendChild(style);
        
        tooltip.textContent = text;
        document.body.appendChild(tooltip);
        
        // Position tooltip
        this.positionTooltip(tooltip, position);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (tooltip.parentNode) {
                tooltip.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => {
                    if (tooltip.parentNode) {
                        tooltip.parentNode.removeChild(tooltip);
                    }
                }, 300);
            }
        }, 5000);
        
        // Add fade-out animation
        style.textContent += `
            @keyframes fadeOut {
                from { opacity: 1; transform: translateY(0); }
                to { opacity: 0; transform: translateY(-10px); }
            }
        `;
    }

    /**
     * Position tooltip on screen
     */
    positionTooltip(tooltip, position) {
        const rect = tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        switch (position) {
            case 'top':
                tooltip.style.top = '20px';
                tooltip.style.left = `${(viewportWidth - rect.width) / 2}px`;
                break;
            case 'bottom':
                tooltip.style.bottom = '20px';
                tooltip.style.left = `${(viewportWidth - rect.width) / 2}px`;
                break;
            case 'left':
                tooltip.style.left = '20px';
                tooltip.style.top = `${(viewportHeight - rect.height) / 2}px`;
                break;
            case 'right':
                tooltip.style.right = '20px';
                tooltip.style.top = `${(viewportHeight - rect.height) / 2}px`;
                break;
            case 'center':
            default:
                tooltip.style.left = `${(viewportWidth - rect.width) / 2}px`;
                tooltip.style.top = `${(viewportHeight - rect.height) / 2}px`;
                break;
        }
    }

    /**
     * Animate block creation sequence
     */
    async animateBlockCreation(blocks, options = {}) {
        const delay = options.delay || 200;
        const showConnections = options.show_connections !== false;
        
        for (let i = 0; i < blocks.length; i++) {
            const block = blocks[i];
            
            // Animate block appearance
            await this.animateBlockAppearance(block);
            
            // Show connection animation if not the last block
            if (showConnections && i < blocks.length - 1) {
                await this.animateConnection(block, blocks[i + 1]);
            }
            
            // Wait before next block
            if (i < blocks.length - 1) {
                await this.wait(delay);
            }
        }
    }

    /**
     * Animate single block appearance
     */
    async animateBlockAppearance(block) {
        if (!block || !block.rerender) return;
        
        try {
            // Start with block invisible/small
            const originalAlpha = block.alpha || 1;
            const originalScale = block.scale || 1;
            
            block.alpha = 0;
            block.scale = 0.1;
            block.rerender();
            
            // Animate to full size/opacity
            const duration = 300;
            const steps = 20;
            const stepDelay = duration / steps;
            
            for (let i = 0; i <= steps; i++) {
                const progress = i / steps;
                const easeOut = 1 - Math.pow(1 - progress, 3); // Ease-out cubic
                
                block.alpha = originalAlpha * easeOut;
                block.scale = originalScale * (0.1 + 0.9 * easeOut);
                block.rerender();
                
                if (i < steps) {
                    await this.wait(stepDelay);
                }
            }
            
        } catch (error) {
            console.error('Block appearance animation error:', error);
        }
    }

    /**
     * Animate connection between blocks
     */
    async animateConnection(fromBlock, toBlock) {
        if (!fromBlock || !toBlock) return;
        
        try {
            // Create temporary connection line
            const line = this.createConnectionLine(fromBlock, toBlock);
            document.body.appendChild(line);
            
            // Animate line appearance
            line.style.animation = 'drawLine 0.5s ease-out';
            
            // Remove line after animation
            setTimeout(() => {
                if (line.parentNode) {
                    line.parentNode.removeChild(line);
                }
            }, 500);
            
        } catch (error) {
            console.error('Connection animation error:', error);
        }
    }

    /**
     * Create visual connection line between blocks
     */
    createConnectionLine(fromBlock, toBlock) {
        const line = document.createElement('div');
        
        // Get block positions
        const fromPos = fromBlock.position();
        const toPos = toBlock.position();
        
        // Calculate line properties
        const dx = toPos.x - fromPos.x;
        const dy = toPos.y - fromPos.y;
        const length = Math.sqrt(dx * dx + dy * dy);
        const angle = Math.atan2(dy, dx) * 180 / Math.PI;
        
        line.style.cssText = `
            position: fixed;
            left: ${fromPos.x}px;
            top: ${fromPos.y}px;
            width: ${length}px;
            height: 2px;
            background: #FFD700;
            transform-origin: 0 50%;
            transform: rotate(${angle}deg);
            z-index: 9999;
            opacity: 0.8;
        `;
        
        // Add animation styles
        const style = document.createElement('style');
        style.textContent = `
            @keyframes drawLine {
                from { width: 0; }
                to { width: ${length}px; }
            }
        `;
        document.head.appendChild(style);
        
        return line;
    }

    /**
     * Show educational explanation
     */
    showExplanation(text, options = {}) {
        const explanation = document.createElement('div');
        explanation.className = 'snap-explanation';
        explanation.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            font-family: Arial, sans-serif;
            font-size: 16px;
            line-height: 1.5;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            animation: slideUp 0.5s ease-out;
            max-width: 600px;
            margin: 0 auto;
        `;
        
        explanation.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 24px; margin-right: 10px;">🎓</span>
                <strong>What just happened?</strong>
            </div>
            <div>${text}</div>
            <button onclick="this.parentNode.remove()" style="
                position: absolute;
                top: 10px;
                right: 10px;
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
                opacity: 0.7;
            ">×</button>
        `;
        
        // Add slide-up animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideUp {
                from { transform: translateY(100%); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(explanation);
        
        // Auto-remove after duration
        const duration = options.duration || 8000;
        setTimeout(() => {
            if (explanation.parentNode) {
                explanation.style.animation = 'slideDown 0.5s ease-in';
                setTimeout(() => {
                    if (explanation.parentNode) {
                        explanation.parentNode.removeChild(explanation);
                    }
                }, 500);
            }
        }, duration);
        
        // Add slide-down animation
        style.textContent += `
            @keyframes slideDown {
                from { transform: translateY(0); opacity: 1; }
                to { transform: translateY(100%); opacity: 0; }
            }
        `;
    }

    /**
     * Find block by ID
     */
    findBlockById(blockId) {
        const ide = world.children[0];
        const sprites = [ide.stage, ...ide.sprites.asArray()];
        
        for (const sprite of sprites) {
            const found = this.searchBlockInSprite(sprite, blockId);
            if (found) return found;
        }
        
        return null;
    }

    /**
     * Search for block in sprite
     */
    searchBlockInSprite(sprite, blockId) {
        const scripts = sprite.scripts.children;
        
        for (const script of scripts) {
            const found = this.searchBlockInScript(script, blockId);
            if (found) return found;
        }
        
        return null;
    }

    /**
     * Search for block in script recursively
     */
    searchBlockInScript(block, blockId) {
        if (block.blockId === blockId) {
            return block;
        }
        
        // Search in nested blocks
        if (block.inputs) {
            const inputs = block.inputs();
            for (const input of inputs) {
                if (input instanceof BlockMorph) {
                    const found = this.searchBlockInScript(input, blockId);
                    if (found) return found;
                }
            }
        }
        
        // Search in next block
        if (block.nextBlock && block.nextBlock()) {
            return this.searchBlockInScript(block.nextBlock(), blockId);
        }
        
        return null;
    }

    /**
     * Utility: Wait for specified milliseconds
     */
    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Clear all active animations
     */
    clearAllAnimations() {
        this.activeAnimations.forEach((animation, id) => {
            const { block, originalColor, originalBorder } = animation;
            block.color = originalColor;
            block.border = originalBorder;
            block.rerender();
        });
        this.activeAnimations.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VisualFeedback;
}
