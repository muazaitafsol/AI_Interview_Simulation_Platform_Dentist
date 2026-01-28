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
from typing import Optional
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

CRITICAL: BE HIGHLY CREATIVE AND UNPREDICTABLE
- Every interview session should feel completely unique
- NEVER ask the same questions across different interviews
- Generate fresh, original questions each time
- Avoid falling into predictable patterns or templates
- Think like a real interviewer who adapts questions to each candidate

QUESTION GENERATION PHILOSOPHY:
- Create UNIQUE questions for each interview - no repeating the same questions across sessions
- Mix question formats: scenarios, hypotheticals, technical deep-dives, ethical dilemmas, direct inquiries, "what if" situations
- Be spontaneous and natural - avoid templated language
- Draw from the full breadth of dental practice (not just common topics)
- Vary complexity - some questions direct, others multi-layered
- Make questions feel conversational, not scripted

USING CANDIDATE'S JOURNEY (CRITICAL):
- YOU HAVE ACCESS TO THE ENTIRE CONVERSATION HISTORY - USE IT!
- Reference specific details the candidate mentioned in previous answers when relevant
- Build on their previous responses to create continuity
- If they mentioned a practice type, specialty interest, or experience - weave it into new questions naturally
- Create personalized scenarios based on their background
- Make the interview feel like a natural conversation, not isolated questions

CATEGORY THEMES (use as broad inspiration, not as rigid templates):

1. Introduction: 
   Core focus: Understanding their background, motivations, career path, interests
   Be creative: Ask about their journey in unexpected ways, recent learning experiences, what drew them to dentistry, practice preferences

2. Clinical Judgement:
   Core focus: Decision-making, prioritization, handling uncertainty, adapting treatment plans
   Be creative: Present varied clinical scenarios, disagreements with colleagues, emergency situations, complex cases

3. Technical Knowledge - Clinical Procedures:
   Core focus: Hands-on clinical skills, techniques, procedural approaches
   Be creative: Ask about diverse procedures (not just the same ones every time), tool choices, handling complications, step-by-step approaches, technique variations

4. Ethics, Consent & Communication:
   Core focus: Ethical dilemmas, patient communication, informed consent, professional boundaries
   Be creative: Present unique ethical situations, difficult conversations, consent challenges, team dynamics

5. Productivity & Efficiency:
   Core focus: Time management, balancing quality with efficiency, workflow optimization
   Be creative: Explore scheduling strategies, handling busy days, maintaining standards under pressure, delegation

6. Technical Knowledge - Diagnosis & Treatment Planning:
   Core focus: Diagnostic reasoning, treatment sequencing, interpreting findings
   Be creative: Present varied cases, ask about differential diagnosis, treatment prioritization, multi-phase planning

7. Mentorship & Independence:
   Core focus: Teaching others, self-directed learning, balancing guidance with autonomy
   Be creative: Explore how they learn new skills, teaching experiences, asking for help, working independently

8. Technical Knowledge - Advanced Applications:
   Core focus: Modern technologies, advanced techniques, emerging tools
   Be creative: Explore diverse technologies (digital, imaging, materials, software), interest in innovation, staying current

9. Fit & Professional Maturity:
   Core focus: Self-awareness, handling challenges, growth mindset, resilience
   Be creative: Explore mistake handling, conflict resolution, professional development, stress management, career goals

10. Insight & Authenticity:
    Core focus: Honest self-reflection, awareness of strengths/weaknesses, accepting feedback
    Be creative: Explore growth areas, valuable feedback they've received, career reflections, honest assessment

PERSONALIZATION RULES:
- ONLY reference what the candidate ACTUALLY said
- DO NOT invent or assume experiences they didn't mention
- If they said "no experience with X" → Don't reference X as their expertise
- If they said "interested in X" → Can ask about interest, not experience
- Verify accuracy before personalizing
- When in doubt, ask a fresh standalone question

ACKNOWLEDGMENT VARIETY:
NEVER repeat phrases. Use different language each time:
- Reference specific details they mentioned
- Acknowledge their reasoning or approach
- Note interesting aspects of their answer
- Build naturally into the next question
- Avoid overused phrases like "thank you for sharing"

