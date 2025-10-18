"""
Text-to-Speech module using gTTS and pydub
Converts AI text responses to speech audio
"""
import os
import asyncio
import tempfile
from typing import Optional
import numpy as np
from gtts import gTTS
from pydub import AudioSegment
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
            rate: Speech rate (words per minute) - not used with gTTS
            volume: Volume level (0.0 to 1.0) - not used with gTTS
        """
        self.rate = rate
        self.volume = volume
        self.initialized = False
        
    async def initialize(self):
        """Initialize TTS handler"""
        self.initialized = True
        logger.info(f"TTS handler initialized")
        
    async def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        """
        Convert text to speech audio
        
        Args:
            text: Text to synthesize
            
        Returns:
            Tuple of (audio as numpy array, sample rate)
        """
        if not self.initialized:
            await self.initialize()
            
        try:
            # Run TTS in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
                tmp_mp3_path = tmp_mp3.name
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                tmp_wav_path = tmp_wav.name
            
            # Generate speech
            await loop.run_in_executor(
                None,
                lambda: gTTS(text=text, lang='en', slow=False).save(tmp_mp3_path)
            )
            
            # Convert MP3 to WAV
            await loop.run_in_executor(
                None,
                lambda: AudioSegment.from_mp3(tmp_mp3_path).export(tmp_wav_path, format="wav")
            )
            
            # Load the audio file
            audio_segment = AudioSegment.from_wav(tmp_wav_path)
            sample_rate = audio_segment.frame_rate
            audio_data = np.array(audio_segment.get_array_of_samples(), dtype=np.int16)
            
            # Clean up temp files
            os.unlink(tmp_mp3_path)
            os.unlink(tmp_wav_path)
            
            logger.info(f"Synthesized speech for text: {text[:50]}... "
                       f"(audio length: {len(audio_data)} samples, rate: {sample_rate} Hz)")
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
        if not self.initialized:
            await self.initialize()
            
        try:
            loop = asyncio.get_event_loop()
            # Create temporary MP3 file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
                tmp_mp3_path = tmp_mp3.name
            
            # Generate speech
            await loop.run_in_executor(
                None,
                lambda: gTTS(text=text, lang='en', slow=False).save(tmp_mp3_path)
            )
            
            # Convert to WAV
            await loop.run_in_executor(
                None,
                lambda: AudioSegment.from_mp3(tmp_mp3_path).export(output_path, format="wav")
            )
            
            # Clean up
            os.unlink(tmp_mp3_path)
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
