"""
Speech-to-Text module using faster-whisper
Handles audio transcription with async support
"""
import asyncio
import os
from typing import Optional
import numpy as np
from faster_whisper import WhisperModel
import logging

logger = logging.getLogger(__name__)


class STTHandler:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """
        Initialize Whisper STT Handler
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            compute_type: Computation type (int8, float16, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None
        
    async def initialize(self):
        """Load the Whisper model asynchronously"""
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None,
            lambda: WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        )
        logger.info(f"Whisper model '{self.model_size}' loaded on {self.device}")
        
    async def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribe audio data to text
        
        Args:
            audio_data: Audio as numpy array (float32, mono)
            sample_rate: Sample rate of the audio (default 16000)
            
        Returns:
            Transcribed text
        """
        if self.model is None:
            await self.initialize()
            
        try:
            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(
                    audio_data,
                    language="en",
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=500
                    )
                )
            )
            
            # Collect all segments
            text_parts = []
            async for segment in self._async_segment_iterator(segments):
                text_parts.append(segment.text.strip())
                
            transcription = " ".join(text_parts)
            logger.info(f"Transcribed: {transcription[:100]}...")
            return transcription
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    async def _async_segment_iterator(self, segments):
        """Convert segment iterator to async iterator"""
        loop = asyncio.get_event_loop()
        segments_list = await loop.run_in_executor(None, list, segments)
        for segment in segments_list:
            yield segment
            
    async def transcribe_file(self, audio_path: str) -> str:
        """
        Transcribe audio from file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        if self.model is None:
            await self.initialize()
            
        try:
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(audio_path, language="en")
            )
            
            text_parts = []
            async for segment in self._async_segment_iterator(segments):
                text_parts.append(segment.text.strip())
                
            return " ".join(text_parts)
            
        except Exception as e:
            logger.error(f"File transcription error: {e}")
            return ""


# Global STT handler instance
_stt_handler: Optional[STTHandler] = None


def get_stt_handler() -> STTHandler:
    """Get or create global STT handler"""
    global _stt_handler
    if _stt_handler is None:
        model_size = os.getenv("WHISPER_MODEL", "base")
        device = os.getenv("WHISPER_DEVICE", "cpu")
        compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        _stt_handler = STTHandler(model_size, device, compute_type)
    return _stt_handler
