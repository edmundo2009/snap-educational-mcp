// browser_extension/snap_bridge/block_creator.js - Snap! Block Creation and Manipulation

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
      throw new Error(
        "SnapBlockCreator requires an instance of SnapAPIWrapper."
      );
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
   * Finds and sets the current sprite in the Snap! IDE.
   * @param {string | null} spriteName - The name of the sprite to find. If null, uses the IDE's currently selected sprite.
   * @returns {SpriteMorph} The found or current sprite.
   */
  getCurrentSprite(spriteName = null) {
    const ide = this.apiWrapper.getIDE();
    if (!ide) {
      throw new Error("Cannot get current sprite: Snap! IDE is not available.");
    }

    if (spriteName) {
      // --- THIS IS THE FIX ---
      // 1. Get the Snap! sprite collection: ide.sprites
      // 2. Convert it into a standard JavaScript array using .asArray()
      const spritesAsArray = ide.sprites.asArray();

      // 3. Use the standard JavaScript .find() method on the resulting array.
      const sprite = spritesAsArray.find((s) => s.name === spriteName);

      if (sprite) {
        // This part of the logic was already correct.
        ide.selectSprite(sprite);
        this.currentSprite = sprite;
      } else {
        // It's good practice to list available sprites on error.
        const availableNames = spritesAsArray.map((s) => s.name).join(", ");
        throw new Error(
          `Sprite '${spriteName}' not found. Available sprites are: [${availableNames}]`
        );
      }
    } else {
      // This fallback logic is correct.
      this.currentSprite = ide.currentSprite;
    }

    if (!this.currentSprite) {
      throw new Error("Could not determine the current sprite.");
    }

    return this.currentSprite;
  }

  /**
   * Create blocks from specification
   */
  async createBlocks(payload) {
    // Check if Snap! environment is ready using the unified check
    if (!this.apiWrapper.isReady()) {
      throw new Error(
        "Snap! environment is not ready. Please wait for Snap! to fully load and try again."
      );
    }

    // --- DEFENSIVE CHECK ---
    // This handles the server sending a double-nested payload.
    let finalPayload = payload;
    if (payload && payload.payload && payload.command === "create_blocks") {
      console.warn(
        "⚠️ Detected double-nested payload. Unwrapping it. Please fix the server-side logic in snap_communicator.py."
      );
      finalPayload = payload.payload;
    }

    // Now, destructure from the corrected payload.
    const { target_sprite, scripts, visual_feedback } = finalPayload;

    // A more specific check for the error you saw.
    if (!scripts || typeof scripts[Symbol.iterator] !== "function") {
      console.error(
        "❌ createBlocks error: The `scripts` property in the payload is missing or not an array.",
        finalPayload
      );
      throw new Error("Invalid payload: `scripts` is not iterable.");
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
        scriptBlocks.forEach((block) => {
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
        status: "success",
        blocks_created: totalBlocksCreated,
        scripts_created: scriptsCreated,
        execution_time_ms: Date.now() - performance.now(),
        created_block_ids: createdBlockIds,
        sprite_info: {
          name: sprite.name,
          position: { x: sprite.xPosition(), y: sprite.yPosition() },
          total_scripts: sprite.scripts.children.length,
        },
      };
    } catch (error) {
      console.error("Block creation error:", error);
      throw error;
    }
  }

  // Revert createScript to its simpler, original form
  async createScript(blockSpecs, position = { x: 50, y: 50 }) {
    const sprite = this.getCurrentSprite();
    const createdBlocks = [];
    let previousBlock = null;

    for (let i = 0; i < blockSpecs.length; i++) {
      const blockSpec = blockSpecs[i];
      const block = await this.createSingleBlock(blockSpec, sprite);

      if (block) {
        createdBlocks.push(block);
        if (previousBlock) {
          this.connectBlocks(previousBlock, block);
        }
        previousBlock = block;
      }
    }

    if (createdBlocks.length > 0) {
      const firstBlock = createdBlocks[0];
      firstBlock.setPosition(new Point(position.x, position.y));
      sprite.scripts.add(firstBlock);
    }

    // A single changed() at the end is sufficient.
    sprite.scripts.changed();
    return createdBlocks;
  }

  /**
   * Create a single block from specification.
   * This version is a minimal, evidence-based implementation based on our debugging findings.
   */
  async createSingleBlock(blockSpec, sprite) {
    try {
      const { opcode, category, inputs, block_id } = blockSpec;
      const ide = this.apiWrapper.getIDE();

      const selectorMap = {
        // Reverted to the proven, working selector.
        whenGreenFlag: "receiveGo",
        doSay: "doSayFor",
      };
      const selector = selectorMap[opcode] || opcode;
      const block = sprite.blockForSelector(selector);

      if (!block) {
        // This error is now critical for debugging.
        console.error(
          `Block creation failed for opcode: '${opcode}' (using selector '${selector}')`
        );
        return null;
      }

      if (opcode === "doSetVar") {
        if (inputs && inputs.VAR !== undefined && inputs.VALUE !== undefined) {
          const varName = inputs.VAR;
          sprite.variables.addVar(varName);
          const variableObject = sprite.variables.getVar(varName);

          const variableInput = block.inputs()[0];
          const valueInput = block.inputs()[1];

          // The core hypothesis: Set the data, then trigger a generic refresh.
          // 1. Set the block's internal data model.
          variableInput.setContents(variableObject);

          // 2. Tell the dropdown it has changed, forcing a redraw.
          variableInput.changed();

          // 3. Set the value.
          valueInput.setContents(inputs.VALUE);
        }
      } else if (opcode === "doSay") {
        if (inputs && inputs.MESSAGE !== undefined) {
          block.inputs()[0].setContents(inputs.MESSAGE);
          const duration = inputs.DURATION !== undefined ? inputs.DURATION : 2;
          block.inputs()[1].setContents(duration);
        }
      }

      if (block_id) {
        block.blockId = block_id;
      }

      block.setColor(ide.palette[category]);
      block.fixLayout();

      return block;
    } catch (error) {
      console.error(
        `Error in createSingleBlock for opcode ${blockSpec.opcode}:`,
        error
      );
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
          if (typeof inputValue === "string") {
            inputSlots[index].setContents(inputValue);
          } else if (typeof inputValue === "number") {
            inputSlots[index].setContents(inputValue);
          } else {
            // Handle complex inputs (blocks, etc.)
            inputSlots[index].setContents(inputValue);
          }
        }
      });
    } catch (error) {
      console.error("Error setting block inputs:", error);
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
      console.error("Error connecting blocks:", error);
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

      if (selection.type === "by_id") {
        // Delete specific blocks by ID
        selection.block_ids.forEach((blockId) => {
          const block = this.findBlockById(sprite, blockId);
          if (block) {
            block.destroy();
            deletedCount++;
          }
        });
      } else if (selection.type === "all_scripts") {
        // Delete all scripts
        sprite.scripts.children.slice().forEach((script) => {
          script.destroy();
          deletedCount++;
        });
      }

      return {
        status: "success",
        blocks_deleted: deletedCount,
      };
    } catch (error) {
      console.error("Block deletion error:", error);
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
        scope === "global"
      );

      // Set parameters
      if (parameters && parameters.length > 0) {
        parameters.forEach((param) => {
          customBlock.addParameter(param.name, param.type);
        });
      }

      // Set definition (body)
      if (definition && definition.length > 0) {
        const bodyBlocks = await this.createScript(definition);
        customBlock.body = new Context(null, bodyBlocks[0]);
      }

      // Set category
      customBlock.category = category || "custom";

      // Add to sprite
      sprite.customBlocks.push(customBlock);

      // Refresh palette
      this.getIDE().flushBlocksCache();
      this.getIDE().refreshPalette();

      return {
        status: "success",
        block_name: block_name,
        message: `Custom block '${block_name}' created successfully`,
      };
    } catch (error) {
      console.error("Custom block creation error:", error);
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
      await new Promise((resolve) => setTimeout(resolve, 200));
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
      ide.inform("Snap! Educational Assistant", text);
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
