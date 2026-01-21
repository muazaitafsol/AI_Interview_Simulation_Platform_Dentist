# Dental Interview Practice - Backend API

FastAPI backend for AI-powered dental interview practice application with OpenAI GPT-4 Mini, Whisper, and ElevenLabs integration.

## Features

- **AI Question Generation**: Uses OpenAI GPT-4 Mini (gpt-4o-mini) to generate contextual interview questions
- **Category-Based Flow**: 7 questions across predefined categories
- **Text-to-Speech**: ElevenLabs API for high-quality audio generation
- **Speech-to-Text**: OpenAI Whisper for accurate transcription
- **Conversation History**: Maintains context for adaptive questioning
- **Two Interview Types**: Separate prompts for Dentist and Dental Hygienist interviews

## Interview Categories

Questions are generated in the following order:

1. **Introduction** - Getting to know the candidate
2. **Clinical Judgement** - Assessing decision-making in clinical scenarios
3. **Ethics, Consent & Communication** - Evaluating ethical reasoning and communication skills
4. **Productivity & Efficiency** - Understanding time management and efficiency
5. **Mentorship & Independence** - Exploring leadership and autonomous working
6. **Fit & Professional Maturity** - Determining cultural fit and professional development
7. **Insight & Authenticity** - Gauging self-awareness and genuine responses

## Technology Stack

- **Framework**: FastAPI
- **AI Models**:
  - OpenAI GPT-4 Mini (gpt-4o-mini) for question generation
  - OpenAI Whisper (whisper-1) for speech-to-text
- **TTS**: ElevenLabs API
- **Python**: 3.9+

## Project Structure

```
backend/
├── main.py                 # Main FastAPI application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .env                   # Your environment variables (create this)
└── README.md              # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- pip package manager
- API keys for:
  - OpenAI (for GPT-4 Mini and Whisper)
  - ElevenLabs (for text-to-speech)

### 2. Installation

```bash
# Clone or navigate to the backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

#### Getting API Keys

**OpenAI API Key:**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Add billing information (required for API access)

**ElevenLabs API Key:**
1. Go to [elevenlabs.io](https://elevenlabs.io)
2. Sign up or log in
3. Navigate to your profile settings
4. Find or create an API key
5. (Optional) Browse voices and update ELEVENLABS_VOICE_ID

### 4. Running the Server

```bash
# Development mode (with auto-reload)
uvicorn main:app --reload --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Start Interview

**POST** `/api/interview/start`

Start a new interview and get the first question with greeting.

**Request Body:**
```json
{
  "interview_type": "dentist",
  "user_name": "John Smith",
  "user_email": "john@example.com"
}
```

**Response:**
```json
{
  "question": "Hello John Smith! Thank you for taking the time to speak with us today. To start, could you tell me a bit about your background and what drew you to dentistry?",
  "category": "Introduction",
  "question_number": 1
}
```

### 2. Generate Question

**POST** `/api/interview/question`

Generate the next question based on conversation history.

**Request Body:**
```json
{
  "interview_type": "dentist",
  "conversation_history": [
    {
      "role": "assistant",
      "content": "Hello John! Tell me about your background."
    },
    {
      "role": "user",
      "content": "I graduated from dental school in 2020..."
    }
  ],
  "question_number": 2,
  "user_name": "John Smith"
}
```

**Response:**
```json
{
  "question": "That's great experience. Now, let me ask you about a clinical scenario...",
  "category": "Clinical Judgement",
  "question_number": 2
}
```

### 3. Generate Audio

**POST** `/api/audio/generate`

Convert text to speech using ElevenLabs.

**Query Parameter:**
- `text`: The text to convert to speech

**Response:**
```json
{
  "audio_base64": "base64_encoded_audio_data",
  "content_type": "audio/mpeg"
}
```

### 4. Transcribe Audio

**POST** `/api/audio/transcribe`

Transcribe audio to text using OpenAI Whisper.

**Request:** Form data with audio file

**Response:**
```json
{
  "transcription": "I graduated from dental school in 2020 and have been practicing for 4 years...",
  "success": true
}
```

### 5. Get Categories

**GET** `/api/categories`

Get list of interview categories.

**Response:**
```json
{
  "categories": [
    "Introduction",
    "Clinical Judgement",
    "Ethics, Consent & Communication",
    "Productivity & Efficiency",
    "Mentorship & Independence",
    "Fit & Professional Maturity",
    "Insight & Authenticity"
  ],
  "total": 7
}
```

### 6. Get Interview Types

**GET** `/api/interview-types`

Get available interview types and descriptions.

**Response:**
```json
{
  "types": ["dentist", "hygienist"],
  "descriptions": {
    "dentist": "Interview practice for dentist positions...",
    "hygienist": "Interview practice for dental hygienist positions..."
  }
}
```

## Conversation History Format

The conversation history is maintained as a list of message objects:

```python
[
    {
        "role": "assistant",
        "content": "First question here"
    },
    {
        "role": "user",
        "content": "User's answer here"
    },
    {
        "role": "assistant",
        "content": "Follow-up question here"
    },
    {
        "role": "user",
        "content": "User's second answer"
    }
]
```

This format:
- Allows the AI to understand the full context
- Enables acknowledgment of previous answers
- Supports adaptive question generation
- Maintains conversation flow

## System Prompts

The backend uses specialized system prompts for each interview type:

### Dentist Interview
Focuses on:
- Clinical expertise and decision-making
- Patient care philosophy
- Practice management
- Professional development
- Leadership capabilities

### Dental Hygienist Interview
Focuses on:
- Preventive care knowledge
- Patient education skills
- Clinical procedures
- Teamwork and collaboration
- Professional growth

Both prompts ensure questions:
- Follow the 7-category structure
- Acknowledge previous responses
- Remain conversational and professional
- Are role-appropriate

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid input (e.g., question number out of range)
- **500 Internal Server Error**: API failures or processing errors

All errors return JSON with details:
```json
{
  "detail": "Error description here"
}
```

## Testing the API

### Using the Interactive Docs

1. Navigate to http://localhost:8000/docs
2. Expand any endpoint
3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"

### Using cURL

```bash
# Start interview
curl -X POST "http://localhost:8000/api/interview/start" \
  -H "Content-Type: application/json" \
  -d '{
    "interview_type": "dentist",
    "user_name": "John Smith",
    "user_email": "john@example.com"
  }'

