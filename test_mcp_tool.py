#!/usr/bin/env python3
"""
Test the generate_math_blocks MCP tool directly
"""

import sys
import asyncio
sys.path.append('.')

async def test_generate_math_blocks():
    """Test the generate_math_blocks MCP tool"""
    print("🧮 Testing generate_math_blocks MCP tool...")
    
    try:
        # Import the function directly
        from mcp_server.main import generate_math_blocks
        
        # Test with preview mode (no WebSocket needed)
        problem = "If 7 hours to mow 4 lawns, how many in 35 hours?"
        
        print(f"📝 Testing problem: '{problem}'")
        print("🔍 Using execution_mode='preview' (no WebSocket needed)")
        
        result = await generate_math_blocks(
            problem_text=problem,
            grade_level=6,
            execution_mode="preview",  # This avoids WebSocket communication
            target_sprite="Sprite"
        )
        
        print("\n📊 Result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Mode: {result.get('mode', 'unknown')}")
        print(f"   Pattern: {result.get('pattern', 'none')}")
        print(f"   Numbers: {result.get('numbers', [])}")
        
        if result.get('success'):
            block_count = result.get('block_count', 0)
            print(f"   Blocks generated: {block_count}")
            
            if 'snap_json' in result:
                print("   ✅ Snap JSON generated successfully!")
                
                # Show a sample of the blocks
                snap_json = result['snap_json']
                if 'payload' in snap_json and 'scripts' in snap_json['payload']:
                    scripts = snap_json['payload']['scripts']
                    if scripts and 'blocks' in scripts[0]:
                        blocks = scripts[0]['blocks']
                        print(f"   📋 Sample blocks (first 3 of {len(blocks)}):")
                        for i, block in enumerate(blocks[:3]):
                            opcode = block.get('opcode', 'unknown')
                            print(f"      {i+1}. {opcode}")
                        if len(blocks) > 3:
                            print(f"      ... and {len(blocks) - 3} more blocks")
            
            print("\n🎉 generate_math_blocks MCP tool is working perfectly!")
            return True
        else:
            error = result.get('error', 'Unknown error')
            print(f"   ❌ Error: {error}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test"""
    print("🚀 Testing Math POC MCP Tool...\n")
    
    success = await test_generate_math_blocks()
    
    print("\n" + "="*60)
    if success:
        print("✅ SUCCESS: The math POC is working correctly!")
        print("\n💡 Next steps:")
        print("   1. The issue is likely in WebSocket communication")
        print("   2. Try using execution_mode='preview' in your CLI tests")
        print("   3. Check if the browser extension is properly connected")
        print("   4. Verify the session_id is valid")
    else:
        print("❌ FAILURE: There are still issues to fix")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
