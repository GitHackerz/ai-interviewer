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
        
        # Voice statistics
        self.voice_stats = {
            "volume_avg": 0.0,
            "volume_max": 0.0,
            "clarity_score": 0.0,
            "speaking_duration": 0.0,
            "num_utterances": 0
        }
        self.energy_samples = []
        self.greeting_sent = False
        self.frame_count = 0
        
    async def recv(self):
        """Receive and process audio frames"""
        # Check if we have a response to send first
        if not self.response_queue.empty():
            response_frame = await self.response_queue.get()
            logger.info("Sending queued audio response frame")
            return response_frame
        
        frame = await self.track.recv()
        
        # Send greeting after connection is stable (after ~50 frames / 1 second)
        self.frame_count += 1
        if not self.greeting_sent and self.frame_count > 50:
            self.greeting_sent = True
            logger.info("Sending greeting after connection stable")
            asyncio.create_task(self._send_greeting())
        
        # Convert frame to numpy array
        audio_data = frame.to_ndarray()
        
        # Log first few frames to verify audio reception
        if self.frame_count < 5:
            logger.info(f"Frame {self.frame_count}: shape={audio_data.shape}, dtype={audio_data.dtype}, sample_rate={frame.sample_rate}")
        
        # Accumulate audio buffer
        self.audio_buffer.append(audio_data)
        self.buffer_duration += frame.samples / frame.sample_rate
        
        # Calculate audio energy for statistics
        energy = np.sqrt(np.mean(audio_data.astype(float) ** 2))
        
        # Log energy periodically
        if self.frame_count % 100 == 0:
            logger.info(f"Audio energy at frame {self.frame_count}: {energy:.4f}")
        
        # Track voice statistics
        if energy > 0.01:  # Voice detected
            self.energy_samples.append(energy)
            self.voice_stats["speaking_duration"] += frame.samples / frame.sample_rate
        
        if energy < 0.01:  # Silence threshold
            self.silence_duration += frame.samples / frame.sample_rate
        else:
            self.silence_duration = 0.0
        
        # Process buffer when silence detected
        if (self.silence_duration >= self.silence_threshold and 
            self.buffer_duration >= 1.0 and 
            not self.processing):
            logger.info(f"Triggering audio processing: buffer_duration={self.buffer_duration:.2f}s, silence={self.silence_duration:.2f}s")
            asyncio.create_task(self._process_audio_buffer())
        
        # Return silence frame (don't echo user's voice back)
        silence = np.zeros_like(audio_data, dtype=audio_data.dtype)
        silent_frame = AudioFrame.from_ndarray(
            silence,
            format=frame.format.name,
            layout=frame.layout.name
        )
        silent_frame.sample_rate = frame.sample_rate
        return silent_frame
    
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
            
            # Update voice statistics
            self._update_voice_stats()
            self.voice_stats["num_utterances"] += 1
            
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
    
    def _update_voice_stats(self):
        """Update voice statistics from collected energy samples"""
        if self.energy_samples:
            self.voice_stats["volume_avg"] = float(np.mean(self.energy_samples))
            self.voice_stats["volume_max"] = float(np.max(self.energy_samples))
            
            # Calculate clarity score based on signal consistency
            if len(self.energy_samples) > 1:
                std_dev = np.std(self.energy_samples)
                mean = np.mean(self.energy_samples)
                # Normalize clarity: lower variation relative to mean = higher clarity
                self.voice_stats["clarity_score"] = min(100, max(0, 100 * (1 - std_dev / (mean + 0.001))))
            
            # Log statistics
            logger.info(f"Voice Stats - Volume: {self.voice_stats['volume_avg']:.4f}, "
                       f"Max: {self.voice_stats['volume_max']:.4f}, "
                       f"Clarity: {self.voice_stats['clarity_score']:.1f}%, "
                       f"Speaking Time: {self.voice_stats['speaking_duration']:.1f}s")
    
    async def _send_greeting(self):
        """Send initial greeting to user"""
        try:
            greeting_text = "Hello! Welcome to your AI interview. Please introduce yourself and tell me about your background."
            logger.info(f"Synthesizing greeting: {greeting_text}")
            
            # Synthesize greeting
            greeting_audio, greeting_sr = await self.tts.synthesize(greeting_text)
            logger.info(f"Greeting audio generated: {len(greeting_audio)} samples at {greeting_sr}Hz")
            
            if len(greeting_audio) == 0:
                logger.error("TTS returned empty audio!")
                return
            
            # Queue greeting audio
            await self._queue_audio_response(greeting_audio, greeting_sr)
            logger.info(f"Greeting audio queued: {self.response_queue.qsize()} frames in queue")
            
        except Exception as e:
            logger.error(f"Greeting error: {e}", exc_info=True)
    
    async def _queue_audio_response(self, audio_data: np.ndarray, sample_rate: int):
        """Queue audio response frames for transmission"""
        try:
            if len(audio_data) == 0:
                logger.warning("Received empty audio data, skipping")
                return
            
            logger.info(f"Queueing audio response: {len(audio_data)} samples at {sample_rate} Hz")
            
            # Audio data is already int16 from TTS
            audio_int16 = audio_data
            
            # Create chunks (20ms per frame)
            samples_per_frame = int(sample_rate * 0.02)
            frame_count = 0
            
            for i in range(0, len(audio_int16), samples_per_frame):
                chunk = audio_int16[i:i + samples_per_frame]
                
                # Pad last chunk if needed
                if len(chunk) < samples_per_frame:
                    chunk = np.pad(chunk, (0, samples_per_frame - len(chunk)), constant_values=0)
                
                # Reshape to (channels, samples) - mono audio
                chunk = chunk.reshape(1, -1)
                
                # Create audio frame
                frame = AudioFrame.from_ndarray(
                    chunk,
                    format='s16',
                    layout='mono'
                )
                frame.sample_rate = sample_rate
                frame.time_base = fractions.Fraction(1, sample_rate)
                
                # Queue frame
                await self.response_queue.put(frame)
                frame_count += 1
            
            logger.info(f"Queued {frame_count} audio frames for playback")
                
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
        self.audio_processors: Dict[str, AudioProcessor] = {}
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
                self.audio_processors[peer_id] = processor
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
    
    def get_voice_stats(self, peer_id: str) -> dict:
        """Get voice statistics for a peer"""
        if peer_id in self.audio_processors:
            return self.audio_processors[peer_id].voice_stats.copy()
        return {}
    
    async def close_peer_connection(self, peer_id: str):
        """Close and remove a peer connection"""
        if peer_id in self.peers:
            pc = self.peers[peer_id]
            await pc.close()
            del self.peers[peer_id]
            if peer_id in self.audio_processors:
                del self.audio_processors[peer_id]
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
