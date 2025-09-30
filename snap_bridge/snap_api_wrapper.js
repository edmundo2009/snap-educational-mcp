// snap_bridge/snap_api_wrapper.js - Snap! API Wrapper and Utilities

/**
 * SnapAPIWrapper
 * 
 * Provides high-level wrapper functions for Snap! internal APIs
 * and utilities for reading project state and executing scripts.
 */

class SnapAPIWrapper {
    constructor() {
        this.ide = null;
        this.stage = null;
    }

    /**
     * Get the current IDE instance
     */
    getIDE() {
        if (!this.ide) {
            this.ide = world.children[0];
        }
        return this.ide;
    }

    /**
     * Get the current stage
     */
    getStage() {
        if (!this.stage) {
            this.stage = this.getIDE().stage;
        }
        return this.stage;
    }

    /**
     * Get Snap! version
     */
    getSnapVersion() {
        try {
            return this.getIDE().version || 'unknown';
        } catch (error) {
            return 'unknown';
        }
    }

    /**
     * Read current project state
     */
    async readProject(payload) {
        try {
            const { include, detail_level } = payload;
            const ide = this.getIDE();
            const stage = this.getStage();
            
            const project = {
                name: ide.projectName || 'Untitled',
                sprites: [],
                stage: {},
                global_variables: [],
                custom_blocks: []
            };

            // Include sprites information
            if (include.sprites) {
                project.sprites = this.getSpritesInfo(detail_level);
            }

            // Include stage information
            if (include.stage) {
                project.stage = this.getStageInfo(detail_level);
            }

            // Include variables
            if (include.variables) {
                project.global_variables = this.getGlobalVariables();
            }

            // Include custom blocks
            if (include.custom_blocks) {
                project.custom_blocks = this.getCustomBlocks();
            }

            return project;

        } catch (error) {
            console.error('Error reading project:', error);
            throw error;
        }
    }

    /**
     * Get sprites information
     */
    getSpritesInfo(detailLevel = 'summary') {
        const ide = this.getIDE();
        const sprites = [];

        ide.sprites.asArray().forEach(sprite => {
            const spriteInfo = {
                name: sprite.name,
                costume_count: sprite.costumes.length(),
                script_count: sprite.scripts.children.length,
                position: {
                    x: sprite.xPosition(),
                    y: sprite.yPosition()
                },
                size: sprite.size,
                visible: sprite.isVisible,
                direction: sprite.heading
            };

            if (detailLevel === 'detailed' || detailLevel === 'full') {
                spriteInfo.costumes = sprite.costumes.asArray().map(costume => ({
                    name: costume.name,
                    width: costume.width(),
                    height: costume.height()
                }));

                spriteInfo.sounds = sprite.sounds.asArray().map(sound => ({
                    name: sound.name,
                    duration: sound.duration || 0
                }));
            }

            if (detailLevel === 'full') {
                spriteInfo.scripts = this.getScriptsInfo(sprite);
                spriteInfo.variables = this.getSpriteVariables(sprite);
            }

            sprites.push(spriteInfo);
        });

        return sprites;
    }

    /**
     * Get stage information
     */
    getStageInfo(detailLevel = 'summary') {
        const stage = this.getStage();
        
        const stageInfo = {
            costume_count: stage.costumes.length(),
            script_count: stage.scripts.children.length,
            current_costume: stage.costume.name
        };

        if (detailLevel === 'detailed' || detailLevel === 'full') {
            stageInfo.costumes = stage.costumes.asArray().map(costume => ({
                name: costume.name,
                width: costume.width(),
                height: costume.height()
            }));
        }

        if (detailLevel === 'full') {
            stageInfo.scripts = this.getScriptsInfo(stage);
        }

        return stageInfo;
    }

