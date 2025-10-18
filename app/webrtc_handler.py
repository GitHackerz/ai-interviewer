"""
WebRTC handler using aiortc
Manages WebRTC connections, audio/video tracks, and processing pipeline
"""
import asyncio
import uuid
import logging
from typing import Dict, Set, Optional
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaRelay, MediaBlackhole
from av import AudioFrame, VideoFrame
import fractions

from app.stt import get_stt_handler
from app.llm import get_llm_handler
from app.tts import get_tts_handler

logger = logging.getLogger(__name__)


class AudioProcessor(MediaStreamTrack):
    """
    Audio processor track that:
    1. Receives audio from user
    2. Accumulates audio buffer
    3. Transcribes speech
    4. Gets AI response
    5. Synthesizes response to audio
    6. Sends audio back to user
    """
    
    kind = "audio"
    
    def __init__(self, track: MediaStreamTrack):
        super().__init__()
        self.track = track
        self.audio_buffer = []
        self.buffer_duration = 0.0
        self.processing = False
        self.response_queue = asyncio.Queue()
        
        # Initialize handlers
        self.stt = get_stt_handler()
        self.llm = get_llm_handler()
        self.tts = get_tts_handler()
        
        # Audio settings
        self.sample_rate = 16000
        self.silence_threshold = 2.0  # seconds of silence before processing
        self.silence_duration = 0.0
        
    async def recv(self):
        """Receive and process audio frames"""
        frame = await self.track.recv()
        
        # Convert frame to numpy array
        audio_data = frame.to_ndarray()
        
        # Accumulate audio buffer
        self.audio_buffer.append(audio_data)
        self.buffer_duration += frame.samples / frame.sample_rate
        
        # Detect silence (simple energy-based)
        energy = np.sqrt(np.mean(audio_data.astype(float) ** 2))
        
        if energy < 0.01:  # Silence threshold
            self.silence_duration += frame.samples / frame.sample_rate
        else:
            self.silence_duration = 0.0
        
        # Process buffer when silence detected
        if (self.silence_duration >= self.silence_threshold and 
            self.buffer_duration >= 1.0 and 
            not self.processing):
            asyncio.create_task(self._process_audio_buffer())
        
        # Check if we have a response to send
        if not self.response_queue.empty():
            response_frame = await self.response_queue.get()
            return response_frame
        
        # Return the original frame (pass-through)
        return frame
    
    async def _process_audio_buffer(self):
        """Process accumulated audio buffer through STT -> LLM -> TTS"""
        self.processing = True
        
        try:
            # Concatenate audio buffer
            if not self.audio_buffer:
                return
                
            audio_array = np.concatenate(self.audio_buffer, axis=1)
            
            # Convert to mono if stereo
            if audio_array.shape[0] > 1:
                audio_array = np.mean(audio_array, axis=0)
            else:
                audio_array = audio_array[0]
            
            # Normalize to float32
            audio_array = audio_array.astype(np.float32)
            
            logger.info(f"Processing audio buffer: {self.buffer_duration:.2f}s")
            
            # Step 1: Transcribe audio (STT)
            transcription = await self.stt.transcribe(audio_array, self.sample_rate)
            
            if not transcription or len(transcription.strip()) < 3:
                logger.info("No speech detected, skipping")
                return
            
            logger.info(f"User said: {transcription}")
            
            # Step 2: Get AI response (LLM)
            ai_response = await self.llm.get_response(transcription)
            logger.info(f"AI response: {ai_response}")
            
            # Step 3: Convert to speech (TTS)
            response_audio, response_sr = await self.tts.synthesize(ai_response)
            
            # Step 4: Queue response audio for transmission
            await self._queue_audio_response(response_audio, response_sr)
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}", exc_info=True)
            
        finally:
            # Clear buffer
            self.audio_buffer = []
            self.buffer_duration = 0.0
            self.silence_duration = 0.0
            self.processing = False
    
    async def _queue_audio_response(self, audio_data: np.ndarray, sample_rate: int):
        """Queue audio response frames for transmission"""
        try:
            # Convert int16 to float32 and normalize
            audio_float = audio_data.astype(np.float32) / 32768.0
            
            # Create chunks (20ms per frame)
            samples_per_frame = int(sample_rate * 0.02)
            
            for i in range(0, len(audio_float), samples_per_frame):
                chunk = audio_float[i:i + samples_per_frame]
                
                # Pad last chunk if needed
                if len(chunk) < samples_per_frame:
                    chunk = np.pad(chunk, (0, samples_per_frame - len(chunk)))
                
                # Reshape to (channels, samples) - mono audio
                chunk = chunk.reshape(1, -1)
                
                # Create audio frame
                frame = AudioFrame.from_ndarray(
                    chunk,
                    format='flt',
                    layout='mono'
                )
                frame.sample_rate = sample_rate
                frame.time_base = fractions.Fraction(1, sample_rate)
                
                # Queue frame
                await self.response_queue.put(frame)
                
        except Exception as e:
            logger.error(f"Error queuing audio response: {e}", exc_info=True)


class VideoPassthrough(MediaStreamTrack):
    """Simple video passthrough track"""
    
    kind = "video"
    
    def __init__(self, track: MediaStreamTrack):
        super().__init__()
        self.track = track
    
    async def recv(self):
        frame = await self.track.recv()
        return frame


class WebRTCHandler:
    """Manages WebRTC peer connections"""
    
    def __init__(self):
        self.peers: Dict[str, RTCPeerConnection] = {}
        self.relay = MediaRelay()
        
    def create_peer_connection(self) -> tuple[str, RTCPeerConnection]:
        """Create a new peer connection"""
        peer_id = str(uuid.uuid4())
        
        # Configure ICE servers (use STUN for NAT traversal)
        config = RTCConfiguration(
            iceServers=[
                RTCIceServer(urls=["stun:stun.l.google.com:19302"])
            ]
        )
        
        pc = RTCPeerConnection(configuration=config)
        self.peers[peer_id] = pc
        
        @pc.on("track")
        async def on_track(track):
            logger.info(f"Track received: {track.kind}")
            
            if track.kind == "audio":
                # Process audio through STT -> LLM -> TTS pipeline
                processor = AudioProcessor(track)
                pc.addTrack(processor)
                
            elif track.kind == "video":
                # Simple video passthrough
                passthrough = VideoPassthrough(track)
                pc.addTrack(passthrough)
        
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state: {pc.connectionState}")
            if pc.connectionState == "failed" or pc.connectionState == "closed":
                await self.close_peer_connection(peer_id)
        
        return peer_id, pc
    
    async def close_peer_connection(self, peer_id: str):
        """Close and remove a peer connection"""
        if peer_id in self.peers:
            pc = self.peers[peer_id]
            await pc.close()
            del self.peers[peer_id]
            logger.info(f"Closed peer connection: {peer_id}")
    
    async def cleanup(self):
        """Close all peer connections"""
        for peer_id in list(self.peers.keys()):
            await self.close_peer_connection(peer_id)


# Global WebRTC handler instance
_webrtc_handler: Optional[WebRTCHandler] = None


def get_webrtc_handler() -> WebRTCHandler:
    """Get or create global WebRTC handler"""
    global _webrtc_handler
    if _webrtc_handler is None:
        _webrtc_handler = WebRTCHandler()
    return _webrtc_handler
