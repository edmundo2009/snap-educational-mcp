# Debugging: TypeError: Cannot read properties of undefined (reading 'currentSprite')

## Error Summary

**Error Location:** `browser_extension/snap_bridge/block_creator.js:63`  
**Error Message:** `TypeError: Cannot read properties of undefined (reading 'currentSprite')`  
**Call Stack:**
```
SnapBlockCreator.getCurrentSprite (block_creator.js:63:38)
SnapBlockCreator.createBlocks (block_creator.js:77:33)
SnapBridge.handleCommand (bridge.js:304:54)
```

## Root Cause Analysis

The error occurs at line 63 in `getCurrentSprite()` method:

```javascript
// Line 63 in browser_extension/snap_bridge/block_creator.js
this.currentSprite = ide.currentSprite;
```

The issue is that `ide` (returned by `this.getIDE()`) is `undefined`, which means `world.children[0]` is returning `undefined`.

### Code Flow Analysis

1. **Command Execution Path:**
   - `SnapBridge.handleCommand()` calls `this.blockCreator.createBlocks()`
   - `createBlocks()` calls `this.getCurrentSprite(target_sprite)`
   - `getCurrentSprite()` calls `this.getIDE()`
   - `getIDE()` returns `world.children[0]`
   - `world.children[0]` is `undefined`

2. **Current Implementation:**
   ```javascript
   // browser_extension/snap_bridge/block_creator.js:30-35
   getIDE() {
       if (!this.ide) {
           this.ide = world.children[0];  // ← This returns undefined
       }
       return this.ide;
   }
   ```

## Probable Causes

### 1. **Snap! Environment Not Fully Loaded**
- The Snap! IDE may not be fully initialized when the command is executed
- `world.children[0]` might not contain the IDE_Morph yet
- **Likelihood:** High

### 2. **Incorrect DOM Structure Access**
- The assumption that `world.children[0]` is the IDE might be incorrect
- Snap! might have changed its internal structure
- **Likelihood:** Medium

### 3. **Timing Issue**
- The extension might be executing before Snap! is ready
- Race condition between extension initialization and Snap! loading
- **Likelihood:** High

### 4. **Missing Snap! Global Objects**
- The `world` object might not be available in the current context
- Content Security Policy might be blocking access
- **Likelihood:** Medium

## Diagnostic Steps

### Step 1: Check Snap! Environment Availability
Add debugging to verify what's available:

```javascript
// Add to browser_extension/snap_bridge/block_creator.js:30
getIDE() {
    console.log('🔍 Debugging getIDE():');
    console.log('  typeof world:', typeof world);
    console.log('  world:', world);
    console.log('  world.children:', world?.children);
    console.log('  world.children.length:', world?.children?.length);
    console.log('  world.children[0]:', world?.children?.[0]);
    console.log('  world.children[0] type:', world?.children?.[0]?.constructor?.name);
    
    if (!this.ide) {
        this.ide = world.children[0];
    }
    return this.ide;
}
```

### Step 2: Check Alternative IDE Access Methods
The `SnapAPIWrapper` class has the same `getIDE()` implementation, suggesting we should use it:

```javascript
// Current problematic approach in block_creator.js
getIDE() {
    if (!this.ide) {
        this.ide = world.children[0];  // Direct access
    }
    return this.ide;
}

// Should use the apiWrapper instead
getIDE() {
    return this.apiWrapper.getIDE();  // Delegate to apiWrapper
}
```

## Proposed Fixes

### Fix 1: Use SnapAPIWrapper for IDE Access (Recommended)
**File:** `browser_extension/snap_bridge/block_creator.js`

```javascript
// Replace the getIDE() method (lines 30-35)
getIDE() {
    return this.apiWrapper.getIDE();
}

// Also update getCurrentSprite to use apiWrapper consistently
getCurrentSprite(spriteName = null) {
    const ide = this.apiWrapper.getIDE();  // Use apiWrapper
    
    if (spriteName) {
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
```

### Fix 2: Add Snap! Readiness Check
**File:** `browser_extension/snap_bridge/block_creator.js`

