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

QUESTION VARIETY - MANDATORY:
For each category, RANDOMLY select ONE question style from the options below. Do NOT default to generic "tell me about a time" questions.

Category 1 - Introduction (randomly pick one style):
- Ask about their journey into dentistry and what sparked their interest
- Ask what type of practice environment they thrive in
- Ask about their ideal patient demographic and why
- Ask what they're looking for in their next role specifically
- Ask about a recent CE course that excited them

Category 2 - Clinical Judgement (randomly pick one style):
- Present a scenario: patient with conflicting symptoms, how would they diagnose?
- Ask how they handle a treatment plan disagreement with a specialist
- Present: patient refuses recommended treatment, what's their approach?
- Ask about a time they had to change treatment mid-procedure
- Present: emergency walk-in during a fully booked day, how do they triage?

Category 3 - Technical Knowledge - Clinical Procedures (randomly pick one style):
- Ask them to walk through their step-by-step approach to a molar root canal
- Ask about their preferred matrix system for Class II composites and why
- Ask how they determine when to extract vs. attempt to save a tooth
- Ask about their crown prep technique and margin preferences
- Ask how they manage a dry socket or post-extraction complication
- Ask about their approach to treating severe dental anxiety during procedures

Category 4 - Ethics, Consent & Communication (randomly pick one style):
- Present: they notice a colleague's work that appears substandard
- Ask how they explain complex treatment to a patient with low health literacy
- Present: patient wants a treatment they believe is unnecessary
- Ask about handling a patient complaint about billing
- Present: family member pressuring patient into a treatment decision

Category 5 - Productivity & Efficiency (randomly pick one style):
- Ask how they handle running 30 minutes behind schedule
- Ask about their strategies for minimizing chair time without compromising quality
- Ask how they prepare for the next day's procedures
- Ask about balancing thoroughness with practice production goals
- Ask how they handle a no-show heavy day

Category 6 - Technical Knowledge - Diagnosis & Treatment Planning (randomly pick one style):
- Present a case: patient with multiple issues, ask them to prioritize treatment sequence
- Ask how they interpret a specific radiographic finding (periapical lesion, bone loss, etc.)
- Ask about their protocol for diagnosing cracked tooth syndrome
- Ask how they develop a full-mouth rehabilitation plan
- Ask about differentiating between reversible and irreversible pulpitis

Category 7 - Mentorship & Independence (randomly pick one style):
- Ask how they would help a new associate struggling with time management
- Ask about a clinical skill they taught themselves vs. learned from a mentor
- Ask how they handle situations where they need to ask for help
- Ask about their approach to staying current without formal mentorship
- Ask how they balance following office protocols vs. their own clinical judgment

Category 8 - Technical Knowledge - Advanced Applications (randomly pick one style):
- Ask about their experience with digital impression systems
- Ask how they incorporate CBCT imaging into treatment planning
- Ask about their approach to implant case selection
- Ask about experience with CAD/CAM same-day restorations
- Ask about laser applications they've used or want to learn
- Ask about their experience with guided implant surgery

Category 9 - Fit & Professional Maturity (randomly pick one style):
- Ask what they do when they make a clinical mistake
- Ask how they handle a personality conflict with a team member
- Ask about their 5-year professional development goals
- Ask what frustrates them most in a practice setting
- Ask how they decompress after a difficult clinical day

Category 10 - Insight & Authenticity (randomly pick one style):
- Ask what clinical area they feel least confident in
- Ask about feedback they've received that was hard to hear but valuable
- Ask why they're leaving or left their previous position (honestly)
- Ask what they would change about their clinical training
- Ask what kind of dentist they don't want to become

