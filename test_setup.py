"""
Quick test script to verify AI Interviewer setup
Tests individual components without running the full WebRTC server
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_stt():
    """Test Speech-to-Text handler"""
    print("\n[1/3] Testing STT (Whisper)...")
    try:
        from app.stt import get_stt_handler
        import numpy as np
        
        stt = get_stt_handler()
        await stt.initialize()
        
        # Test with dummy audio
        dummy_audio = np.random.randn(16000).astype(np.float32)  # 1 second
        result = await stt.transcribe(dummy_audio)
        
        print("✓ STT initialized successfully")
        print(f"  Model: {stt.model_size}, Device: {stt.device}")
        return True
    except Exception as e:
        print(f"✗ STT test failed: {e}")
        return False


async def test_llm():
    """Test LLM handler"""
    print("\n[2/3] Testing LLM (OpenRouter)...")
    try:
        from app.llm import get_llm_handler
        
        llm = get_llm_handler()
        
        # Test with simple message
        response = await llm.get_response("Hello, this is a test message.")
        
        print("✓ LLM initialized successfully")
        print(f"  Model: {llm.model}")
        print(f"  Response preview: {response[:100]}...")
        return True
    except ValueError as e:
        if "OPENROUTER_API_KEY" in str(e):
            print("✗ LLM test failed: OPENROUTER_API_KEY not set in .env")
            print("  Please add your API key to .env file")
        else:
            print(f"✗ LLM test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ LLM test failed: {e}")
        return False


async def test_tts():
    """Test Text-to-Speech handler"""
    print("\n[3/3] Testing TTS (pyttsx3)...")
    try:
        from app.tts import get_tts_handler
        
        tts = get_tts_handler()
        await tts.initialize()
        
        # Test with short text
        audio, sr = await tts.synthesize("Hello, this is a test.")
        
        print("✓ TTS initialized successfully")
        print(f"  Rate: {tts.rate}, Volume: {tts.volume}")
        print(f"  Generated {len(audio)} audio samples at {sr}Hz")
        return True
    except Exception as e:
        print(f"✗ TTS test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 50)
    print("AI Interviewer - Component Test")
    print("=" * 50)
    
    # Check environment
    print("\nChecking environment variables...")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("⚠️  OPENROUTER_API_KEY not found in .env")
        print("   Some tests may fail without it.")
    else:
        print(f"✓ OPENROUTER_API_KEY found ({api_key[:8]}...)")
    
    # Run tests
    results = []
    
    # STT test
    results.append(await test_stt())
    
    # LLM test (only if API key is set)
    if api_key:
        results.append(await test_llm())
    else:
        print("\n[2/3] Skipping LLM test (no API key)")
        results.append(False)
    
    # TTS test
    results.append(await test_tts())
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("  1. Make sure .env has your OPENROUTER_API_KEY")
        print("  2. Run: uvicorn app.main:app --reload")
        print("  3. Open: http://localhost:8000")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\nCommon issues:")
        print("  - Missing dependencies: pip install -r requirements.txt")
        print("  - Missing API key: Add OPENROUTER_API_KEY to .env")
        print("  - Model download: First run downloads models (may be slow)")


if __name__ == "__main__":
    asyncio.run(main())
