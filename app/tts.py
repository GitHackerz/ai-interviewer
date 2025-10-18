"""
Text-to-Speech module using pyttsx3
Converts AI text responses to speech audio
"""
import os
import asyncio
import tempfile
from typing import Optional
import numpy as np
import pyttsx3
import wave
import logging

logger = logging.getLogger(__name__)


class TTSHandler:
    def __init__(
        self,
        rate: int = 150,
        volume: float = 0.9
    ):
        """
        Initialize TTS Handler
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
        """
        self.rate = rate
        self.volume = volume
        self.engine: Optional[pyttsx3.Engine] = None
        
    async def initialize(self):
        """Load the TTS engine asynchronously"""
        loop = asyncio.get_event_loop()
        self.engine = await loop.run_in_executor(
            None,
            lambda: pyttsx3.init()
        )
        self.engine.setProperty('rate', self.rate)
        self.engine.setProperty('volume', self.volume)
        logger.info(f"TTS engine initialized (rate={self.rate}, volume={self.volume})")
        
    async def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        """
        Convert text to speech audio
        
        Args:
            text: Text to synthesize
            
        Returns:
            Tuple of (audio as numpy array, sample rate)
        """
        if self.engine is None:
            await self.initialize()
            
        try:
            # Run TTS in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            # Generate speech
            await loop.run_in_executor(
                None,
                lambda: self.engine.save_to_file(text, tmp_path)
            )
            await loop.run_in_executor(None, self.engine.runAndWait)
            
            # Load the audio file
            with wave.open(tmp_path, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
                audio_data = np.frombuffer(frames, dtype=np.int16)
                
            # Clean up temp file
            os.unlink(tmp_path)
            
            logger.info(f"Synthesized speech for text: {text[:50]}...")
            return audio_data, sample_rate
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            # Return empty audio on error
            return np.array([], dtype=np.int16), 16000
    
    async def synthesize_streaming(self, text: str):
        """
        Convert text to speech with streaming support (for future enhancement)
        Currently generates full audio then yields chunks
        
        Args:
            text: Text to synthesize
            
        Yields:
            Audio chunks as numpy arrays
        """
        audio_data, sample_rate = await self.synthesize(text)
        
        # Chunk size: 0.1 second chunks
        chunk_size = int(sample_rate * 0.1)
        
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            yield chunk, sample_rate
    
    async def text_to_wav_file(self, text: str, output_path: str):
        """
        Convert text to speech and save to WAV file
        
        Args:
            text: Text to synthesize
            output_path: Path to save WAV file
        """
        if self.engine is None:
            await self.initialize()
            
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.engine.save_to_file(text, output_path)
            )
            await loop.run_in_executor(None, self.engine.runAndWait)
            logger.info(f"Saved speech to {output_path}")
            
        except Exception as e:
            logger.error(f"TTS file save error: {e}")


# Global TTS handler instance
_tts_handler: Optional[TTSHandler] = None


def get_tts_handler() -> TTSHandler:
    """Get or create global TTS handler"""
    global _tts_handler
    if _tts_handler is None:
        rate = int(os.getenv("TTS_RATE", "150"))
        volume = float(os.getenv("TTS_VOLUME", "0.9"))
        _tts_handler = TTSHandler(rate, volume)
    return _tts_handler
