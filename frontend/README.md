# Dental Interview Practice Application

A professional AI-powered interview practice application for dental professionals, featuring voice-based interactions and adaptive questioning.

## Features

- **Two Interview Tracks**: Separate practice modes for Dentist and Dental Hygienist positions
- **AI-Powered Questions**: Contextual questions generated using Claude AI (Anthropic)
- **Voice Interaction**: Audio questions using text-to-speech and voice recording for answers
- **Adaptive Flow**: 7 questions that adapt based on candidate responses
- **Professional Design**: Clean, trustworthy aesthetic appropriate for healthcare professionals
- **Progress Tracking**: Visual progress indicators throughout the interview

## Technology Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **UI Framework**: Tailwind CSS (via CDN)
- **Icons**: Lucide Icons
- **AI Service**: Anthropic Claude API
- **Text-to-Speech**: Browser Speech Synthesis API (with ElevenLabs integration ready)
- **Speech-to-Text**: Browser MediaRecorder API (with OpenAI Whisper integration ready)

## File Structure

```
dental-interview-app/
├── index.html          # Main HTML structure
├── styles.css          # Custom CSS styles and animations
├── app.js             # Application logic and state management
└── README.md          # This file
```

## Setup Instructions

### 1. Basic Setup (Demo Mode)

The application works out of the box using browser APIs for demo purposes:

1. Open `index.html` in a modern web browser
2. The app will use:
   - Browser Speech Synthesis API for question audio
   - Browser MediaRecorder for recording answers
   - Simulated transcriptions for demo purposes

### 2. Production Setup with Full APIs

To enable full AI-powered functionality, you'll need API keys from:

#### A. Anthropic API (Required for AI Questions)

1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Generate an API key
3. The API is called directly in the browser (consider using a backend proxy for security)

#### B. ElevenLabs API (Optional - for better voice quality)

1. Sign up at [elevenlabs.io](https://elevenlabs.io)
2. Get your API key
3. Update `CONFIG.ELEVENLABS_API_KEY` in `app.js`
4. Uncomment the production ElevenLabs code in `generateAudioForQuestion()` function

#### C. OpenAI Whisper API (Optional - for better transcription)

1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Get your API key
3. Uncomment the production Whisper code in `transcribeAudio()` function

### 3. Security Considerations

**IMPORTANT**: Never expose API keys in client-side code in production!

For production deployment:
- Create a backend server (Node.js, Python, etc.)
- Store API keys securely on the server
- Proxy API requests through your backend
- Implement rate limiting and authentication

Example backend proxy structure:
```
POST /api/generate-question
POST /api/generate-audio
POST /api/transcribe-audio
```

### 4. Browser Requirements

- Modern browser with:
  - ES6+ JavaScript support
  - MediaRecorder API support
  - Speech Synthesis API support (for demo mode)
  - Microphone permissions

Recommended browsers:
- Chrome 80+
- Firefox 75+
- Safari 14+
- Edge 80+

## Configuration

### API Configuration (app.js)

```javascript
const CONFIG = {
    TOTAL_QUESTIONS: 7,
    ANTHROPIC_API_URL: 'https://api.anthropic.com/v1/messages',
    ELEVENLABS_API_URL: 'https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM',
    ELEVENLABS_API_KEY: 'YOUR_API_KEY_HERE'
};
```

### System Prompts

Interview questions are guided by role-specific system prompts in `app.js`:

- **Dentist**: Clinical expertise, patient management, practice leadership
- **Hygienist**: Preventive care, patient education, clinical procedures

You can customize these prompts to match your specific interview requirements.

## Usage Guide

### For Candidates

1. **Select Interview Type**: Choose between Dentist or Dental Hygienist
2. **Enter Information**: Provide your name and email
3. **Start Practice**: Click "Start Interview" to begin
4. **Listen to Questions**: Each question will be read aloud automatically
5. **Record Answers**: Click the microphone button to record your response
6. **Complete Interview**: Answer all 7 questions to finish

### For Administrators

To customize interview questions:
1. Edit system prompts in `SYSTEM_PROMPTS` object in `app.js`
2. Adjust `CONFIG.TOTAL_QUESTIONS` to change interview length
3. Modify the UI text in `index.html` for branding

## Customization

### Styling

The application uses:
- **Primary Color**: Indigo/Blue gradient
- **Fonts**: Playfair Display (headings), Crimson Text (body)
- **Theme**: Professional, trustworthy, healthcare-appropriate

To customize:
- Edit CSS variables in `styles.css`
- Modify Tailwind classes in `index.html`
- Update gradient colors throughout

### Interview Flow

To modify the interview structure:
1. Change `CONFIG.TOTAL_QUESTIONS` in `app.js`
2. Update progress bar in `index.html` (add/remove progress segments)
3. Modify question generation logic in `generateQuestionWithAI()`

## API Integration Details

### Anthropic Claude API

Request format:
```javascript
{
    model: "claude-sonnet-4-20250514",
    max_tokens: 1000,
    system: "System prompt here...",
    messages: [
        { role: "user", content: "User message" },
        { role: "assistant", content: "AI response" }
    ]
}
```

### ElevenLabs TTS API

Request format:
```javascript
{
    text: "Text to convert to speech",
    model_id: "eleven_monolingual_v1",
    voice_settings: {
        stability: 0.5,
        similarity_boost: 0.5
    }
}
```

### OpenAI Whisper API

Request format:
```javascript
FormData {
    file: audioBlob,
    model: 'whisper-1'
}
```

## Troubleshooting

### Microphone Access Denied
- Check browser permissions
- Ensure HTTPS is used (required for getUserMedia)
- Try a different browser

### Audio Not Playing
- Check browser audio permissions
- Verify speakers/headphones are connected
- Check browser console for errors

### API Errors
- Verify API keys are correct
- Check API rate limits
- Ensure network connectivity
- Review browser console for detailed error messages

### Speech Synthesis Not Working
- Some browsers require user interaction before playing audio
- Check if browser supports Speech Synthesis API
- Try clicking on the page before starting

## Performance Optimization

- Questions are generated sequentially to manage API costs
- Audio is generated on-demand
- Conversation history is maintained in memory only
- No persistent storage used (sessions don't persist across page reloads)

## Privacy & Data

- User information (name, email) is stored only in browser memory
- No data is persisted to local storage or sent to external servers (except API calls)
- Audio recordings are temporary and deleted after transcription
- Conversation history is cleared when interview ends

## Future Enhancements

Potential improvements:
- Backend server for secure API key management
- Results summary and feedback at end of interview
- Export interview transcript as PDF
- Multi-language support
- Video recording option
- Admin dashboard for reviewing sessions
- Database integration for storing practice sessions
- Analytics and performance tracking

## License

This is a demonstration project. Modify as needed for your use case.

## Support

For issues or questions:
1. Check browser console for error messages
2. Verify API credentials and quotas
3. Ensure browser compatibility
4. Review this README for configuration details

## Credits

- **AI**: Anthropic Claude
- **Icons**: Lucide Icons
- **Fonts**: Google Fonts (Playfair Display, Crimson Text)
- **CSS Framework**: Tailwind CSS
