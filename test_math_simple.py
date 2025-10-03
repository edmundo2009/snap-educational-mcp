#!/usr/bin/env python3
"""
Simple test to verify math pattern generation works
"""

import sys
import os
sys.path.append('.')

def test_math_parsing():
    """Test math problem parsing"""
    print("🧮 Testing Math Problem Parsing...")
    
    try:
        from mcp_server.parsers.math_parser import parse_math_problem
        
        # Test cases
        test_problems = [
            "If 7 hours to mow 4 lawns, how many in 35 hours?",
            "Ratio 3:2, scale by 4",
            "Divide 20 cookies among 5 kids"
        ]
        
        for problem in test_problems:
            print(f"\n📝 Testing: '{problem}'")
            result = parse_math_problem(problem)
            print(f"   Pattern: {result['pattern']}")
            print(f"   Numbers: {result['numbers']}")
            
        print("\n✅ Math parsing test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Math parsing test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_math_generation():
    """Test math block generation"""
    print("\n🔧 Testing Math Block Generation...")
    
    try:
        from mcp_server.parsers.math_parser import parse_math_problem
        from mcp_server.tools.block_generator import SnapBlockGenerator
        
        # Parse a problem
        problem = "If 7 hours to mow 4 lawns, how many in 35 hours?"
        parsed = parse_math_problem(problem)
        print(f"📊 Parsed: {parsed}")
        
        if not parsed["pattern"]:
            print("❌ No pattern detected!")
            return False
            
        # Generate blocks
        generator = SnapBlockGenerator(
            knowledge_path='mcp_server/knowledge/snap_blocks.json',
            patterns_path='mcp_server/knowledge/patterns.json'
        )
        
        result = generator.generate_from_math_pattern(parsed)
        
        if "error" in result.get("payload", {}):
            print(f"❌ Generation error: {result['payload']['error']}")
            return False
            
        # Check result
        blocks = result.get("payload", {}).get("scripts", [{}])[0].get("blocks", [])
        print(f"✅ Generated {len(blocks)} blocks successfully!")
        print(f"   Pattern: {parsed['pattern']}")
        print(f"   Numbers: {parsed['numbers']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Math generation test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Math POC Tests...\n")
    
    # Test 1: Math parsing
    parsing_ok = test_math_parsing()
    
    # Test 2: Math generation  
    generation_ok = test_math_generation()
    
    # Summary
    print("\n" + "="*50)
    print("📋 TEST SUMMARY:")
    print(f"   Math Parsing: {'✅ PASS' if parsing_ok else '❌ FAIL'}")
    print(f"   Math Generation: {'✅ PASS' if generation_ok else '❌ FAIL'}")
    
    if parsing_ok and generation_ok:
        print("\n🎉 ALL TESTS PASSED! Math POC is working!")
        print("   The issue is likely in the communication layer.")
        print("   Try using execution_mode='preview' to test without WebSocket.")
    else:
        print("\n⚠️  Some tests failed. Fix these issues first.")
    
    print("="*50)

if __name__ == "__main__":
    main()
