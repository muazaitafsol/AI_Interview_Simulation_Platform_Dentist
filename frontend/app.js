// Application State
const state = {
    currentPage: 'home',
    interviewType: null,
    userName: '',
    userEmail: '',
    conversationHistory: [],
    questionNumber: 0,
    currentQuestion: '',
    isGeneratingQuestion: false,
    isGeneratingAudio: false,
    isPlaying: false,
    isRecording: false,
    isProcessingAnswer: false,
    audioUrl: null,
    mediaRecorder: null,
    audioChunks: []
};

// System Prompts
const SYSTEM_PROMPTS = {
    dentist: `You are an experienced dental practice manager conducting a professional interview for a dentist position. Ask thoughtful, relevant questions about clinical expertise, patient care philosophy, practice management, continuing education, and ethical scenarios. Base follow-up questions on the candidate's previous responses. Keep questions conversational and professional. Ask only one question at a time.`,
    hygienist: `You are an experienced dental practice manager conducting a professional interview for a dental hygienist position. Ask thoughtful, relevant questions about preventive care, patient education, clinical procedures, teamwork, and professional development. Base follow-up questions on the candidate's previous responses. Keep questions conversational and professional. Ask only one question at a time.`
};

// Configuration
const CONFIG = {
    TOTAL_QUESTIONS: 7,
    ANTHROPIC_API_URL: 'https://api.anthropic.com/v1/messages',
    ELEVENLABS_API_URL: 'https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM',
    // Note: In production, API keys should be stored securely on the backend
    ELEVENLABS_API_KEY: 'YOUR_ELEVENLABS_API_KEY'
};

// DOM Elements
const elements = {
    homePage: document.getElementById('homePage'),
    interviewPage: document.getElementById('interviewPage'),
    completionPage: document.getElementById('completionPage'),
    userModal: document.getElementById('userModal'),
    modalTitle: document.getElementById('modalTitle'),
    userName: document.getElementById('userName'),
    userEmail: document.getElementById('userEmail'),
    startBtn: document.getElementById('startBtn'),
    interviewTitle: document.getElementById('interviewTitle'),
    candidateName: document.getElementById('candidateName'),
    currentQuestionNum: document.getElementById('currentQuestionNum'),
    progressBar: document.getElementById('progressBar'),
    questionContent: document.getElementById('questionContent'),
    recordingControls: document.getElementById('recordingControls'),
    questionAudio: document.getElementById('questionAudio'),
    completionName: document.getElementById('completionName')
};

// Initialize the application
function init() {
    setupEventListeners();
    showPage('home');
}

// Setup event listeners
function setupEventListeners() {
    // Input validation
    elements.userName.addEventListener('input', validateInputs);
    elements.userEmail.addEventListener('input', validateInputs);
    
    // Audio element event
    elements.questionAudio.addEventListener('ended', handleAudioEnded);
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Navigation Functions
function showPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
        page.style.display = 'none';
    });
    
    // Show selected page
    const pageElement = document.getElementById(`${pageName}Page`);
    if (pageElement) {
        pageElement.style.display = 'block';
        setTimeout(() => {
            pageElement.classList.add('active');
        }, 10);
    }
    
    state.currentPage = pageName;
}

function selectInterview(type) {
    state.interviewType = type;
    const title = type === 'dentist' ? 'Dentist Interview' : 'Dental Hygienist Interview';
    elements.modalTitle.textContent = title;
    elements.userModal.classList.add('active');
    elements.userModal.style.display = 'flex';
}

function closeModal() {
    elements.userModal.classList.remove('active');
    elements.userModal.style.display = 'none';
    elements.userName.value = '';
    elements.userEmail.value = '';
}

