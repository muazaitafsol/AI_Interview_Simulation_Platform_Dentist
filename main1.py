"""
Dental Interview Practice - Backend API
FastAPI application for AI-powered dental interview practice
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Literal
import openai
import requests
import os
from dotenv import load_dotenv
import logging
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Dental Interview Practice API",
    description="AI-powered interview practice for dental professionals",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files FIRST (before defining routes)
# This serves CSS, JS, and other static files
current_dir = os.path.dirname(os.path.abspath(__file__))

possible_frontend_dirs = [
    os.path.join(current_dir, "..", "frontend"),  # ../frontend (if main.py in backend/)
    os.path.join(current_dir, "frontend"),         # frontend/ (if main.py in files/)
    current_dir,                                   # same directory as main.py
]

frontend_dir = None
for dir_path in possible_frontend_dirs:
    logger.info(f"Checking for static files in: {dir_path} - Exists: {os.path.exists(dir_path)}")
    if os.path.exists(dir_path):
        # Check if it actually has frontend files
        test_files = ["index.html", "styles.css"]
        if any(os.path.exists(os.path.join(dir_path, f)) for f in test_files):
            frontend_dir = dir_path
            break

if frontend_dir:
    try:
        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
        logger.info(f"✅ Serving static files from: {frontend_dir}")
    except Exception as e:
        logger.error(f"❌ Error mounting static files: {e}")
else:
    logger.warning(f"⚠️ Frontend directory not found. Checked: {possible_frontend_dirs}")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

# Interview categories in order
INTERVIEW_CATEGORIES = [
    "Introduction",
    "Clinical Judgement",
    "Technical Knowledge - Clinical Procedures",
    "Ethics, Consent & Communication",
    "Productivity & Efficiency",
    "Technical Knowledge - Advanced Applications",
    "Mentorship & Independence",
    "Technical Knowledge - Diagnosis & Treatment Planning",
    "Fit & Professional Maturity",
    "Insight & Authenticity"
]

# System prompts for different interview types
SYSTEM_PROMPTS = {
    "dentist": """You are an experienced dental practice manager conducting a professional interview for a dentist position. 

Your role is to ask thoughtful, relevant questions across ten specific categories in order:
1. Introduction - Getting to know the candidate
2. Clinical Judgement - Assessing decision-making in clinical scenarios
3. Technical Knowledge - Clinical Procedures
4. Ethics, Consent & Communication
5. Productivity & Efficiency
6. Technical Knowledge - Diagnosis & Treatment Planning
7. Mentorship & Independence
8. Technical Knowledge - Advanced Applications
9. Fit & Professional Maturity
10. Insight & Authenticity

QUESTION GENERATION APPROACH:
- For each category, generate UNIQUE, VARIED questions that assess the core competency
- DO NOT rely on repetitive question patterns like "tell me about a time..."
- MIX question styles: scenarios, technical how-to's, ethical dilemmas, hypotheticals, direct inquiries
- Be creative and unpredictable while staying relevant to the category
- Ensure questions feel natural, not templated

CATEGORY GUIDANCE (use as inspiration, not rigid templates):

Introduction: Ask about their journey, interests, practice preferences, career goals, recent learning
Clinical Judgement: Present real scenarios, ask about decision-making, handling disagreements, triage, adapting plans
Technical Knowledge - Clinical Procedures: Ask step-by-step techniques, tool preferences, complication management, procedural approaches
Ethics & Communication: Present ethical dilemmas, consent issues, patient conflicts, team dynamics
Productivity & Efficiency: Discuss time management, scheduling challenges, quality vs. speed balance
Technical Knowledge - Diagnosis & Treatment Planning: Case prioritization, interpreting findings, treatment sequencing
Mentorship & Independence: Teaching others, learning independently, asking for help, balancing autonomy
Technical Knowledge - Advanced Applications: Digital tools, CBCT, implants, CAD/CAM, lasers, new technologies
Fit & Professional Maturity: Handling mistakes, conflicts, growth goals, challenges, stress management
Insight & Authenticity: Self-awareness, accepting feedback, honest career reflections, areas of growth

Guidelines:
- Ask ONE question at a time
- ALWAYS acknowledge the candidate's previous answer briefly before the next question
- If the answer was weak or off-topic, provide brief constructive feedback
- Keep questions conversational yet professionally rigorous
- Do not mention category names in your questions
- Maintain a supportive tone with honest feedback
- VARY your question structures - avoid predictable patterns""",

    "hygienist": """You are an experienced dental practice manager conducting a professional interview for a dental hygienist position.