    /**
     * Get scripts information for a sprite or stage
     */
    getScriptsInfo(target) {
        const scripts = [];
        
        target.scripts.children.forEach((script, index) => {
            const scriptInfo = {
                id: `script_${index}`,
                position: {
                    x: script.position().x,
                    y: script.position().y
                },
                blocks: this.getBlocksInfo(script)
            };
            scripts.push(scriptInfo);
        });

        return scripts;
    }

    /**
     * Get blocks information from a script
     */
    getBlocksInfo(block, depth = 0) {
        if (!block || depth > 10) return []; // Prevent infinite recursion

        const blocks = [];
        let currentBlock = block;

        while (currentBlock) {
            const blockInfo = {
                opcode: currentBlock.selector || 'unknown',
                category: this.getBlockCategory(currentBlock),
                inputs: this.getBlockInputs(currentBlock),
                position: {
                    x: currentBlock.position().x,
                    y: currentBlock.position().y
                }
            };

            // Handle nested blocks (C-blocks)
            if (currentBlock.inputs) {
                const inputs = currentBlock.inputs();
                inputs.forEach((input, index) => {
                    if (input instanceof BlockMorph) {
                        blockInfo.nested_blocks = this.getBlocksInfo(input, depth + 1);
                    }
                });
            }

            blocks.push(blockInfo);
            currentBlock = currentBlock.nextBlock ? currentBlock.nextBlock() : null;
        }

        return blocks;
    }

    /**
     * Get block category
     */
    getBlockCategory(block) {
        if (block.category) {
            return block.category;
        }
        
        // Try to determine category from block color or type
        const color = block.color;
        if (color) {
            // Map colors to categories (approximate)
            const colorMap = {
                '#4a6cd4': 'motion',
                '#8a55d7': 'looks',
                '#bb42c3': 'sound',
                '#c88330': 'events',
                '#e1a91a': 'control',
                '#2ca5e2': 'sensing',
                '#5cb712': 'operators',
                '#ee7d16': 'variables'
            };
            return colorMap[color.toString()] || 'unknown';
        }
        
        return 'unknown';
    }

    /**
     * Get block inputs
     */
    getBlockInputs(block) {
        const inputs = {};
        
        if (block.inputs) {
            const inputSlots = block.inputs();
            inputSlots.forEach((input, index) => {
                if (input.contents) {
                    inputs[`input_${index}`] = input.contents();
                } else if (input instanceof BlockMorph) {
                    inputs[`input_${index}`] = `[${input.selector || 'block'}]`;
                }
            });
        }

        return inputs;
    }

    /**
     * Get global variables
     */
    getGlobalVariables() {
        const stage = this.getStage();
        const variables = [];

        if (stage.variables) {
            stage.variables.names().forEach(name => {
                variables.push({
                    name: name,
                    value: stage.variables.getVar(name)
                });
            });
        }

        return variables;
    }

    /**
     * Get sprite variables
     */
    getSpriteVariables(sprite) {
        const variables = [];

        if (sprite.variables) {
            sprite.variables.names().forEach(name => {
                variables.push({
                    name: name,
                    value: sprite.variables.getVar(name)
                });
            });
        }

        return variables;
    }

    /**
     * Get custom blocks
     */
    getCustomBlocks() {
        const ide = this.getIDE();
        const customBlocks = [];

        // Get global custom blocks
        if (ide.stage.customBlocks) {
            ide.stage.customBlocks.forEach(block => {
                customBlocks.push({
                    name: block.blockSpec(),
                    category: block.category,
                    scope: 'global'
                });
            });
        }

        // Get sprite-specific custom blocks
        ide.sprites.asArray().forEach(sprite => {
            if (sprite.customBlocks) {
                sprite.customBlocks.forEach(block => {
                    customBlocks.push({
                        name: block.blockSpec(),
                        category: block.category,
                        scope: 'sprite',
                        sprite: sprite.name
                    });
                });
            }
        });

        return customBlocks;
    }