function validateInputs() {
    const name = elements.userName.value.trim();
    const email = elements.userEmail.value.trim();
    const isValid = name.length > 0 && email.length > 0 && isValidEmail(email);
    elements.startBtn.disabled = !isValid;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function startInterview() {
    state.userName = elements.userName.value.trim();
    state.userEmail = elements.userEmail.value.trim();
    
    if (!state.userName || !state.userEmail) return;
    
    // Update UI
    elements.candidateName.textContent = state.userName;
    const title = state.interviewType === 'dentist' ? 'Dentist Interview' : 'Dental Hygienist Interview';
    elements.interviewTitle.textContent = title;
    
    // Reset state
    state.conversationHistory = [];
    state.questionNumber = 0;
    
    // Close modal and show interview page
    closeModal();
    showPage('interview');
    
    // Start the interview
    generateFirstQuestion();
}

function exitInterview() {
    if (confirm('Are you sure you want to exit the interview? Your progress will be lost.')) {
        resetState();
        showPage('home');
    }
}

function returnHome() {
    resetState();
    showPage('home');
}

function resetState() {
    state.conversationHistory = [];
    state.questionNumber = 0;
    state.currentQuestion = '';
    state.isGeneratingQuestion = false;
    state.isGeneratingAudio = false;
    state.isPlaying = false;
    state.isRecording = false;
    state.isProcessingAnswer = false;
    state.audioUrl = null;
    
    if (state.mediaRecorder && state.mediaRecorder.state === 'recording') {
        state.mediaRecorder.stop();
    }
}

// Interview Flow Functions
async function generateFirstQuestion() {
    state.isGeneratingQuestion = true;
    updateQuestionDisplay();
    
    const greeting = `Hello ${state.userName}! Thank you for taking the time to interview with us today. Let's get started.`;
    
    try {
        const systemPrompt = SYSTEM_PROMPTS[state.interviewType];
        const firstQuestion = await generateQuestionWithAI(systemPrompt, []);
        
        const fullMessage = `${greeting} ${firstQuestion}`;
        state.currentQuestion = fullMessage;
        
        await generateAudioForQuestion(fullMessage);
        
        state.questionNumber = 1;
        updateProgress();
        
    } catch (error) {
        console.error('Error generating first question:', error);
        state.currentQuestion = 'Error generating question. Please refresh and try again.';
        state.isGeneratingQuestion = false;
        updateQuestionDisplay();
    }
}

async function generateQuestionWithAI(systemPrompt, history) {
    try {
        const response = await fetch(CONFIG.ANTHROPIC_API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                model: "claude-sonnet-4-20250514",
                max_tokens: 1000,
                system: systemPrompt,
                messages: [
                    ...history,
                    { 
                        role: "user", 
                        content: history.length === 0 
                            ? "Start the interview with an appropriate opening question."
                            : "Based on the candidate's response, ask a relevant follow-up question. Only provide the question, nothing else."
                    }
                ],
            })
        });
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }
        
        const data = await response.json();
        const questionText = data.content
            .filter(item => item.type === "text")
            .map(item => item.text)
            .join("\n")
            .trim();
        
        return questionText;
    } catch (error) {
        console.error('Error calling AI API:', error);
        throw error;
    }
}

async function generateAudioForQuestion(questionText) {
    state.isGeneratingAudio = true;
    state.isGeneratingQuestion = false;
    updateQuestionDisplay();
    
    try {
        // Note: This is a placeholder for ElevenLabs integration
        // In production, you would call the actual ElevenLabs API
        // For demo purposes, we'll use browser's Speech Synthesis API
        
        await speakText(questionText);
        
        /* Production ElevenLabs code would look like:
        const response = await fetch(CONFIG.ELEVENLABS_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'xi-api-key': CONFIG.ELEVENLABS_API_KEY
            },
            body: JSON.stringify({
                text: questionText,
                model_id: "eleven_monolingual_v1",
                voice_settings: {
                    stability: 0.5,
                    similarity_boost: 0.5
                }
            })
        });
        
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        state.audioUrl = url;
        
        playAudio(url);
        */
        
    } catch (error) {
        console.error('Error generating audio:', error);
        state.isGeneratingAudio = false;
        updateQuestionDisplay();
        updateRecordingControls();
    }
}

