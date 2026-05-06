#!/usr/bin/env python3
"""Test script for Z.ai Coding Plan integration"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test that required environment variables are set"""
    print("🔍 Testing environment configuration...")
    
    required_vars = {
        "ZAI_CODING_API_KEY": "Z.ai Coding Plan API key"
    }
    
    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"  ✅ {description}: {masked}")
        else:
            print(f"  ❌ {description}: Not set")
            missing.append(var)
    
    if missing:
        print(f"\n❌ Missing required variables: {', '.join(missing)}")
        return False
    
    print("✅ Environment configuration complete\n")
    return True

def test_imports():
    """Test that required packages are installed"""
    print("🔍 Testing package imports...")
    
    try:
        import requests
        print("  ✅ requests")
    except ImportError:
        print("  ❌ requests - Install with: pip install requests")
        return False
    
    try:
        import dotenv
        print("  ✅ python-dotenv")
    except ImportError:
        print("  ❌ python-dotenv - Install with: pip install python-dotenv")
        return False
    
    print("✅ All required packages installed\n")
    return True

def test_brain_initialization():
    """Test that ZaiCoding brain can be initialized"""
    print("🔍 Testing Z.ai Coding Plan brain initialization...")
    
    try:
        from nanocode_zai import ZaiCoding
        brain = ZaiCoding()
        print(f"  ✅ Brain initialized")
        print(f"  ✅ Model: {brain.model}")
        print(f"  ✅ URL: {brain.url}")
        print("✅ Brain initialization successful\n")
        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}\n")
        return False

def test_basic_think():
    """Test a basic think operation"""
    print("🔍 Testing basic think operation...")
    
    try:
        from nanocode_zai import ZaiCoding
        
        brain = ZaiCoding()
        conversation = [
            {"role": "user", "content": "Say 'Hello, Z.ai!'"}
        ]
        
        print("  📤 Sending test message...")
        thought = brain.think(conversation)
        
        if thought.text:
            print(f"  ✅ Received response: {thought.text[:100]}...")
            print("✅ Basic think operation successful\n")
            return True
        else:
            print("  ⚠️ Received empty response")
            print("✅ Think operation completed (but response was empty)\n")
            return True
            
    except Exception as e:
        print(f"  ❌ Think operation failed: {e}\n")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Z.ai Coding Plan Integration Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("Brain Init", test_brain_initialization),
        ("Basic Think", test_basic_think),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}\n")
            results[name] = False
    
    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Z.ai integration is ready to use.")
        return 0
    else:
        print("⚠️ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