Your role is to ask thoughtful, relevant questions across ten specific categories in order:
1. Introduction - Getting to know the candidate
2. Clinical Judgement - Assessing decision-making in clinical scenarios
3. Technical Knowledge - Clinical Procedures
4. Ethics, Consent & Communication
5. Productivity & Efficiency
6. Technical Knowledge - Diagnosis & Treatment Planning
7. Mentorship & Independence
8. Technical Knowledge - Advanced Applications
9. Fit & Professional Maturity
10. Insight & Authenticity

QUESTION GENERATION APPROACH:
- For each category, generate UNIQUE, VARIED questions that assess the core competency
- DO NOT rely on repetitive question patterns like "tell me about a time..."
- MIX question styles: scenarios, technical how-to's, ethical dilemmas, hypotheticals, direct inquiries
- Be creative and unpredictable while staying relevant to the category
- Ensure questions feel natural, not templated

CATEGORY GUIDANCE (use as inspiration, not rigid templates):

Introduction: Ask about their path to hygiene, practice preferences, patient care philosophy, role expectations
Clinical Judgement: Present patient scenarios (cancer signs, heavy calculus, diabetes, pediatric challenges), assessment protocols
Technical Knowledge - Clinical Procedures: Instrument selection, SRP techniques, polishing, sensitivity management, scaling approaches
Ethics & Communication: Refusal of care, patient motivation, mandated reporting, competency questions, confidentiality
Productivity & Efficiency: Time management, room setup, heavy schedules, patient flow, prioritization
Technical Knowledge - Diagnosis & Treatment Planning: Periodontal classification, recession documentation, pocket assessment, cancer screening
Mentorship & Independence: Training others, working autonomously, disagreeing with dentists, self-directed learning
Technical Knowledge - Advanced Applications: Piezoelectric scalers, lasers, digital radiography, desensitizing treatments, air polishing
Fit & Professional Maturity: Handling mistakes, team conflicts, career development, challenges, maintaining enthusiasm
Insight & Authenticity: Areas for improvement, valuable feedback, honest career moves, training gaps, weaknesses

Guidelines:
- Ask ONE question at a time
- ALWAYS acknowledge the candidate's previous answer briefly before the next question
- If the answer was weak or off-topic, provide brief constructive feedback
- Keep questions conversational yet professionally rigorous
- Do not mention category names in your questions
- Maintain a supportive tone with honest feedback
- VARY your question structures - avoid predictable patterns"""
}

# Pydantic Models
class InterviewStartRequest(BaseModel):
    interview_type: Literal["dentist", "hygienist"]
    user_name: str
    user_email: EmailStr

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class QuestionRequest(BaseModel):
    interview_type: Literal["dentist", "hygienist"]
    conversation_history: List[Message]
    question_number: int
    user_name: str

class QuestionResponse(BaseModel):
    question: str
    category: str
    question_number: int

class QuestionWithAudioResponse(BaseModel):
    question: str
    category: str
    question_number: int
    audio_base64: str = None

class AudioResponse(BaseModel):
    audio_url: str
    audio_base64: str = None

class InterviewEvaluationRequest(BaseModel):
    interview_type: Literal["dentist", "hygienist"]
    conversation_history: List[Message]
    user_name: str

class InterviewEvaluationResponse(BaseModel):
    overall_score: float
    category_scores: Dict[str, float]
    strengths: List[str]
    areas_for_improvement: List[str]
    detailed_feedback: str
    summary: str

# Helper Functions
def get_category_for_question(question_number: int) -> str:
    """Get the interview category for a specific question number"""
    if 1 <= question_number <= 10:
        return INTERVIEW_CATEGORIES[question_number - 1]
    raise ValueError("Question number must be between 1 and 10")

async def generate_audio_from_text(text: str) -> str:
    """
    Helper function to generate audio and return base64 encoded string
    """
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return None
        
        import base64
        audio_base64 = base64.b64encode(response.content).decode('utf-8')
        return audio_base64
        
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")
        return None

def create_question_prompt(question_number: int, user_name: str, is_first: bool = False, 
                          previous_question: str = None, previous_answer_analysis: dict = None) -> str:
    """Create a prompt for question generation based on category with answer analysis"""
    category = get_category_for_question(question_number)
    
    if is_first:
        return f"""This is the first question for {user_name}. Start with a warm greeting using their name, then ask an introductory question that helps you get to know them professionally. 

