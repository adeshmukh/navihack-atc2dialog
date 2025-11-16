# Welcome to ATC Dialog Parser! ✈️🎙️

Transform Air Traffic Control audio communications into structured, readable dialog with intelligent parsing.

## How It Works

### 1. Identify Yourself
When you start a new chat session, you'll be prompted to identify your aircraft callsign (e.g., "Southwest 34", "United 123", "Delta 789").

### 2. Upload Audio
Upload an audio file (.mp3, .wav, .m4a) containing ATC communications. The system will:
- Transcribe the audio using OpenAI Whisper
- Parse the conversation into structured dialog
- Identify ATC and pilot messages
- **Highlight ATC messages directed at your specific callsign in bold**

### 3. Review Dialog
The parsed dialog will show:
- 🔵 **ATC**: Air Traffic Control communications
- 🟣 **PILOT**: Pilot communications
- 👤 **Who annotations**: Aircraft callsigns
- ⚡ **What annotations**: Key actions and instructions
- **Bold text**: ATC messages specifically directed at your callsign

## Features

- **Smart Parsing**: LLM-powered conversation analysis
- **Role Identification**: Automatic detection of ATC vs. Pilot messages
- **Personalized Highlighting**: See which ATC communications are meant for you
- **Semantic Annotations**: Key information highlighted with emojis
- **Raw Transcript Access**: Collapsible section with original transcription

## Tips

- Use clear, standard aviation callsigns when identifying yourself
- Upload high-quality audio for best transcription results
- The parser works best with standard aviation phraseology