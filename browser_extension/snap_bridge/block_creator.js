// snap_bridge/block_creator.js - Snap! Block Creation and Manipulation

// Prevent duplicate loading
if (typeof window.SnapBlockCreator !== 'undefined') {
    console.log('⚠️ SnapBlockCreator already loaded, skipping...');
} else {

/**
 * SnapBlockCreator
 *
 * Handles the creation, manipulation, and deletion of Snap! blocks
 * using the Snap! internal APIs.
 */

class SnapBlockCreator {
    constructor(apiWrapper) {
        if (!apiWrapper) {
            throw new Error("SnapBlockCreator requires an instance of SnapAPIWrapper.");
        }
        this.apiWrapper = apiWrapper;
        this.ide = null;
        this.stage = null;
        this.currentSprite = null;
        this.blockCount = 0;
    }

    /**
     * Get the current IDE instance
     */
    getIDE() {
        return this.apiWrapper.getIDE();
    }

    /**
     * Get the current stage
     */
    getStage() {
        return this.apiWrapper.getStage();
    }


    // REMOVED isSnapReady method; use apiWrapper.isReady instead

    /**
     * Get or set current sprite
     */
    getCurrentSprite(spriteName = null) {
        const ide = this.apiWrapper.getIDE();

        if (spriteName) {
            // Find sprite by name
            const sprite = ide.sprites.detect(s => s.name === spriteName);
            if (sprite) {
                ide.selectSprite(sprite);
                this.currentSprite = sprite;
            } else {
                throw new Error(`Sprite '${spriteName}' not found`);
            }
        } else {
            this.currentSprite = ide.currentSprite;
        }

        return this.currentSprite;
    }

    /**
     * Create blocks from specification
     */
    async createBlocks(payload) {
        // Check if Snap! environment is ready using the unified check
        if (!this.apiWrapper.isReady()) {
            throw new Error('Snap! environment is not ready. Please wait for Snap! to fully load and try again.');
        }

        try {
            const { target_sprite, scripts, visual_feedback } = payload;
            // ...existing code...
            // (rest of method unchanged)
            const sprite = this.getCurrentSprite(target_sprite);
            const scriptsArea = sprite.scripts;
            let totalBlocksCreated = 0;
            let scriptsCreated = 0;
            const createdBlockIds = [];
            for (const scriptSpec of scripts) {
                const { script_id, position, blocks } = scriptSpec;
                if (!blocks || blocks.length === 0) {
                    continue;
                }
                const scriptBlocks = await this.createScript(blocks, position);
                totalBlocksCreated += scriptBlocks.length;
                scriptsCreated++;
                scriptBlocks.forEach(block => {
                    if (block.blockId) {
                        createdBlockIds.push(block.blockId);
                    }
                });
                if (visual_feedback && visual_feedback.animate_creation) {
                    await this.animateBlockCreation(scriptBlocks, visual_feedback);
                }
            }
            this.getIDE().flushBlocksCache();
            this.getIDE().refreshPalette();
            return {
                status: 'success',
                blocks_created: totalBlocksCreated,
                scripts_created: scriptsCreated,
                execution_time_ms: Date.now() - performance.now(),
                created_block_ids: createdBlockIds,
                sprite_info: {
                    name: sprite.name,
                    position: { x: sprite.xPosition(), y: sprite.yPosition() },
                    total_scripts: sprite.scripts.children.length
                }
            };
        } catch (error) {
            console.error('Block creation error:', error);
            throw error;
        }
    }

    /**
     * Create a script from block specifications
     */
    async createScript(blockSpecs, position = { x: 50, y: 50 }) {
        const sprite = this.getCurrentSprite();
        const createdBlocks = [];
        let previousBlock = null;
        
        for (let i = 0; i < blockSpecs.length; i++) {
            const blockSpec = blockSpecs[i];
            const block = await this.createSingleBlock(blockSpec, sprite);
            
            if (block) {
                createdBlocks.push(block);
                
                // Connect to previous block if not a hat block
                if (previousBlock && !blockSpec.is_hat_block) {
                    this.connectBlocks(previousBlock, block);
                }
                
                previousBlock = block;
            }
        }
        
        // Position the first block (hat block or first block)
        if (createdBlocks.length > 0) {
            const firstBlock = createdBlocks[0];
            firstBlock.setPosition(new Point(position.x, position.y));
            sprite.scripts.add(firstBlock);
        }
        
        return createdBlocks;
    }

    /**
     * Create a single block from specification
     */
    async createSingleBlock(blockSpec, sprite) {
        try {
            const { opcode, category, inputs, is_hat_block, block_id } = blockSpec;
            
            // Create the block using Snap!'s block creation system
            let block;
            
            if (is_hat_block) {
                // Create hat block (event block)
                block = sprite.blockForSelector(opcode);
            } else {
                // Create regular block
                block = sprite.blockForSelector(opcode);
            }
            
            if (!block) {
                console.warn(`Could not create block for opcode: ${opcode}`);
                return null;
            }
            
            // Set inputs
            if (inputs && Object.keys(inputs).length > 0) {
                this.setBlockInputs(block, inputs);
            }
            
            // Store block ID for reference
            if (block_id) {
                block.blockId = block_id;
            }
            
            return block;
            
        } catch (error) {
            console.error(`Error creating block ${blockSpec.opcode}:`, error);
            return null;
        }
    }

    /**
     * Set inputs for a block
     */
    setBlockInputs(block, inputs) {
        try {
            const inputSlots = block.inputs();
            
            Object.entries(inputs).forEach(([inputName, inputValue], index) => {
                if (inputSlots[index]) {
                    if (typeof inputValue === 'string') {
                        inputSlots[index].setContents(inputValue);
                    } else if (typeof inputValue === 'number') {
                        inputSlots[index].setContents(inputValue);
                    } else {
                        // Handle complex inputs (blocks, etc.)
                        inputSlots[index].setContents(inputValue);
                    }
                }
            });
            
        } catch (error) {
            console.error('Error setting block inputs:', error);
        }
    }

    /**
     * Connect two blocks
     */
    connectBlocks(topBlock, bottomBlock) {
        try {
            if (topBlock && bottomBlock) {
                topBlock.nextBlock(bottomBlock);
            }
        } catch (error) {
            console.error('Error connecting blocks:', error);
        }
    }

    /**
     * Delete blocks by specification
     */
    async deleteBlocks(payload) {
        try {
            const { target_sprite, selection } = payload;
            const sprite = this.getCurrentSprite(target_sprite);
            
            let deletedCount = 0;
            
            if (selection.type === 'by_id') {
                // Delete specific blocks by ID
                selection.block_ids.forEach(blockId => {
                    const block = this.findBlockById(sprite, blockId);
                    if (block) {
                        block.destroy();
                        deletedCount++;
                    }
                });
            } else if (selection.type === 'all_scripts') {
                // Delete all scripts
                sprite.scripts.children.slice().forEach(script => {
                    script.destroy();
                    deletedCount++;
                });
            }
            
            return {
                status: 'success',
                blocks_deleted: deletedCount
            };
            
        } catch (error) {
            console.error('Block deletion error:', error);
            throw error;
        }
    }

    /**
     * Create custom block
     */
    async createCustomBlock(payload) {
        try {
            const { block_name, parameters, definition, category, scope } = payload;
            const sprite = this.getCurrentSprite();
            
            // Create custom block definition
            const customBlock = new CustomBlockDefinition(
                block_name,
                sprite,
                scope === 'global'
            );
            
            // Set parameters
            if (parameters && parameters.length > 0) {
                parameters.forEach(param => {
                    customBlock.addParameter(param.name, param.type);
                });
            }
            
            // Set definition (body)
            if (definition && definition.length > 0) {
                const bodyBlocks = await this.createScript(definition);
                customBlock.body = new Context(null, bodyBlocks[0]);
            }
            
            // Set category
            customBlock.category = category || 'custom';
            
            // Add to sprite
            sprite.customBlocks.push(customBlock);
            
            // Refresh palette
            this.getIDE().flushBlocksCache();
            this.getIDE().refreshPalette();
            
            return {
                status: 'success',
                block_name: block_name,
                message: `Custom block '${block_name}' created successfully`
            };
            
        } catch (error) {
            console.error('Custom block creation error:', error);
            throw error;
        }
    }

    /**
     * Find block by ID
     */
    findBlockById(sprite, blockId) {
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
     * Animate block creation
     */
    async animateBlockCreation(blocks, visualFeedback) {
        if (!visualFeedback.animate_creation) return;
        
        for (const block of blocks) {
            // Simple animation: highlight the block
            if (block && block.flash) {
                block.flash();
            }
            
            // Wait a bit between animations
            await new Promise(resolve => setTimeout(resolve, 200));
        }
        
        // Show explanation if requested
        if (visualFeedback.show_explanation && visualFeedback.explanation_text) {
            this.showExplanation(visualFeedback.explanation_text);
        }
    }

    /**
     * Show explanation bubble
     */
    showExplanation(text) {
        const ide = this.getIDE();
        if (ide && ide.inform) {
            ide.inform('Snap! Educational Assistant', text);
        }
    }
}

// Store reference to prevent duplicate loading
window.SnapBlockCreator = SnapBlockCreator;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SnapBlockCreator;
}

} // End of duplicate loading protection
