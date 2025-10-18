# 🔧 Troubleshooting Guide - AI Interviewer

## Common Issues & Solutions

### 1. Import Errors at Runtime

#### Symptom:
```
ModuleNotFoundError: No module named 'faster_whisper'
ImportError: No module named 'TTS'
```

#### Solution:
```bash
# Install all dependencies
pip install -r requirements.txt

# If still failing, upgrade pip first
pip install --upgrade pip
pip install -r requirements.txt

# For specific modules
pip install faster-whisper
pip install TTS
pip install aiortc
```

---

### 2. OpenRouter API Key Error

#### Symptom:
```
ValueError: OPENROUTER_API_KEY not set in environment
```

#### Solution:
```bash
# 1. Make sure .env file exists
cp .env.example .env

# 2. Edit .env and add your key
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE

# 3. Get a free key at:
https://openrouter.ai/

# 4. Restart the server
```

---

### 3. WebRTC Connection Fails

#### Symptom:
- "Connection failed" in browser
- Stuck on "Connecting..."
- No audio/video streams

#### Solutions:

**A. Use localhost (not 127.0.0.1)**
```
✅ http://localhost:8000
❌ http://127.0.0.1:8000
```

**B. Check browser permissions**
1. Click 🔒 icon in address bar
2. Allow Camera and Microphone
3. Reload page

**C. Try different browser**
- Chrome/Edge (Recommended) ✅
- Firefox ✅
- Safari ⚠️ (may have issues)

**D. Check firewall**
```bash
# Windows: Allow Python through firewall
# Linux: Check iptables
sudo ufw allow 8000
```

**E. HTTPS requirement**
For non-localhost domains, WebRTC requires HTTPS:
```bash
# Use localhost for testing
# For production, set up SSL certificate
```

---

### 4. No Audio Response from AI

#### Symptom:
- Can hear yourself (echo)
- AI text appears but no voice
- Connection established but silent

#### Solutions:

**A. Check server logs**
```bash
# Look for errors like:
# "TTS synthesis error"
# "LLM API error"
# "Audio processing error"
```

**B. Test TTS independently**
```bash
python test_setup.py
# Check if TTS test passes
```

**C. Verify API key works**
```bash
# Test OpenRouter API
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-3.5-turbo","messages":[{"role":"user","content":"test"}]}'
```

**D. Check audio output device**
- Unmute speakers
- Check volume levels
- Try different output device

**E. Wait longer**
First response may take 10-15s:
- Model loading
- Initial API call
- TTS synthesis

---

### 5. Poor Transcription Quality

#### Symptom:
- Incorrect words
- Missing speech
- Nonsense output

#### Solutions:

**A. Improve environment**
- Speak clearly and slowly
- Reduce background noise
- Use headset microphone
- Check mic levels

**B. Adjust silence threshold**
Edit `app/webrtc_handler.py`:
```python
self.silence_threshold = 3.0  # Increase from 2.0
```

**C. Use larger Whisper model**
Edit `.env`:
```env
WHISPER_MODEL=small  # or medium
```

**D. Check microphone**
```bash
# Test mic in browser
# Visit: chrome://settings/content/microphone
```

---

### 6. Slow Response Time

#### Symptom:
- 10+ second delays
- Laggy audio
- Server unresponsive

#### Solutions:

**A. Use faster models**
```env
WHISPER_MODEL=tiny
TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
```

**B. Enable GPU acceleration**
```env
WHISPER_DEVICE=cuda
TTS_DEVICE=cuda

# Requires NVIDIA GPU + CUDA
# Install: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**C. Close other applications**
- Free up CPU/RAM
- Stop background processes

**D. Reduce concurrent requests**
- Test with one user at a time
- Implement queuing for multiple users

---

### 7. First Run is Very Slow

#### Symptom:
- Initial startup takes 5+ minutes
- "Downloading models..." messages
- High network usage

#### Why:
Models are downloaded on first run:
- Whisper base: ~150 MB
- Coqui TTS: ~150 MB
- Total: ~2 GB with dependencies

#### Solution:
**Just wait!** This only happens once.

Progress:
```
Downloading whisper base model... ⏳
Downloading TTS model... ⏳
Models cached for future use ✅
```

---

### 8. Memory Issues / Crashes

#### Symptom:
```
MemoryError
Killed
Out of memory
```

#### Solutions:

**A. Use smaller models**
```env
WHISPER_MODEL=tiny  # Only ~1 GB RAM
```

**B. Increase system RAM**
- Minimum: 4 GB
- Recommended: 8 GB+
- With large models: 16 GB+

**C. Close other programs**
```bash
# Free up memory
# Close browsers, IDEs, etc.
```

**D. Use swap space (Linux)**
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

### 9. CORS Errors in Browser

#### Symptom:
```
Access to fetch at 'http://localhost:8000/offer' has been blocked by CORS policy
```

#### Solution:
CORS is already configured in `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change for production
)
```

If still occurring:
1. Clear browser cache
2. Restart server
3. Hard reload page (Ctrl+Shift+R)

---

### 10. Audio Echo / Feedback

#### Symptom:
- Hearing your own voice
- Feedback loop
- Screeching sound

#### Solutions:

**A. Use headphones**
- Prevents speaker output from entering mic

**B. Mute local video**
```javascript
// Already done in index.html
<video id="localVideo" muted></video>
```

**C. Enable echo cancellation**
```javascript
// Already enabled in index.html
audio: {
    echoCancellation: true,
    noiseSuppression: true
}
```

---

### 11. Server Won't Start

#### Symptom:
```
Address already in use
Port 8000 is in use
```

#### Solutions:

**A. Kill existing process**
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8000
kill -9 <PID>
```