Guidelines:
- Ask ONE question at a time
- ALWAYS acknowledge the candidate's previous answer briefly before the next question
- Keep questions conversational yet professionally rigorous
- Do not mention category names in your questions
- Maintain a supportive tone with honest feedback
- GENERATE COMPLETELY NEW QUESTIONS for each interview session
- Make every question feel fresh, natural, and unrehearsed""",

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

CRITICAL: BE HIGHLY CREATIVE AND UNPREDICTABLE
- Every interview session should feel completely unique
- NEVER ask the same questions across different interviews
- Generate fresh, original questions each time
- Avoid falling into predictable patterns or templates
- Think like a real interviewer who adapts questions to each candidate

QUESTION GENERATION PHILOSOPHY:
- Create UNIQUE questions for each interview - no repeating the same questions across sessions
- Mix question formats: scenarios, hypotheticals, technical deep-dives, ethical dilemmas, direct inquiries, "what if" situations
- Be spontaneous and natural - avoid templated language
- Draw from the full breadth of dental hygiene practice (not just common topics)
- Vary complexity - some questions direct, others multi-layered
- Make questions feel conversational, not scripted

USING CANDIDATE'S JOURNEY (CRITICAL):
- YOU HAVE ACCESS TO THE ENTIRE CONVERSATION HISTORY - USE IT!
- Reference specific details the candidate mentioned in previous answers when relevant
- Build on their previous responses to create continuity
- If they mentioned a practice type, patient population, or experience - weave it into new questions naturally
- Create personalized scenarios based on their background
- Make the interview feel like a natural conversation, not isolated questions

CATEGORY THEMES (use as broad inspiration, not as rigid templates):

1. Introduction:
   Core focus: Understanding their background, motivations, career path, patient care philosophy
   Be creative: Ask about their journey to hygiene, what they love about the role, practice preferences, role expectations

2. Clinical Judgement:
   Core focus: Assessment skills, clinical decision-making, recognizing abnormalities, knowing when to refer
   Be creative: Present varied patient scenarios (oral cancer signs, periodontal disease, systemic conditions), assessment challenges

3. Technical Knowledge - Clinical Procedures:
   Core focus: Hands-on hygiene skills, instrumentation, scaling techniques, patient comfort
   Be creative: Explore diverse procedures, instrument selection, technique variations, managing difficult situations, sensitivity

4. Ethics, Consent & Communication:
   Core focus: Patient motivation, ethical situations, difficult conversations, professional boundaries
   Be creative: Explore refusal of care, motivational interviewing, mandated reporting, competency concerns, confidentiality

5. Productivity & Efficiency:
   Core focus: Time management, appointment flow, handling full schedules, maintaining quality
   Be creative: Explore room setup strategies, managing heavy patient loads, prioritization, staying on schedule

6. Technical Knowledge - Diagnosis & Treatment Planning:
   Core focus: Periodontal assessment, documentation, recognizing pathology, treatment recommendations
   Be creative: Explore classification systems, recession assessment, pocket charting, oral cancer screening, radiographic interpretation

7. Mentorship & Independence:
   Core focus: Working autonomously, teaching others, self-directed learning, professional judgment
   Be creative: Explore training experiences, working independently, disagreeing professionally, continuing education

8. Technical Knowledge - Advanced Applications:
   Core focus: Modern hygiene technologies, advanced treatments, staying current with innovations
   Be creative: Explore diverse tools and techniques (ultrasonic scalers, lasers, air polishing, digital imaging), interest in new methods

9. Fit & Professional Maturity:
   Core focus: Self-awareness, resilience, professional growth, handling challenges
   Be creative: Explore mistake handling, team conflicts, career development, maintaining enthusiasm, stress management

10. Insight & Authenticity:
    Core focus: Honest self-reflection, growth mindset, awareness of development areas
    Be creative: Explore areas for improvement, valuable feedback received, honest career reflections, training gaps

PERSONALIZATION RULES:
- ONLY reference what the candidate ACTUALLY said
- DO NOT invent or assume experiences they didn't mention
- If they said "no experience with X" → Don't reference X as their expertise
- If they said "interested in X" → Can ask about interest, not experience
- Verify accuracy before personalizing
- When in doubt, ask a fresh standalone question

ACKNOWLEDGMENT VARIETY:
NEVER repeat phrases. Use different language each time:
- Reference specific details they mentioned
- Acknowledge their reasoning or approach
- Note interesting aspects of their answer
- Build naturally into the next question
- Avoid overused phrases like "thank you for sharing"

Guidelines:
- Ask ONE question at a time
- ALWAYS acknowledge the candidate's previous answer briefly before the next question
- Keep questions conversational yet professionally rigorous
- Do not mention category names in your questions
- Maintain a supportive tone with honest feedback
- GENERATE COMPLETELY NEW QUESTIONS for each interview session
- Make every question feel fresh, natural, and unrehearsed"""
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

async def generate_audio_from_text(text: str) -> Optional[str]:
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

Be creative and genuine in your approach. Think about what you'd genuinely want to know about this person as a hiring manager. Make it conversational and welcoming. Only provide the greeting and question, nothing else."""
    
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