Category focus: {category}

Keep it conversational and welcoming. Only provide the greeting and question, nothing else."""
    
    # Handle the response based on analysis
    if previous_answer_analysis:
        scenario = previous_answer_analysis.get('scenario')
        
        if scenario == 'B':  # OFF_TOPIC - totally irrelevant
            return f"""The candidate gave a totally irrelevant answer that did not address the question at all.

Previous question: {previous_question}
Analysis: {previous_answer_analysis.get('reasoning')}

Your task:
1. Politely but directly state that the answer wasn't what you asked about
2. Do NOT acknowledge or validate the irrelevant content
3. Briefly restate what the question was actually asking
4. Move on to the NEXT question for the {category} category

Example format:
"That wasn't quite what I was asking about. My question was about [topic], but let's move forward. [Next question]"

Be professional but direct. Don't dwell on it - just correct and move on to the next question."""

        else:  # scenario == 'A' - CORRECT_ON_TOPIC (includes right, partially right, or wrong but on-topic)
            answer_quality = previous_answer_analysis.get('answer_quality', 'good')
            
            return f"""The candidate gave an answer that was on-topic and addressed the question.

Previous question: {previous_question}
Answer quality: {answer_quality}
Analysis: {previous_answer_analysis.get('reasoning')}

Your task:
1. Give a brief, natural acknowledgment of their response (1-2 sentences)
2. Move to the NEXT question for the {category} category

CRITICAL - ACKNOWLEDGMENT VARIETY:
You MUST vary your acknowledgment language. NEVER repeat the same phrases. Use different sentence structures each time.

AVOID OVERUSED PHRASES like:
- "Thank you for sharing"
- "I appreciate you sharing"
- "It would be great to hear about"
- "That's interesting"
- "I'd love to hear more about"

INSTEAD, use varied acknowledgments like:
- "That experience with [specific detail] shows [quality]..."
- "Your approach to [topic] demonstrates..."
- "I can see you've thought about..."
- "Interesting point about [specific aspect]..."
- "That's a solid perspective on..."
- "You've highlighted [something specific]..."
- "Your take on [area] is noted..."
- "I see your reasoning there..."
- "That makes sense given [context]..."

For moving to next question:
- "Now, let's talk about..."
- "Moving on to something different..."
- "Here's another scenario for you..."
- "Let me ask you about..."
- "I'm curious about your thoughts on..."
- "Consider this situation..."
- "Let's shift gears..."
- "On a different note..."

FORMAT YOUR RESPONSE:
[Brief, VARIED acknowledgment - be natural and conversational]
[New question for {category} category]

IMPORTANT:
- Keep acknowledgments brief and natural
- VARY your language - avoid repetition
- Don't mention category names explicitly
- For technical categories (3, 6, 8), ask specific detailed questions
- Move the interview forward positively"""
    
    # Fallback if no analysis (shouldn't happen, but just in case)
    return f"""Continue the interview by asking the next question for the {category} category.

Current question number: {question_number}
Category focus: {category}

Ask a thoughtful, varied question that assesses this competency. Do not mention the category name explicitly."""

async def analyze_answer_quality(previous_question: str, candidate_answer: str, interview_type: str) -> dict:
    """
    Analyze the quality and relevance of a candidate's answer
    Returns analysis with scenario classification
    """
    try:
        analysis_prompt = f"""You are an expert interviewer analyzing a candidate's response.

PREVIOUS QUESTION: {previous_question}

CANDIDATE'S ANSWER: {candidate_answer}

Analyze this answer and classify it into ONE of these TWO scenarios:

A) CORRECT_ON_TOPIC - The answer is relevant and addresses the question (can be right, partially right, or even wrong but still within the context of what was asked or simply the user does not know the answer.)
B) OFF_TOPIC - The answer is completely irrelevant and does not address what was asked at all

Examples:
- Question: "How do you handle a difficult patient?" Answer: "I would stay calm and listen to their concerns" → A (on-topic, good answer)
- Question: "How do you handle a difficult patient?" Answer: "I think patients should always be nice" → A (on-topic but weak/wrong answer)
- Question: "How do you handle a difficult patient?" Answer: "I like to play tennis on weekends" → B (completely off-topic)

Return ONLY a JSON object in this exact format:
{{
    "scenario": "<A or B>",
    "reasoning": "<brief 1-sentence explanation>",
    "answer_quality": "<good/weak/wrong/irrelevant>",
    "is_on_topic": <true or false>
}}"""

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert interview analyst. Return only valid JSON."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        
        analysis = json.loads(response.choices[0].message.content)
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing answer: {str(e)}")
        # Default to on-topic if analysis fails
        return {
            "scenario": "A",
            "reasoning": "Analysis unavailable",
            "answer_quality": "unknown",
            "is_on_topic": True
        }