# Generate audio
curl -X POST "http://localhost:8000/api/audio/generate?text=Hello%20world" \
  -H "Content-Type: application/json"

# Transcribe audio
curl -X POST "http://localhost:8000/api/audio/transcribe" \
  -F "file=@audio.wav"
```

### Using Python

```python
import requests

# Start interview
response = requests.post(
    "http://localhost:8000/api/interview/start",
    json={
        "interview_type": "dentist",
        "user_name": "John Smith",
        "user_email": "john@example.com"
    }
)
print(response.json())
```

## Frontend Integration

Update your frontend JavaScript to use the backend API:

```javascript
// Example: Start interview
const response = await fetch('http://localhost:8000/api/interview/start', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    interview_type: 'dentist',
    user_name: 'John Smith',
    user_email: 'john@example.com'
  })
});

const data = await response.json();
console.log(data.question);
```

## Performance Considerations

- **Response Time**: GPT-4 Mini typically responds in 1-3 seconds
- **Audio Generation**: ElevenLabs usually takes 2-5 seconds
- **Transcription**: Whisper processes audio in 1-2 seconds
- **Caching**: Consider implementing Redis for repeated questions
- **Rate Limiting**: Add rate limiting for production use

## Security Best Practices

1. **API Keys**: Never commit `.env` file to version control
2. **CORS**: Update allowed origins in production
3. **Rate Limiting**: Implement request rate limiting
4. **Authentication**: Add user authentication for production
5. **Input Validation**: All inputs are validated via Pydantic models
6. **HTTPS**: Use HTTPS in production
7. **Environment**: Use environment-specific configurations

## Deployment

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t dental-interview-api .
docker run -p 8000:8000 --env-file .env dental-interview-api
```

### Using Cloud Services

**Heroku:**
```bash
heroku create dental-interview-api
git push heroku main
heroku config:set OPENAI_API_KEY=your_key
heroku config:set ELEVENLABS_API_KEY=your_key
```

**AWS/Azure/GCP:**
- Deploy using their container services
- Set environment variables in the service configuration
- Configure auto-scaling based on traffic

## Monitoring & Logging

The application uses Python's logging module:

```python
# Logs include:
# - Interview starts
# - Question generation
# - Audio generation
# - Transcription requests
# - Errors and exceptions
```

View logs:
```bash
# Development
# Logs appear in terminal

# Production with systemd
journalctl -u dental-interview-api -f
```

## Troubleshooting

### OpenAI API Errors

```
Error: Incorrect API key provided
Solution: Verify OPENAI_API_KEY in .env file
```

```
Error: Rate limit exceeded
Solution: Wait or upgrade your OpenAI plan
```

### ElevenLabs API Errors

```
Error: Unauthorized
Solution: Check ELEVENLABS_API_KEY
```

```
Error: Voice not found
Solution: Verify ELEVENLABS_VOICE_ID or use default
```

### Audio Upload Issues

```
Error: File too large
Solution: Check file size limits (usually 25MB for Whisper)
```

## Cost Estimation

**Per Interview (7 questions):**
- GPT-4 Mini: ~$0.01-0.02
- Whisper: ~$0.01-0.02  
- ElevenLabs: ~$0.05-0.10

**Total per interview: ~$0.07-0.14**

## Support & Contributing

For issues or questions:
1. Check the logs for detailed error messages
2. Verify API keys and quotas
3. Review the interactive docs at `/docs`
4. Ensure all dependencies are installed

## License

This is a demonstration project for educational purposes.

## Changelog

**v1.0.0** - Initial release
- GPT-4 Mini integration
- Category-based question flow
- ElevenLabs TTS
- Whisper STT
- Two interview types