```javascript
// Add method to check if Snap! is ready
isSnapReady() {
    return typeof world !== 'undefined' && 
           world.children && 
           world.children.length > 0 && 
           world.children[0] && 
           typeof world.children[0].currentSprite !== 'undefined';
}

// Update createBlocks to check readiness
async createBlocks(payload) {
    if (!this.isSnapReady()) {
        throw new Error('Snap! environment is not ready. Please wait for Snap! to fully load.');
    }
    
    try {
        // ... rest of the method
    } catch (error) {
        console.error('Block creation error:', error);
        throw error;
    }
}
```

### Fix 3: Implement Retry Logic with Timeout
**File:** `browser_extension/snap_bridge/block_creator.js`

```javascript
// Add retry mechanism for IDE access
async getIDEWithRetry(maxRetries = 5, delay = 1000) {
    for (let i = 0; i < maxRetries; i++) {
        const ide = this.apiWrapper.getIDE();
        if (ide && ide.currentSprite !== undefined) {
            return ide;
        }
        
        console.log(`⏳ Waiting for Snap! IDE (attempt ${i + 1}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    throw new Error('Snap! IDE not available after maximum retries');
}
```

## Implementation Priority

1. **Immediate Fix:** Apply Fix 1 (Use SnapAPIWrapper) - This addresses the architectural issue
2. **Robustness:** Add Fix 2 (Readiness Check) - This prevents execution when Snap! isn't ready  
3. **Reliability:** Consider Fix 3 (Retry Logic) - This handles timing issues gracefully

## Files to Modify

1. **`browser_extension/snap_bridge/block_creator.js`**
   - Lines 30-35: `getIDE()` method
   - Lines 50-67: `getCurrentSprite()` method
   - Lines 72-131: `createBlocks()` method (add readiness check)

2. **`browser_extension/snap_bridge/bridge.js`** (Already fixed)
   - Lines 23-26: Constructor initialization

## Implementation Status

✅ **Fix 1 Applied:** Updated `getIDE()` and `getStage()` methods to use `apiWrapper`
✅ **Fix 2 Applied:** Added `isSnapReady()` check and integrated into `createBlocks()`
⏳ **Fix 3 Pending:** Retry logic can be added if needed after testing

### Changes Made:

1. **`browser_extension/snap_bridge/block_creator.js:27-32`**
   ```javascript
   getIDE() {
       return this.apiWrapper.getIDE();
   }
   ```

2. **`browser_extension/snap_bridge/block_creator.js:34-39`**
   ```javascript
   getStage() {
       return this.apiWrapper.getStage();
   }
   ```

3. **`browser_extension/snap_bridge/block_creator.js:41-53`**
   ```javascript
   isSnapReady() {
       try {
           const ide = this.apiWrapper.getIDE();
           return ide &&
                  typeof ide.currentSprite !== 'undefined' &&
                  ide.sprites &&
                  typeof ide.sprites.detect === 'function';
       } catch (error) {
           console.warn('Snap! readiness check failed:', error);
           return false;
       }
   }
   ```

4. **`browser_extension/snap_bridge/block_creator.js:82-86`**
   ```javascript
   // Check if Snap! environment is ready
   if (!this.isSnapReady()) {
       throw new Error('Snap! environment is not ready. Please wait for Snap! to fully load and try again.');
   }
   ```

## Testing Steps

1. ✅ **Reload the browser extension** in Chrome (`chrome://extensions/`)
2. ✅ **Hard refresh** the Snap! page (`Ctrl+Shift+R`)
3. 🔄 **Test command:** `rovodev snap execute "move 10 steps"`
4. 📊 **Check browser console** for any remaining errors or new debugging output
5. 🔍 **Verify** that the error message changes (should be more descriptive now)

## Related Files

- **`browser_extension/snap_bridge/snap_api_wrapper.js`** - Contains the correct IDE access pattern
- **`browser_extension/snap_bridge/bridge.js`** - Handles command routing and component initialization
- **`browser_extension/snap_bridge/page_world_script.js`** - Manages injection into Snap! page context