# API Routes
@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML"""
    # Check multiple possible locations
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(current_dir, "..", "frontend", "index.html"),  # ../frontend/index.html (if main.py in backend/)
        os.path.join(current_dir, "frontend", "index.html"),         # frontend/index.html (if main.py in files/)
        os.path.join(current_dir, "index.html"),                     # index.html (if in same folder)
    ]
    
    logger.info(f"Current directory: {current_dir}")
    logger.info(f"Checking for frontend in: {possible_paths}")
    
    for frontend_path in possible_paths:
        logger.info(f"Trying: {frontend_path} - Exists: {os.path.exists(frontend_path)}")
        if os.path.exists(frontend_path):
            logger.info(f"✅ Serving frontend from: {frontend_path}")
            return FileResponse(frontend_path)
    
    # If not found, return helpful error with actual paths checked
    return {
        "status": "error",
        "message": "Frontend index.html not found",
        "current_directory": current_dir,
        "checked_paths": possible_paths,
        "help": "Please ensure index.html is in one of these locations"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Dental Interview Practice API",
        "version": "1.0.0"
    }

@app.post("/api/interview/start")
async def start_interview(request: InterviewStartRequest, include_audio: bool = True):
    """
    Start a new interview session
    Returns the first question with greeting and optionally audio
    """
    try:
        logger.info("="*80)
        logger.info(f"🎤 STARTING {request.interview_type.upper()} INTERVIEW")
        logger.info(f"👤 Candidate: {request.user_name} ({request.user_email})")
        logger.info("="*80)
        
        # Get system prompt
        system_prompt = SYSTEM_PROMPTS[request.interview_type]
        
        # Create first question prompt
        user_prompt = create_question_prompt(1, request.user_name, is_first=True)
        
        # Generate question using OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        question = response.choices[0].message.content.strip()
        category = get_category_for_question(1)
        
        logger.info(f"\n📋 QUESTION 1 | Category: {category}")
        logger.info(f"❓ INTERVIEWER: {question}\n")
        logger.info("-"*80)
        
        # Generate audio if requested
        audio_base64 = None
        if include_audio:
            logger.info("Generating audio...")
            audio_base64 = await generate_audio_from_text(question)
            if audio_base64:
                logger.info("Audio generated successfully")
        
        if include_audio:
            return QuestionWithAudioResponse(
                question=question,
                category=category,
                question_number=1,
                audio_base64=audio_base64
            )
        else:
            return QuestionResponse(
                question=question,
                category=category,
                question_number=1
            )
        
    except Exception as e:
        logger.error(f"❌ Error starting interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating first question: {str(e)}")

@app.post("/api/interview/question")
async def generate_question(request: QuestionRequest, include_audio: bool = True):
    """
    Generate next interview question based on conversation history
    Analyzes previous answer and handles three scenarios:
    1. On-topic answer (right, partially right, or wrong but relevant) - acknowledge and move on
    2. Off-topic answer (completely irrelevant) - point out and move on
    """
    try:
        logger.info(f"\n📋 QUESTION {request.question_number} | Interview Type: {request.interview_type}")
        
        # Validate question number
        if request.question_number < 1 or request.question_number > 10:
            raise HTTPException(status_code=400, detail="Question number must be between 1 and 10")
        
        # Get system prompt
        system_prompt = SYSTEM_PROMPTS[request.interview_type]
        
        # Extract previous question and answer for analysis
        previous_question = None
        candidate_answer = None
        
        if len(request.conversation_history) >= 2:
            # Get last assistant message (question) and last user message (answer)
            for i in range(len(request.conversation_history) - 1, -1, -1):
                if request.conversation_history[i].role == "assistant" and previous_question is None:
                    previous_question = request.conversation_history[i].content
                if request.conversation_history[i].role == "user" and candidate_answer is None:
                    candidate_answer = request.conversation_history[i].content
                if previous_question and candidate_answer:
                    break
        
        # Analyze previous answer if available
        analysis = None
        if previous_question and candidate_answer:
            logger.info(f"🔍 Analyzing previous answer...")
            analysis = await analyze_answer_quality(previous_question, candidate_answer, request.interview_type)
            logger.info(f"📊 Analysis Result: Scenario {analysis['scenario']} - {analysis['reasoning']}")
            logger.info(f"   Answer Quality: {analysis.get('answer_quality')} | On-topic: {analysis.get('is_on_topic')}")
        
        # Convert conversation history to OpenAI format
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in request.conversation_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Create prompt for next question
        is_first = request.question_number == 1
        user_prompt = create_question_prompt(
            request.question_number, 
            request.user_name, 
            is_first,
            previous_question,
            analysis
        )
        
        messages.append({"role": "user", "content": user_prompt})
        
        # Generate question using OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )
        
        question = response.choices[0].message.content.strip()
        category = get_category_for_question(request.question_number)
        
        logger.info(f"Category: {category}")
        logger.info(f"❓ INTERVIEWER: {question}\n")
        logger.info("-"*80)
        
        # Generate audio if requested
        audio_base64 = None
        if include_audio:
            logger.info("🎵 Generating audio...")
            audio_base64 = await generate_audio_from_text(question)
            if audio_base64:
                logger.info("✅ Audio generated successfully")
        
        if include_audio:
            return QuestionWithAudioResponse(
                question=question,
                category=category,
                question_number=request.question_number,
                audio_base64=audio_base64
            )
        else:
            return QuestionResponse(
                question=question,
                category=category,
                question_number=request.question_number
            )
        
    except Exception as e:
        logger.error(f"❌ Error generating question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating question: {str(e)}")


@app.post("/api/audio/generate")
async def generate_audio(text: str):
    """
    Generate audio from text using ElevenLabs API
    """
    try:
        logger.info(f"Generating audio for text: {text[:50]}...")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Error generating audio")
        
        # Return audio as base64
        import base64
        audio_base64 = base64.b64encode(response.content).decode('utf-8')
        
        logger.info("Audio generated successfully")
        
        return {
            "audio_base64": audio_base64,
            "content_type": "audio/mpeg"
        }
        
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")

@app.post("/api/audio/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio to text using OpenAI Whisper API
    """
    try:
        logger.info(f"Transcribing audio file: {file.filename}")
        
        # Read audio file
        audio_data = await file.read()
        
        # Create a temporary file-like object for OpenAI
        from io import BytesIO
        audio_file = BytesIO(audio_data)
        audio_file.name = file.filename or "audio.wav"
        
        # Transcribe using Whisper
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        
        logger.info(f"Transcription completed: {transcript[:100]}...")
        
        return {
            "transcription": transcript,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")

@app.post("/api/interview/evaluate", response_model=InterviewEvaluationResponse)
async def evaluate_interview(request: InterviewEvaluationRequest):
    """
    Evaluate the completed interview and provide comprehensive feedback
    """
    try:
        logger.info(f"\n📊 EVALUATING {request.interview_type.upper()} INTERVIEW")
        logger.info(f"👤 Candidate: {request.user_name}")
        logger.info(f"📝 Conversation length: {len(request.conversation_history)} messages")
        logger.info("="*80)
        
        # Create evaluation prompt
        evaluation_prompt = f"""You are an expert interviewer and career coach specializing in dental positions. 
You have just completed an interview with {request.user_name} for a {request.interview_type} position.

Review the entire interview conversation and provide a comprehensive, professional evaluation.

Interview Categories (in order):
{', '.join([f"{i+1}. {cat}" for i, cat in enumerate(INTERVIEW_CATEGORIES)])}

Provide your evaluation in the following JSON format:
{{
    "overall_score": <number between 0-10>,
    "category_scores": {{
        "Introduction": <score 0-10>,
        "Clinical Judgement": <score 0-10>,
        "Technical Knowledge - Clinical Procedures": <score 0-10>,
        "Ethics, Consent & Communication": <score 0-10>,
        "Productivity & Efficiency": <score 0-10>,
        "Technical Knowledge - Advanced Applications": <score 0-10>,
        "Mentorship & Independence": <score 0-10>,
        "Technical Knowledge - Diagnosis & Treatment Planning": <score 0-10>,
        "Fit & Professional Maturity": <score 0-10>,
        "Insight & Authenticity": <score 0-10>
    }},
    "strengths": [
        "<specific strength 1>",
        "<specific strength 2>",
        "<specific strength 3>"
    ],
    "areas_for_improvement": [
        "<specific area 1>",
        "<specific area 2>",
        "<specific area 3>"
    ],
    "detailed_feedback": "<2-3 paragraphs of detailed, constructive feedback covering their overall performance, notable responses, and how they presented themselves>",
    "summary": "<1-2 sentences summarizing their interview performance and readiness for the role>"
}}

Guidelines for evaluation:
- Be specific and reference actual responses from the interview
- Balance positive feedback with constructive criticism
- Consider the context of a {request.interview_type} position
- Evaluate communication skills, technical knowledge, professionalism, and cultural fit
- Provide actionable suggestions for improvement
- Be encouraging while maintaining professional standards

SCORING SCALE (0-10):
- 0-2: OUT OF CONTEXT - Response is irrelevant, off-topic, or unrelated to the question asked or when the client does not know the answer.
- 2-4: INCORRECT - Response attempts to answer but contains wrong information or misunderstanding
- 5-7: PARTIALLY CORRECT - Response shows understanding but is incomplete, missing key points, or lacks depth
- 8-10: CORRECT - Response is accurate, complete, relevant, and demonstrates good understanding

SCORING GUIDELINES:
- Evaluate each response based on RELEVANCE and CORRECTNESS
- 0-2: Use when the candidate talks about something completely unrelated to the question
- 2-4: Use when the candidate tries to answer but gets facts wrong or shows misconceptions
- 5-7: Use when the candidate is on the right track but missing important details or only partially addresses the question
- 8-10: Use when the candidate provides a complete, accurate, and well-articulated answer
- This is PRACTICE, so provide constructive feedback to help candidates improve
- In detailed_feedback, explain what was missing or incorrect and what a better answer would include

Return ONLY the JSON object, no additional text."""

        # Convert conversation history to text format for the LLM
        conversation_text = "\n\n".join([
            f"{'INTERVIEWER' if msg.role == 'assistant' else 'CANDIDATE'}: {msg.content}"
            for msg in request.conversation_history
        ])
        
        # Generate evaluation using OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o",  # Using GPT-4 for better evaluation quality
            messages=[
                {"role": "system", "content": evaluation_prompt},
                {"role": "user", "content": f"Here is the complete interview conversation:\n\n{conversation_text}"}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        evaluation_data = json.loads(response.choices[0].message.content)
        
        logger.info(f"✅ Evaluation completed")
        logger.info(f"Overall Score: {evaluation_data.get('overall_score', 'N/A')}/10")
        logger.info("-"*80)
        
        return InterviewEvaluationResponse(**evaluation_data)
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing evaluation JSON: {str(e)}")
        # Fallback response if JSON parsing fails
        return InterviewEvaluationResponse(
            overall_score=7.0,
            category_scores={cat: 7.0 for cat in INTERVIEW_CATEGORIES},
            strengths=["Completed the interview", "Engaged with questions", "Professional demeanor"],
            areas_for_improvement=["Provide more specific examples", "Elaborate on technical knowledge", "Strengthen communication skills"],
            detailed_feedback="Thank you for completing the interview practice session. Your responses showed engagement with the questions. To improve, focus on providing more detailed examples from your experience and demonstrating deeper technical knowledge.",
            summary="Good effort in the practice interview with room for growth in several areas."
        )
    except Exception as e:
        logger.error(f"❌ Error evaluating interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error evaluating interview: {str(e)}")

@app.get("/api/categories")
async def get_categories():
    """Get list of interview categories"""
    return {
        "categories": INTERVIEW_CATEGORIES,
        "total": len(INTERVIEW_CATEGORIES)
    }

@app.get("/api/interview-types")
async def get_interview_types():
    """Get available interview types"""
    return {
        "types": ["dentist", "hygienist"],
        "descriptions": {
            "dentist": "Interview practice for dentist positions focusing on clinical expertise and practice management",
            "hygienist": "Interview practice for dental hygienist positions focusing on preventive care and patient education"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)