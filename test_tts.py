"""
Test TTS functionality
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.tts import TTSHandler

async def test_tts():
    print("Initializing TTS...")
    tts = TTSHandler()
    await tts.initialize()
    
    print("Synthesizing speech...")
    text = "Hello! This is a test of the text to speech system."
    audio_data, sample_rate = await tts.synthesize(text)
    
    print(f"Generated audio: {len(audio_data)} samples at {sample_rate}Hz")
    print(f"Duration: {len(audio_data) / sample_rate:.2f} seconds")
    print(f"Audio dtype: {audio_data.dtype}")
    print(f"Audio shape: {audio_data.shape}")
    print(f"Audio min/max: {audio_data.min()} / {audio_data.max()}")

if __name__ == "__main__":
    asyncio.run(test_tts())