    /**
     * Execute JavaScript code in Snap! context
     */
    async executeScript(payload) {
        try {
            const { javascript_code, return_result, sandbox_mode } = payload;
            
            let result;
            const startTime = performance.now();

            if (sandbox_mode) {
                // Execute in limited context
                result = this.executeSandboxed(javascript_code);
            } else {
                // Execute directly (be careful!)
                result = eval(javascript_code);
            }

            const executionTime = performance.now() - startTime;

            return {
                result: return_result ? result : null,
                execution_time_ms: executionTime,
                side_effects: this.detectSideEffects()
            };

        } catch (error) {
            console.error('Script execution error:', error);
            throw error;
        }
    }

    /**
     * Execute code in sandboxed environment
     */
    executeSandboxed(code) {
        // Create limited context
        const sandbox = {
            ide: this.getIDE(),
            stage: this.getStage(),
            sprite: this.getIDE().currentSprite,
            // Add safe utilities
            console: {
                log: console.log.bind(console)
            }
        };

        // Execute with limited scope
        const func = new Function(...Object.keys(sandbox), code);
        return func(...Object.values(sandbox));
    }

    /**
     * Detect side effects from script execution
     */
    detectSideEffects() {
        // Simple side effect detection
        return {
            sprite_moved: false, // Would need to track position changes
            sprite_shown: false, // Would need to track visibility changes
            variables_changed: false // Would need to track variable changes
        };
    }

    /**
     * Inspect specific state
     */
    async inspectState(payload) {
        try {
            const { query } = payload;
            
            switch (query.type) {
                case 'blocks_at_position':
                    return this.getBlocksAtPosition(query);
                case 'sprite_info':
                    return this.getSpriteInfo(query.sprite);
                case 'variable_value':
                    return this.getVariableValue(query.variable);
                default:
                    throw new Error(`Unknown query type: ${query.type}`);
            }

        } catch (error) {
            console.error('State inspection error:', error);
            throw error;
        }
    }

    /**
     * Get blocks at specific position
     */
    getBlocksAtPosition(query) {
        const { sprite, x, y, radius } = query;
        const targetSprite = this.getIDE().sprites.detect(s => s.name === sprite);
        
        if (!targetSprite) {
            throw new Error(`Sprite '${sprite}' not found`);
        }

        const blocksFound = [];
        const searchRadius = radius || 50;

        targetSprite.scripts.children.forEach(script => {
            const scriptPos = script.position();
            const distance = Math.sqrt(
                Math.pow(scriptPos.x - x, 2) + Math.pow(scriptPos.y - y, 2)
            );

            if (distance <= searchRadius) {
                blocksFound.push({
                    block_id: script.blockId || 'unknown',
                    opcode: script.selector || 'unknown',
                    position: { x: scriptPos.x, y: scriptPos.y },
                    connected_blocks: this.countConnectedBlocks(script)
                });
            }
        });

        return {
            blocks_found: blocksFound,
            total_count: blocksFound.length
        };
    }

    /**
     * Count connected blocks in a script
     */
    countConnectedBlocks(block) {
        let count = 0;
        let current = block;

        while (current) {
            count++;
            current = current.nextBlock ? current.nextBlock() : null;
        }

        return count;
    }

    /**
     * Export project
     */
    async exportProject(payload) {
        try {
            const { format, include_media, compress } = payload;
            const ide = this.getIDE();
            
            let projectData;
            
            if (format === 'xml') {
                projectData = ide.serializer.serialize(ide.stage);
            } else if (format === 'json') {
                // Convert XML to JSON (simplified)
                const xmlData = ide.serializer.serialize(ide.stage);
                projectData = JSON.stringify({ xml: xmlData });
            } else {
                throw new Error(`Unsupported format: ${format}`);
            }

            return {
                project_data: projectData,
                size_bytes: projectData.length,
                format: format
            };

        } catch (error) {
            console.error('Project export error:', error);
            throw error;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SnapAPIWrapper;
}