// Browser Speech Synthesis (fallback for demo)
function speakText(text) {
    return new Promise((resolve, reject) => {
        if (!('speechSynthesis' in window)) {
            reject(new Error('Speech synthesis not supported'));
            return;
        }
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 1;
        
        utterance.onend = () => {
            state.isPlaying = false;
            state.isGeneratingAudio = false;
            updateQuestionDisplay();
            updateRecordingControls();
            resolve();
        };
        
        utterance.onerror = (error) => {
            console.error('Speech synthesis error:', error);
            state.isPlaying = false;
            state.isGeneratingAudio = false;
            updateQuestionDisplay();
            updateRecordingControls();
            reject(error);
        };
        
        state.isPlaying = true;
        updateQuestionDisplay();
        window.speechSynthesis.speak(utterance);
    });
}

function playAudio(url) {
    if (elements.questionAudio) {
        elements.questionAudio.src = url || state.audioUrl;
        elements.questionAudio.play();
        state.isPlaying = true;
        updateQuestionDisplay();
    }
}

function handleAudioEnded() {
    state.isPlaying = false;
    state.isGeneratingAudio = false;
    updateQuestionDisplay();
    updateRecordingControls();
}

function replayQuestion() {
    if (state.currentQuestion) {
        speakText(state.currentQuestion);
    }
}

// Recording Functions
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        state.mediaRecorder = new MediaRecorder(stream);
        state.audioChunks = [];
        
        state.mediaRecorder.ondataavailable = (event) => {
            state.audioChunks.push(event.data);
        };
        
        state.mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(state.audioChunks, { type: 'audio/wav' });
            stream.getTracks().forEach(track => track.stop());
            await transcribeAudio(audioBlob);
        };
        
        state.mediaRecorder.start();
        state.isRecording = true;
        updateRecordingControls();
        
    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Unable to access microphone. Please check permissions.');
    }
}

function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;
        state.isProcessingAnswer = true;
        updateRecordingControls();
    }
}

async function transcribeAudio(audioBlob) {
    try {
        // Note: This is a placeholder for Whisper API integration
        // In production, you would send the audio to OpenAI's Whisper API
        
        // For demo purposes, we'll use browser's Speech Recognition API
        // or simulate a transcription
        
        const transcription = await simulateTranscription(audioBlob);
        
        /* Production Whisper API code would look like:
        const formData = new FormData();
        formData.append('file', audioBlob, 'audio.wav');
        formData.append('model', 'whisper-1');
        
        const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${OPENAI_API_KEY}`
            },
            body: formData
        });
        
        const data = await response.json();
        const transcription = data.text;
        */
        
        // Add to conversation history
        const newHistory = [
            ...state.conversationHistory,
            { role: "assistant", content: state.currentQuestion },
            { role: "user", content: transcription }
        ];
        state.conversationHistory = newHistory;
        
        state.isProcessingAnswer = false;
        updateRecordingControls();
        
        // Generate next question or complete interview
        if (state.questionNumber < CONFIG.TOTAL_QUESTIONS) {
            await generateNextQuestion(newHistory);
        } else {
            completeInterview();
        }
        
    } catch (error) {
        console.error('Error transcribing audio:', error);
        state.isProcessingAnswer = false;
        updateRecordingControls();
        alert('Error processing your answer. Please try again.');
    }
}

// Simulate transcription for demo purposes
async function simulateTranscription(audioBlob) {
    return new Promise((resolve) => {
        // Simulate API delay
        setTimeout(() => {
            resolve("This is a simulated transcription of the user's answer. In production, this would be the actual Whisper API response with the candidate's spoken answer.");
        }, 2000);
    });
}