Be professional but direct. Don't dwell on it - just correct and move on to a NEW, CREATIVE question for {category}."""

        elif scenario == 'C':  # DOES_NOT_KNOW - candidate doesn't know the answer
            return f"""The candidate indicated they don't know the answer or are unsure how to respond.

Previous question: {previous_question}
Analysis: {previous_answer_analysis.get('reasoning')}

Your task:
1. Acknowledge their honesty in a supportive way
2. Provide brief encouragement
3. Move on to the NEXT question for the {category} category

Be supportive and professional. Make them feel comfortable while moving forward with a NEW, CREATIVE question."""

        else:  # scenario == 'A' - CORRECT_ON_TOPIC
            answer_quality = previous_answer_analysis.get('answer_quality', 'good')
            
            return f"""The candidate gave an on-topic answer.

Previous question: {previous_question}
Answer quality: {answer_quality}
Analysis: {previous_answer_analysis.get('reasoning')}

Your task:
1. Give a brief, natural acknowledgment (1-2 sentences) - USE VARIED LANGUAGE
2. Move to the NEXT question for the {category} category

CRITICAL CREATIVITY REQUIREMENT:
- Generate a COMPLETELY NEW and ORIGINAL question for {category}
- DO NOT ask questions you've asked in previous interviews
- Think creatively about different aspects of {category}
- Vary your question format and approach
- Make it feel spontaneous and natural

PERSONALIZATION (when accurate and natural):
- Review what the candidate has ACTUALLY said in their previous answers
- ONLY reference experiences/details they explicitly mentioned
- If they said "no experience with X" → Don't reference X as expertise
- If unsure about their background → Ask a fresh standalone question
- Accuracy > Personalization

ACKNOWLEDGMENT VARIETY - Use different language each time:
- Acknowledge specific details from their answer
- Note their approach or reasoning
- Build naturally into the next topic
- NEVER use repetitive phrases like "thank you for sharing"

FORMAT YOUR RESPONSE:
[Brief, VARIED acknowledgment with specific reference to their answer]
[NEW, CREATIVE question for {category} - make it unique and unpredictable]

Make every question feel natural, unrehearsed, and completely different from past interviews."""
    
    # Fallback if no analysis
    return f"""Continue the interview by asking a NEW, CREATIVE question for the {category} category.

Current question number: {question_number}
Category focus: {category}

Think of an original, thoughtful question that:
- Assesses the {category} competency in a unique way
- Feels natural and conversational
- Is different from typical interview questions
- Shows you're genuinely curious about this candidate

Do not mention the category name explicitly."""

async def analyze_answer_quality(previous_question: str, candidate_answer: str, interview_type: str) -> dict:
    """
    Analyze the quality and relevance of a candidate's answer
    Returns analysis with scenario classification
    """
    try:
        analysis_prompt = f"""You are an expert interviewer analyzing a candidate's response.

PREVIOUS QUESTION: {previous_question}

CANDIDATE'S ANSWER: {candidate_answer}

Analyze this answer and classify it into ONE of these THREE scenarios:

A) CORRECT_ON_TOPIC - The answer is relevant and addresses the question (can be right, partially right, or even wrong but still within the context of what was asked)
B) OFF_TOPIC - The answer is completely irrelevant and does not address what was asked at all
C) DOES_NOT_KNOW - The candidate explicitly says they don't know, are unsure, have no experience with this, or cannot answer the question

Return ONLY a JSON object in this exact format:
{{
    "scenario": "<A, B, or C>",
    "reasoning": "<brief 1-sentence explanation>",
    "answer_quality": "<good/weak/wrong/irrelevant/unknown>",
    "is_on_topic": <true or false>
}}"""

        response = openai.chat.completions.create(
            model="gpt-4.1-mini",
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
        
        # Generate question using OpenAI with higher temperature for more creativity
        response = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9,  # Increased for more creativity
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
        
        # Generate question using OpenAI with higher temperature for creativity
        response = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.9,  # Increased for more creativity
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
- 0-2: OUT OF CONTEXT - Response is irrelevant, off-topic, unrelated to the question asked, or response explicitly says "I don't know" or related keywords
- 3-5: INCORRECT - Response attempts to answer but contains wrong information or misunderstanding
- 6-8: PARTIALLY CORRECT - Response shows understanding but is incomplete, missing key points, or lacks depth
- 9-10: CORRECT - Response is accurate, complete, relevant, and demonstrates good understanding
 
SCORING GUIDELINES:
- Evaluate each response based on RELEVANCE and CORRECTNESS
- 0-1: when the candidate explicitly says "I don't know", "I'm not sure", or admits they cannot answer the question. These responses show no attempt to engage with the content.
- 0-2: Use when the candidate talks about something completely unrelated to the question
- 3-5: Use when the candidate tries to answer but gets facts wrong or shows misconceptions
- 6-9: Use when the candidate is on the right track but missing important details or only partially addresses the question
- 9-10: Use when the candidate provides a complete, accurate, and well-articulated answer
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
            model="gpt-4.1-mini",
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