# AI Interviewer Simulator 🎤

A real-time AI-powered interview simulator using WebRTC, speech recognition, and text-to-speech. Practice your interview skills with an AI that can hear you, understand your responses, and speak back naturally.

## Features

- 🎥 **Real-time WebRTC Communication**: Audio and video streaming between client and server
- 🗣️ **Speech-to-Text**: Uses Whisper (faster-whisper) for accurate transcription
- 🤖 **AI Responses**: OpenRouter API integration for intelligent interview questions
- 🔊 **Text-to-Speech**: Coqui TTS for natural-sounding AI voice responses
- 💬 **Conversation Context**: Maintains interview context for follow-up questions
- ⚡ **Async Processing**: Non-blocking audio pipeline (STT → LLM → TTS)

## Architecture

```
User (Browser) ←→ WebRTC ←→ FastAPI Server
                              ↓
                    ┌─────────┴─────────┐
                    │                   │
                  STT ──→ LLM ──→ TTS
              (Whisper) (OpenRouter) (Coqui)
```

## Project Structure

```
ai-interviewer/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── webrtc_handler.py    # WebRTC logic with aiortc
│   ├── stt.py               # Whisper transcription
│   ├── llm.py               # OpenRouter API integration
│   └── tts.py               # Coqui TTS synthesis
├── index.html               # WebRTC client interface
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- OpenRouter API key (get one at https://openrouter.ai/)
- Microphone and camera access in browser

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenRouter API key
# OPENROUTER_API_KEY=your_actual_api_key_here
```

### 4. Run the Application

```bash
# Option 1: Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Run the main module
python -m app.main
```

### 5. Access the Application

Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

1. **Start Interview**: Click "Start Interview" to begin the WebRTC connection
2. **Grant Permissions**: Allow camera and microphone access when prompted
3. **Speak**: The AI will greet you. Speak naturally into your microphone
4. **Listen**: The AI will respond with follow-up questions
5. **Reset**: Click "Reset Conversation" to start over
6. **Stop**: Click "Stop Interview" to end the session

## Configuration

Edit `.env` file to customize:

```env
# OpenRouter API
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-3.5-turbo  # or other models

# Server
HOST=0.0.0.0
PORT=8000

# Whisper STT
WHISPER_MODEL=base  # tiny, base, small, medium, large
WHISPER_DEVICE=cpu  # or cuda for GPU
WHISPER_COMPUTE_TYPE=int8  # int8, float16, float32

# Coqui TTS
TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
TTS_DEVICE=cpu  # or cuda for GPU

# Interview
INTERVIEWER_ROLE=professional technical interviewer
```

## API Endpoints

- `GET /` - Serve the web interface
- `GET /health` - Health check endpoint
- `POST /offer` - WebRTC offer/answer exchange
- `POST /reset/{peer_id}` - Reset conversation history
- `GET /conversation/{peer_id}` - Get conversation history
- `DELETE /peer/{peer_id}` - Close peer connection

## How It Works

1. **Client Side**:
   - Browser captures audio/video via `getUserMedia()`
   - Creates WebRTC peer connection
   - Sends SDP offer to server via `/offer` endpoint
   - Receives and plays AI audio responses

2. **Server Side**:
   - Accepts WebRTC offer and creates answer
   - Receives audio tracks from client
   - Buffers audio until silence detected
   - **STT Pipeline**: Transcribes audio using Whisper
   - **LLM Pipeline**: Sends transcription to OpenRouter
   - **TTS Pipeline**: Converts AI response to speech
   - Sends audio response back via WebRTC

3. **Processing Flow**:
   ```
   Mic Audio → Buffer → Whisper → Text
                                    ↓
                              OpenRouter LLM
                                    ↓
   WebRTC ← Audio Frames ← Coqui TTS ← AI Text
   ```

## Troubleshooting

### Import errors during runtime
Make sure to install all dependencies:
```bash
pip install -r requirements.txt
```

### WebRTC connection fails
- Check that you're using HTTPS or localhost
- Verify firewall settings
- Check browser console for errors

### No audio response
- Verify OpenRouter API key is valid
- Check server logs for errors
- Ensure TTS model is downloaded (happens on first run)

### Poor transcription quality
- Speak clearly and reduce background noise
- Try a larger Whisper model (e.g., "small" or "medium")
- Check microphone quality

### Slow response time
- Use GPU if available (set `WHISPER_DEVICE=cuda`, `TTS_DEVICE=cuda`)
- Use smaller models for faster processing
- Consider using `WHISPER_MODEL=tiny` for testing

## Performance Optimization

- **GPU Acceleration**: Set device to `cuda` for faster STT/TTS
- **Model Selection**: Balance quality vs speed:
  - Fast: `WHISPER_MODEL=tiny`, lightweight TTS
  - Balanced: `WHISPER_MODEL=base` (default)
  - Quality: `WHISPER_MODEL=medium` or `large`

## Development

To run in development mode with auto-reload:
```bash
uvicorn app.main:app --reload --log-level debug
```

## License

MIT License - feel free to use for your projects!

## Credits

- **FastAPI**: Modern Python web framework
- **aiortc**: WebRTC implementation for Python
- **Whisper**: OpenAI's speech recognition model
- **OpenRouter**: LLM API gateway
- **Coqui TTS**: Text-to-speech synthesis

## Future Enhancements

- [ ] Add conversation summary/feedback
- [ ] Support multiple interview types (technical, behavioral, etc.)
- [ ] Real-time transcription display
- [ ] Recording and playback features
- [ ] Multi-language support
- [ ] Emotion detection from voice
- [ ] Integration with resume parsing

---

**Note**: This is a learning/demo project. For production use, add proper authentication, rate limiting, and error handling.
