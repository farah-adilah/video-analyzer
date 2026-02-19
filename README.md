# 🎥 Video AI Analyzer

A local desktop application for analyzing short video files using AI. Extract transcriptions, generate visual descriptions, and create professional reports - all without sending data to the cloud.

![Video AI Analyzer](https://img.shields.io/badge/AI-Local-green) ![Python](https://img.shields.io/badge/Python-3.10-blue) ![Tauri](https://img.shields.io/badge/Tauri-Desktop-orange)

## Features

- **Speech-to-Text Transcription** - Powered by OpenAI Whisper
- **Visual Analysis** - AI-powered scene understanding using BLIP
- **AI Summarization** - Intelligent video summaries using local LLMs
- **Report Generation** - Export to PDF or PowerPoint
- **Analysis History** - Automatically saves all analysis results

## Architecture
```
┌─────────────────────────────────────────────────┐
│           Frontend (React + Tauri)              │
│         Desktop UI & File Management            │
└─────────────────┬───────────────────────────────┘
                  │ gRPC
┌─────────────────▼───────────────────────────────┐
│         Backend (Python + gRPC)                 │
│              Orchestrator                       │
└─────────────────┬───────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
┌──────────┐ ┌─────────┐ ┌──────────────┐
│Transcribe│ │ Vision  │ │Summarization │
│  Agent   │ │ Agent   │ │    Agent     │
└────┬─────┘ └────┬────┘ └──────┬───────┘
     │            │              │
     ▼            ▼              ▼
┌──────────┐ ┌─────────┐ ┌──────────────┐
│ Whisper  │ │  BLIP   │ │  TinyLlama   │
│   MCP    │ │  MCP    │ │     MCP      │
└──────────┘ └─────────┘ └──────────────┘
```

## Prerequisites

- **Python 3.10 or higher**
- **Node.js 18+**
- **Rust & Cargo** (for Tauri)
- **ffmpeg** (for audio extraction)
- **4GB+ RAM** (8GB recommended for AI models)
- **5GB free disk space** (for AI models)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/video-ai-analyzer.git
cd video-ai-analyzer
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install Python dependencies
cd backend
pip install -r requirements.txt
```

### 3. Install ffmpeg

**Windows:**
- Download from https://ffmpeg.org/download.html
- Add to PATH or place `ffmpeg.exe` in `backend/` folder

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Install Tauri CLI
npm install --save-dev @tauri-apps/cli
```

### 5. Generate gRPC Protocol Files
```bash
cd backend
python -m grpc_tools.protoc -I./grpc_service/proto --python_out=./grpc_service --grpc_python_out=./grpc_service ./grpc_service/proto/video_analyzer.proto
```

## Usage

### Development Mode

**Terminal 1 - Start Backend (gRPC Server):**
```bash
cd backend
python grpc_service/server.py
```

**Terminal 2 - Start Frontend (Vite):**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Start Desktop App (Tauri):**
```bash
cd frontend
npx tauri dev
```

### Using the Application

1. **Upload Video** - Click the upload button and select an MP4 file
2. **Wait for Analysis** - Progress indicators show transcription, vision analysis, and summarization
3. **View Results** - Analysis results appear in the chat interface
4. **Generate Report** - Choose PDF or PowerPoint format and download

## Project Structure
```
video-ai-analyzer/
├── backend/
│   ├── agents/                 # AI coordination agents
│   │   ├── transcription_agent.py
│   │   ├── vision_agent.py
│   │   ├── summarization_agent.py
│   │   └── generation_agent.py
│   ├── mcp_servers/           # Model Context Protocol servers
│   │   ├── transcription_server/
│   │   ├── vision_server/
│   │   └── generation_server/
│   ├── orchestrator/          # Workflow coordination
│   │   └── workflow.py
│   ├── grpc_service/          # gRPC API
│   │   ├── proto/
│   │   └── server.py
│   ├── utils/                 # Utilities
│   │   └── video_processor.py
│   ├── storage/               # Analysis results (auto-generated)
│   ├── output/                # Generated reports (auto-generated)
│   ├── storage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API clients
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── src-tauri/            # Rust backend for desktop
│   │   ├── src/
│   │   │   └── main.rs
│   │   └── tauri.conf.json
│   └── package.json
└── README.md
```

## 🔧 Configuration

### Model Selection

Edit `backend/agents/summarization_agent.py` to change the summarization model:
```python
# Options:
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Fast, small
model_name = "microsoft/Phi-3-mini-4k-instruct"    # Better quality
```
```
```

### ffmpeg Not Found
```bash
# Test if ffmpeg is installed
ffmpeg -version

# If not found, add to PATH or place in backend/ folder
```

```

## Performance Tips

- **CPU Usage:** Models run on CPU by default. For faster inference, use a GPU if available
- **Video Length:** Optimal for videos under 60 seconds. Longer videos take proportionally more time
- **First Analysis:** Slower due to model loading (~30 seconds). Subsequent analyses are much faster

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [Salesforce BLIP](https://github.com/salesforce/BLIP) - Image understanding
- [TinyLlama](https://github.com/jzhang38/TinyLlama) - Text generation
- [Tauri](https://tauri.app/) - Desktop framework
- [gRPC](https://grpc.io/) - RPC framework