Guidelines:
- Ask ONE question at a time
- ALWAYS acknowledge the candidate's previous answer briefly before the next question
- If the answer was weak or off-topic, provide brief constructive feedback
- Keep questions conversational yet professionally rigorous
- Do not mention category names in your questions
- Maintain a supportive tone with honest feedback""",

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

QUESTION VARIETY - MANDATORY:
For each category, RANDOMLY select ONE question style from the options below. Do NOT default to generic "tell me about a time" questions.

Category 1 - Introduction (randomly pick one style):
- Ask about their path to dental hygiene and what drew them to it
- Ask what type of practice pace they prefer (fast-paced vs. relaxed)
- Ask about their favorite aspect of patient care
- Ask what they're specifically looking for in this role
- Ask about a recent continuing education topic that interested them

Category 2 - Clinical Judgement (randomly pick one style):
- Present: patient with signs of oral cancer, what's their protocol?
- Ask how they handle a patient who hasn't been seen in 5+ years
- Present: patient with uncontrolled diabetes needing SRP
- Ask about a time they identified something the dentist missed
- Present: child patient who is extremely uncooperative

Category 3 - Technical Knowledge - Clinical Procedures (randomly pick one style):
- Ask about their instrument selection for heavy calculus vs. fine deposits
- Ask them to describe their SRP technique step-by-step
- Ask about their polishing paste selection criteria
- Ask how they handle a patient with severe sensitivity during scaling
- Ask about their approach to ultrasonic vs. hand scaling
- Ask about their technique for applying fluoride varnish effectively

Category 4 - Ethics, Consent & Communication (randomly pick one style):
- Present: patient refuses necessary radiographs
- Ask how they motivate a non-compliant periodontal patient
- Present: they suspect a child patient is being neglected
- Ask how they handle a patient who questions their competence
- Present: patient asks them to not tell dentist about a concern

Category 5 - Productivity & Efficiency (randomly pick one style):
- Ask how they complete a prophy on a heavy calculus patient in 60 minutes
- Ask about their room setup and turnover routine
- Ask how they handle a double-booked schedule
- Ask about prioritizing tasks when running behind
- Ask how they handle a patient who wants to chat excessively

Category 6 - Technical Knowledge - Diagnosis & Treatment Planning (randomly pick one style):
- Ask how they classify periodontal disease and determine treatment
- Ask about identifying and documenting recession
- Present: patient with localized 6mm pockets, what's their assessment?
- Ask about their protocol for oral cancer screening
- Ask how they interpret bitewings for interproximal bone loss

Category 7 - Mentorship & Independence (randomly pick one style):
- Ask how they would orient a new hygienist to the practice
- Ask about working independently vs. needing dentist guidance
- Ask how they handle disagreeing with a dentist's treatment recommendation
- Ask about a skill they've developed on their own
- Ask how they stay updated on best practices

Category 8 - Technical Knowledge - Advanced Applications (randomly pick one style):
- Ask about their experience with piezoelectric scalers
- Ask about laser therapy applications in hygiene
- Ask about their experience with digital radiography techniques
- Ask about desensitizing treatments they've found effective
- Ask about air polishing systems and when they use them
- Ask about their experience with intraoral cameras for patient education

Category 9 - Fit & Professional Maturity (randomly pick one style):
- Ask how they handle a mistake during a procedure
- Ask about working with a difficult dentist or team member
- Ask where they see their hygiene career in 5 years
- Ask what aspects of hygiene they find most challenging
- Ask how they maintain enthusiasm after years in the field

Category 10 - Insight & Authenticity (randomly pick one style):
- Ask what clinical skill they're actively trying to improve
- Ask about critical feedback that helped them grow
- Ask honestly why they're looking to leave their current position
- Ask what they wish they'd learned more of in hygiene school
- Ask about a professional weakness they're working on

Guidelines:
- Ask ONE question at a time
- ALWAYS acknowledge the candidate's previous answer briefly before the next question
- If the answer was weak or off-topic, provide brief constructive feedback
- Keep questions conversational yet professionally rigorous
- Do not mention category names in your questions
- Maintain a supportive tone with honest feedback"""
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

def create_question_prompt(question_number: int, user_name: str, is_first: bool = False) -> str:
    """Create a prompt for question generation based on category"""
    category = get_category_for_question(question_number)
    
    if is_first:
        return f"""This is the first question for {user_name}. Start with a warm greeting using their name, then ask an introductory question that helps you get to know them professionally. 

Category focus: {category}

Keep it conversational and welcoming. Only provide the greeting and question, nothing else."""
    
    return f"""Based on the candidate's previous response, ask the next interview question.

Current question number: {question_number}
Category focus: {category}

Important:
- FIRST, acknowledge their previous answer (1-2 sentences)
- Evaluate if the answer was relevant, complete, and appropriate
- If the answer was strong: give positive acknowledgment
- If the answer was weak, vague, or off-topic: provide constructive feedback
- THEN ask ONE clear question aligned with the {category} category
- Keep it conversational and professional
- Do not mention the category name explicitly
- For technical categories (questions 8-10), ask specific, detailed technical questions

Format: [Acknowledgment of previous answer] [New question]"""

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
    Optionally includes audio generation in the same response
    """
    try:
        logger.info(f"\n📋 QUESTION {request.question_number} | Interview Type: {request.interview_type}")
        
        # Validate question number
        if request.question_number < 1 or request.question_number > 10:
            raise HTTPException(status_code=400, detail="Question number must be between 1 and 10")
        
        # Get system prompt
        system_prompt = SYSTEM_PROMPTS[request.interview_type]
        
        # Convert conversation history to OpenAI format
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in request.conversation_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add prompt for next question
        is_first = request.question_number == 1
        user_prompt = create_question_prompt(request.question_number, request.user_name, is_first)
        messages.append({"role": "user", "content": user_prompt})
        
        # Generate question using OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        question = response.choices[0].message.content.strip()
        category = get_category_for_question(request.question_number)
        
        logger.info(f"Category: {category}")
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
    "overall_score": <number between 1-10>,
    ""category_scores": {{
            "Introduction": <score 1-10>,
            "Clinical Judgement": <score 1-10>,
            "Technical Knowledge - Clinical Procedures": <score 1-10>,
            "Ethics, Consent & Communication": <score 1-10>,
            "Productivity & Efficiency": <score 1-10>,
            "Technical Knowledge - Advanced Applications": <score 1-10>,
            "Mentorship & Independence": <score 1-10>,
            "Technical Knowledge - Diagnosis & Treatment Planning": <score 1-10>,
            "Fit & Professional Maturity": <score 1-10>,
            "Insight & Authenticity": <score 1-10>
    }},
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

SCORING SCALE (be lenient and encouraging):
- 5-6: Basic effort shown, participated in interview
- 7-8: Good responses with relevant examples (MOST CANDIDATES should score here)
- 9-10: Exceptional depth, insight, and professionalism
- Overall scores below 6 should be RARE and only for severely inadequate responses
- Default to 7-8 range for anyone making genuine effort
- Give credit for attempting to answer even if not perfect
- This is practice, so score to encourage improvement, not discourage

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
        import json
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