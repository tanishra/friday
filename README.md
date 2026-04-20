<div align="center">

  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,50:1d4ed8,100:312e81&height=220&section=header&text=Friday&fontSize=72&fontColor=FFFFFF&fontAlignY=40&desc=Real-time%20voice%20AI%20Agent&descAlignY=63&descColor=ffffff&descSize=18" width="100%"/>


  <br />

  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![LiveKit](https://img.shields.io/badge/LiveKit-00D1FF?style=for-the-badge&logo=livekit&logoColor=white)](https://livekit.io)
  [![Deepgram](https://img.shields.io/badge/Deepgram-13EF95?style=for-the-badge&logo=deepgram&logoColor=black)](https://deepgram.com)
  [![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)

  <br />

  ### Talk to Friday live at [tanish.website](https://tanish.website)
</div>

---

## Overview
Friday is a high-performance AI voice agent built to live on Tanish's portfolio. She doesn't just talk; she controls the UI, handles networking, and represents Tanish in real-time using a first-principles architecture.

## Architecture
```mermaid
graph TD
    User((Visitor)) <-->|Voice/Data| Portfolio[tanish.website]
    Portfolio <-->|Auth| API[Friday Token Server]
    Portfolio <-->|WebRTC| LiveKit[LiveKit Cloud]
    LiveKit <-->|Agent Loop| Friday[Friday Agent Worker]
    
    subgraph Friday Tools
        Friday -->|UI Control| UI[Remote Navigation]
        Friday -->|Messaging| Email[Resend API]
        Friday -->|Code| GH[GitHub API]
        Friday -->|Meetings| Cal[Google Calendar]
    end
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
python -c "from livekit.plugins import silero; silero.VAD.load()"
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
# LiveKit Cloud
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# AI Stack (Deepgram + GPT-4o)
DEEPGRAM_API_KEY=your_deepgram_api_key
OPENAI_API_KEY=your_openai_api_key

# Tools
RESEND_API_KEY=your_resend_api_key
SENDER_EMAIL=friday@yourdomain.com
YOUR_EMAIL=tanish@youremail.com
GITHUB_USERNAME=tanishra
```

### 3. Run Locally
```bash
python main.py
```

## Remote Control Integration
Friday can "drive" your portfolio. Listen for data packets on your frontend:

```javascript
room.on(RoomEvent.DataReceived, (payload) => {
  const data = JSON.parse(new TextDecoder().decode(payload));
  if (data.type === 'NAVIGATE') {
    document.getElementById(data.section)?.scrollIntoView({ behavior: 'smooth' });
  }
});
```

---

<div align="center">
  <b>Voice-first. Agent-led. From first principles.</b>
</div>