async function generateNextQuestion(history) {
    state.isGeneratingQuestion = true;
    updateQuestionDisplay();
    updateRecordingControls();
    
    try {
        const systemPrompt = SYSTEM_PROMPTS[state.interviewType];
        const nextQuestion = await generateQuestionWithAI(systemPrompt, history);
        
        state.currentQuestion = nextQuestion;
        await generateAudioForQuestion(nextQuestion);
        
        state.questionNumber++;
        updateProgress();
        
    } catch (error) {
        console.error('Error generating next question:', error);
        state.isGeneratingQuestion = false;
        updateQuestionDisplay();
    }
}

function completeInterview() {
    elements.completionName.textContent = state.userName;
    showPage('completion');
    
    // Reinitialize Lucide icons for the completion page
    setTimeout(() => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 100);
}

// UI Update Functions
function updateProgress() {
    elements.currentQuestionNum.textContent = state.questionNumber;
    
    const progressItems = elements.progressBar.children;
    for (let i = 0; i < progressItems.length; i++) {
        if (i < state.questionNumber) {
            progressItems[i].className = 'flex-1 h-2 rounded-full bg-gradient-to-r from-indigo-600 to-blue-600 transition-all';
        } else {
            progressItems[i].className = 'flex-1 h-2 rounded-full bg-slate-200 transition-all';
        }
    }
}

function updateQuestionDisplay() {
    let html = '';
    
    if (state.isGeneratingQuestion) {
        html = `
            <div class="question-state">
                <i data-lucide="loader-2" class="loading-spinner animate-spin"></i>
                <p class="status-text">Generating question...</p>
            </div>
        `;
    } else if (state.isGeneratingAudio) {
        html = `
            <div class="question-state">
                <i data-lucide="volume-2" class="loading-spinner animate-pulse"></i>
                <p class="status-text">Preparing audio...</p>
            </div>
        `;
    } else if (state.isPlaying) {
        html = `
            <div class="question-state">
                <i data-lucide="volume-2" class="loading-spinner animate-pulse"></i>
                <p class="status-text mb-6">Playing question...</p>
                <p class="question-text">${state.currentQuestion}</p>
            </div>
        `;
    } else if (state.currentQuestion) {
        html = `
            <div class="question-state">
                <p class="question-text">${state.currentQuestion}</p>
                <button onclick="replayQuestion()" class="replay-btn">
                    <i data-lucide="volume-2" style="width: 20px; height: 20px;"></i>
                    Replay Question
                </button>
            </div>
        `;
    }
    
    elements.questionContent.innerHTML = html;
    
    // Reinitialize Lucide icons
    setTimeout(() => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 10);
}

function updateRecordingControls() {
    const canRecord = !state.isGeneratingQuestion && 
                     !state.isGeneratingAudio && 
                     !state.isPlaying && 
                     !state.isProcessingAnswer;
    
    let html = '';
    
    if (state.isProcessingAnswer) {
        html = `
            <div>
                <i data-lucide="loader-2" class="loading-spinner animate-spin"></i>
                <p class="status-text">Processing your answer...</p>
            </div>
        `;
    } else {
        const statusText = !canRecord 
            ? "Please wait for the question to finish playing..."
            : state.isRecording 
                ? "Recording your answer... Click to stop"
                : "Click the microphone to record your answer";
        
        html = `
            <p class="text-lg text-slate-600 mb-6">${statusText}</p>
            <button 
                onclick="${state.isRecording ? 'stopRecording()' : 'startRecording()'}"
                ${!canRecord && !state.isRecording ? 'disabled' : ''}
                class="recording-btn ${state.isRecording ? 'recording' : canRecord ? 'idle' : 'disabled'}"
            >
                <i data-lucide="${state.isRecording ? 'mic-off' : 'mic'}" style="width: 48px; height: 48px; color: white;"></i>
            </button>
            ${state.isRecording ? `
                <div class="recording-indicator">
                    <div class="recording-dot"></div>
                    <span class="text-red-500 font-semibold">Recording in progress</span>
                </div>
            ` : ''}
        `;
    }
    
    elements.recordingControls.innerHTML = html;
    
    // Reinitialize Lucide icons
    setTimeout(() => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 10);
}

// Initialize the app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
