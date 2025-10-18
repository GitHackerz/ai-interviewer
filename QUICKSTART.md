# Quick Start Guide - AI Interviewer

## 🚀 Fast Setup (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure API Key
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenRouter API key
# Get one free at: https://openrouter.ai/
```

**Edit `.env` file:**
```env
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
```

### Step 3: Test Setup (Optional)
```bash
python test_setup.py
```

### Step 4: Run the Application
```bash
# Option A: Quick start script
./start.sh          # Linux/Mac
start.bat           # Windows

# Option B: Direct uvicorn
uvicorn app.main:app --reload
```

### Step 5: Open in Browser
```
http://localhost:8000
```

---

## 🎯 Usage Flow

1. **Click "Start Interview"**
   - Allow camera/microphone permissions
   - Wait for "Connected" status

2. **Speak naturally**
   - The AI will greet you first
   - Answer questions clearly
   - Wait for AI responses

3. **Control the session**
   - "Reset Conversation" - Start fresh
   - "Stop Interview" - End session

---

## ⚙️ Configuration Presets

### For Testing (Fast)
```env
WHISPER_MODEL=tiny
TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
WHISPER_DEVICE=cpu
TTS_DEVICE=cpu
```

### For Quality (Slow)
```env
WHISPER_MODEL=medium
TTS_MODEL=tts_models/en/vctk/vits
WHISPER_DEVICE=cuda  # Requires GPU
TTS_DEVICE=cuda      # Requires GPU
```

### Balanced (Default)
```env
WHISPER_MODEL=base
TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
WHISPER_DEVICE=cpu
TTS_DEVICE=cpu
```

---

## 🐛 Common Issues

### "Import could not be resolved" errors
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### "OPENROUTER_API_KEY not set"
**Solution:** Add API key to `.env` file
```env
OPENROUTER_API_KEY=your_key_here
```

### WebRTC connection fails
**Solutions:**
- Use `http://localhost:8000` (not 127.0.0.1)
- Check browser permissions for mic/camera
- Try different browser (Chrome/Edge recommended)

### No audio response
**Solutions:**
- Check server logs for errors
- Verify API key is valid
- Wait for models to download (first run)

### Slow response time
**Solutions:**
- Use GPU: Set `WHISPER_DEVICE=cuda` and `TTS_DEVICE=cuda`
- Use smaller model: Set `WHISPER_MODEL=tiny`
- Close other applications

---

## 📊 Model Options

### Whisper Models (Speed vs Accuracy)
| Model | Speed | Quality | Memory |
|-------|-------|---------|--------|
| tiny | ⚡⚡⚡⚡⚡ | ⭐⭐ | ~1 GB |
| base | ⚡⚡⚡⚡ | ⭐⭐⭐ | ~1 GB |
| small | ⚡⚡⚡ | ⭐⭐⭐⭐ | ~2 GB |
| medium | ⚡⚡ | ⭐⭐⭐⭐⭐ | ~5 GB |
| large | ⚡ | ⭐⭐⭐⭐⭐ | ~10 GB |

### LLM Models (via OpenRouter)
| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| openai/gpt-3.5-turbo | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | $ |
| openai/gpt-4 | ⚡⚡ | ⭐⭐⭐⭐⭐ | $$$ |
| anthropic/claude-2 | ⚡⚡⭐ | ⭐⭐⭐⭐⭐ | $$ |
| meta-llama/llama-2-70b | ⚡⚡⚡ | ⭐⭐⭐⭐ | $ |

Change in `.env`:
```env
OPENROUTER_MODEL=openai/gpt-4
```

---

## 🔧 Advanced Configuration

### Custom Interview Personality
Edit `.env`:
```env
INTERVIEWER_ROLE=friendly HR recruiter specializing in software engineering
```

### Audio Processing Tuning
Edit `app/webrtc_handler.py`:
```python
self.silence_threshold = 2.0  # seconds before processing
self.sample_rate = 16000      # audio quality
```

### Enable Debug Logging
```bash
uvicorn app.main:app --reload --log-level debug
```

---

## 📚 API Reference

### Endpoints
- `GET /` - Web interface
- `GET /health` - Server status
- `POST /offer` - WebRTC handshake
- `POST /reset/{peer_id}` - Reset conversation
- `GET /conversation/{peer_id}` - Get chat history
- `DELETE /peer/{peer_id}` - Close connection

### Example API Call
```bash
# Check server health
curl http://localhost:8000/health

# Reset conversation
curl -X POST http://localhost:8000/reset/peer-123
```

---

## 🎓 Interview Types

### Technical Interview (Default)
```env
INTERVIEWER_ROLE=professional technical interviewer
```

### Behavioral Interview
```env
INTERVIEWER_ROLE=behavioral interviewer focusing on soft skills and past experiences
```

### System Design Interview
```env
INTERVIEWER_ROLE=senior engineer conducting system design interviews
```

---

## 💡 Tips for Best Results

1. **Speak clearly** - Enunciate words, avoid mumbling
2. **Use headphones** - Prevents audio feedback
3. **Quiet environment** - Reduces background noise
4. **Natural pauses** - Wait 2-3 seconds after speaking
5. **Good lighting** - For video (optional)

---

## 🔐 Security Notes

⚠️ **For Development Only**

For production deployment:
- Add authentication
- Use HTTPS/WSS
- Implement rate limiting
- Validate all inputs
- Use environment-specific configs
- Monitor API usage

---

## 📞 Support

Issues? Check:
1. Server logs in terminal
2. Browser console (F12)
3. `test_setup.py` output
4. README.md for detailed docs

---

**Happy Interviewing! 🚀**