**B. Use different port**
```bash
# Edit .env
PORT=8001

# Or run with custom port
uvicorn app.main:app --port 8001
```

---

### 12. Models Not Loading

#### Symptom:
```
Error loading model
Model file not found
```

#### Solutions:

**A. Clear cache and redownload**
```bash
# Remove cached models
rm -rf ~/.cache/whisper
rm -rf ~/.local/share/tts

# Restart server to redownload
```

**B. Manual download**
```python
# Run Python shell
python

# Download Whisper
from faster_whisper import WhisperModel
model = WhisperModel("base")

# Download TTS
from TTS.api import TTS
tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")
```

---

### 13. OpenRouter API Errors

#### Symptom:
```
401 Unauthorized
429 Too Many Requests
500 Internal Server Error
```

#### Solutions:

**A. Check API key**
- Verify key is correct in .env
- Check key hasn't expired
- Visit openrouter.ai to verify

**B. Check rate limits**
- Free tier has limits
- Wait and retry
- Upgrade plan if needed

**C. Check model availability**
```env
# Try different model
OPENROUTER_MODEL=anthropic/claude-instant-v1
```

---

### 14. Video Not Showing

#### Symptom:
- Audio works
- Video feed is black
- Camera light not on

#### Solutions:

**A. Grant camera permission**
```
1. Browser address bar 🔒
2. Allow Camera
3. Reload page
```

**B. Check camera usage**
- Close other apps using camera (Zoom, Teams, etc.)
- Only one app can use camera at once

**C. Try without video**
Edit `index.html`:
```javascript
getUserMedia({
    video: false,  // Disable video
    audio: true
})
```

---

### 15. Logs are Too Verbose

#### Symptom:
- Too many log messages
- Hard to read errors

#### Solutions:

**A. Change log level**
```bash
# Less verbose
uvicorn app.main:app --log-level warning

# More verbose (debugging)
uvicorn app.main:app --log-level debug
```

**B. Filter logs**
```bash
# Linux/Mac: Filter out info
uvicorn app.main:app 2>&1 | grep -v INFO

# Windows PowerShell:
uvicorn app.main:app 2>&1 | Select-String -Pattern "ERROR|WARNING"
```

---

## Diagnostic Commands

### Check Python Version
```bash
python --version
# Required: 3.9+
```

### Check Installed Packages
```bash
pip list | grep -E "fastapi|aiortc|whisper|TTS|openai"
```

### Test Components
```bash
python test_setup.py
```

### Check Server Status
```bash
curl http://localhost:8000/health
```

### View Server Logs
```bash
# Run with verbose logging
uvicorn app.main:app --log-level debug
```

---

## Still Having Issues?

### 1. Check the logs
```bash
# Server terminal output
# Browser console (F12)
```

### 2. Run diagnostics
```bash
python test_setup.py
```

### 3. Check documentation
```bash
# README.md - Full documentation
# QUICKSTART.md - Quick setup
# PROJECT_SUMMARY.md - Architecture
```

### 4. Clean reinstall
```bash
# Remove virtual environment
rm -rf venv

# Recreate
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 5. System requirements check
- Python 3.9+
- 4GB+ RAM (8GB recommended)
- 5GB free disk space
- Stable internet connection
- Modern browser (Chrome/Edge/Firefox)

---

## Quick Health Check

Run this checklist:

- [ ] Python 3.9+ installed
- [ ] All packages installed (`pip install -r requirements.txt`)
- [ ] `.env` file exists with API key
- [ ] Server starts without errors
- [ ] `http://localhost:8000/health` returns 200 OK
- [ ] Browser permissions granted (mic/camera)
- [ ] Headphones connected (prevents echo)
- [ ] Quiet environment (for better transcription)

---

**Most issues are solved by:**
1. Installing dependencies correctly
2. Adding OpenRouter API key to `.env`
3. Using headphones
4. Being patient on first run (model downloads)

Good luck! 🚀
