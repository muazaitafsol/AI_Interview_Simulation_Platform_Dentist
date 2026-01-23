// Application State
const state = {
    currentPage: 'home',
    interviewType: null,
    userName: '',
    userEmail: '',
    conversationHistory: [],
    questionNumber: 0,
    currentQuestion: '',
    currentCategory: '',
    isGeneratingQuestion: false,
    isGeneratingAudio: false,
    isPlaying: false,
    isRecording: false,
    isProcessingAnswer: false,
    isEvaluating: false,
    audioUrl: null,
    mediaRecorder: null,
    audioChunks: [],
    evaluationResults: null,
    recordingStartTime: null
};

// Configuration
const CONFIG = {
    TOTAL_QUESTIONS: 10,
    API_BASE_URL: ""
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
    completionName: document.getElementById('completionName'),
    evaluationLoading: document.getElementById('evaluationLoading'),
    evaluationResults: document.getElementById('evaluationResults'),
    overallScore: document.getElementById('overallScore'),
    evaluationSummary: document.getElementById('evaluationSummary'),
    categoryScores: document.getElementById('categoryScores'),
    strengthsList: document.getElementById('strengthsList'),
    improvementsList: document.getElementById('improvementsList'),
    detailedFeedback: document.getElementById('detailedFeedback')
};

// Initialize the application
function init() {
    setupEventListeners();
    showPage('home');
}

// Setup event listeners
function setupEventListeners() {
    elements.userName.addEventListener('input', validateInputs);
    elements.userEmail.addEventListener('input', validateInputs);
    elements.questionAudio.addEventListener('ended', handleAudioEnded);
    
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Navigation Functions
function showPage(pageName) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
        page.style.display = 'none';
    });
    
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

async function startInterview() {
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
    await generateFirstQuestion();
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
    state.currentCategory = '';
    state.isGeneratingQuestion = false;
    state.isGeneratingAudio = false;
    state.isPlaying = false;
    state.isRecording = false;
    state.isProcessingAnswer = false;
    state.isEvaluating = false;
    state.audioUrl = null;
    state.evaluationResults = null;
    
    if (state.mediaRecorder && state.mediaRecorder.state === 'recording') {
        state.mediaRecorder.stop();
    }
}

async function generateFirstQuestion() {
    state.isGeneratingQuestion = true;
    updateQuestionDisplay(); // Display question placeholder immediately
    
    try {
        console.log('Requesting first question from API...');
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/interview/start?include_audio=true`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                interview_type: state.interviewType,
                user_name: state.userName,
                user_email: state.userEmail
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('First question received:', data);
        
        // Immediately display the question text
        state.currentQuestion = data.question;
        state.currentCategory = data.category;
        state.questionNumber = data.question_number;
        state.isGeneratingQuestion = false;
        
        updateProgress();
        updateQuestionDisplay(); // This updates the UI with the question text immediately
        
        // Handle audio if available, without blocking the question display
        if (data.audio_base64) {
            console.log('Audio received with question, preparing playback...');
            // Start audio generation in the background
            handleReceivedAudio(data.audio_base64);
        } else {
            state.isGeneratingAudio = false; // If audio is not available, proceed without it
            updateRecordingControls(); // Enable recording if no audio is needed
        }
        
    } catch (error) {
        console.error('Error generating first question:', error);
        state.currentQuestion = 'Error generating question. Please refresh and try again.';
        state.isGeneratingQuestion = false;
        updateQuestionDisplay();
        alert('Failed to start interview. Please check your connection and try again.');
    }
}


function handleReceivedAudio(audioBase64) {
    try {
        // Convert base64 to blob and create URL
        const audioBlob = base64ToBlob(audioBase64, 'audio/mpeg');
        const audioUrl = URL.createObjectURL(audioBlob);
        
        state.audioUrl = audioUrl;
        
        // Play the audio immediately
        playAudio(audioUrl);
        
    } catch (error) {
        console.error('Error processing audio:', error);
        // If audio processing fails, just show the question text
        state.isGeneratingAudio = false;
        updateQuestionDisplay();
        updateRecordingControls();
    }
}

function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}

function playAudio(url) {
    if (elements.questionAudio) {
        elements.questionAudio.src = url || state.audioUrl;
        elements.questionAudio.play();
        state.isPlaying = true;
        updateQuestionDisplay();
        updateRecordingControls();
    }
}

function handleAudioEnded() {
    console.log('Audio playback ended');
    state.isPlaying = false;
    state.isGeneratingAudio = false;
    updateQuestionDisplay();
    updateRecordingControls();
}

function replayQuestion() {
    if (state.audioUrl) {
        playAudio(state.audioUrl);
        updateRecordingControls();
    }
}

// Recording Functions
async function startRecording() {
    try {
        console.log('Starting recording...');
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        state.mediaRecorder = new MediaRecorder(stream);
        state.audioChunks = [];
        state.recordingStartTime = Date.now();  // ADD THIS LINE - Track start time
        
        state.mediaRecorder.ondataavailable = (event) => {
            state.audioChunks.push(event.data);
        };
        
        state.mediaRecorder.onstop = async () => {
            console.log('Recording stopped, creating audio blob...');
            
            // ADD THIS BLOCK - Check minimum recording duration
            const recordingDuration = (Date.now() - state.recordingStartTime) / 1000; // in seconds
            console.log('Recording duration:', recordingDuration, 'seconds');
            
            if (recordingDuration < 3) {
                console.log('Recording too short, discarding...');
                stream.getTracks().forEach(track => track.stop());
                state.audioChunks = [];
                state.isProcessingAnswer = false;
                updateRecordingControls();
                
                // Show a brief message to user
                const tempMessage = document.createElement('div');
                tempMessage.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #ef4444; color: white; padding: 1rem 2rem; border-radius: 0.5rem; font-weight: 600; z-index: 1000; box-shadow: 0 4px 6px rgba(0,0,0,0.1);';
                tempMessage.textContent = 'Recording too short! Please speak for at least 3 seconds.';
                document.body.appendChild(tempMessage);
                
                setTimeout(() => {
                    document.body.removeChild(tempMessage);
                }, 2500);
                
                return;
            }
            // END OF ADDED BLOCK
            
            const audioBlob = new Blob(state.audioChunks, { type: 'audio/wav' });
            stream.getTracks().forEach(track => track.stop());
            await transcribeAudio(audioBlob);
        };
        
        state.mediaRecorder.start();
        state.isRecording = true;
        updateRecordingControls();
        console.log('Recording started successfully');
        
    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Unable to access microphone. Please check permissions.');
    }
}

function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        console.log('Stopping recording...');
        state.mediaRecorder.stop();
        state.isRecording = false;
        state.isProcessingAnswer = true;
        updateRecordingControls();
    }
}

async function transcribeAudio(audioBlob) {
    try {
        console.log('Starting transcription...', 'Blob size:', audioBlob.size);
        
        // Create form data
        const formData = new FormData();
        formData.append('file', audioBlob, 'audio.wav');
        
        // Send to backend for transcription
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/audio/transcribe`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Transcription error: ${response.status}`);
        }
        
        const data = await response.json();
        const transcription = data.transcription;
        
        console.log('Transcription received:', transcription);
        
        // Add to conversation history
        const newHistory = [
            ...state.conversationHistory,
            { role: "assistant", content: state.currentQuestion },
            { role: "user", content: transcription }
        ];
        state.conversationHistory = newHistory;
        
        console.log('Current question number:', state.questionNumber);
        console.log('Total questions:', CONFIG.TOTAL_QUESTIONS);
        console.log('Conversation history length:', newHistory.length);
        
        // Generate next question or complete interview
        if (state.questionNumber < CONFIG.TOTAL_QUESTIONS) {
            console.log('Generating next question...');
            state.isProcessingAnswer = false;
            updateRecordingControls();
            await generateNextQuestion(newHistory);
        } else {
            console.log('Interview complete!');
            state.isProcessingAnswer = false;
            completeInterview();
        }
        
    } catch (error) {
        console.error('Error transcribing audio:', error);
        state.isProcessingAnswer = false;
        updateRecordingControls();
        alert('Error processing your answer. Please try again.');
    }
}

async function generateNextQuestion(history) {
    state.isGeneratingQuestion = true;
    updateQuestionDisplay(); // Display the next question immediately
    
    try {
        const nextQuestionNumber = state.questionNumber + 1;
        
        console.log('Requesting next question:', nextQuestionNumber);
        console.log('History length:', history.length);
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/interview/question?include_audio=true`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                interview_type: state.interviewType,
                conversation_history: history,
                question_number: nextQuestionNumber,
                user_name: state.userName
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API error response:', errorText);
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Next question received:', data);
        
        // Immediately display the next question text
        state.currentQuestion = data.question;
        state.currentCategory = data.category;
        state.questionNumber = data.question_number;
        state.isGeneratingQuestion = false;
        
        updateProgress();
        updateQuestionDisplay(); // Updates the UI with the next question text immediately
        
        // Handle audio if available, without blocking the question display
        if (data.audio_base64) {
            console.log('Audio received with question, preparing playback...');
            // Start audio generation in the background
            handleReceivedAudio(data.audio_base64);
        } else {
            state.isGeneratingAudio = false; // If audio is not available, proceed without it
            updateRecordingControls(); // Enable recording if no audio is needed
        }
        
    } catch (error) {
        console.error('Error generating next question:', error);
        state.isGeneratingQuestion = false;
        updateQuestionDisplay();
        alert('Error generating next question. Please try again.');
    }
}


function completeInterview() {
    console.log('Completing interview...');
    elements.completionName.textContent = state.userName;
    showPage('completion');
    
    // Show loading state
    elements.evaluationLoading.style.display = 'block';
    elements.evaluationResults.style.display = 'none';
    
    setTimeout(() => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 100);
    
    // Request evaluation from backend
    evaluateInterview();
}

async function evaluateInterview() {
    state.isEvaluating = true;
    
    try {
        console.log('Requesting interview evaluation...');
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/interview/evaluate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                interview_type: state.interviewType,
                conversation_history: state.conversationHistory,
                user_name: state.userName
            })
        });
        
        if (!response.ok) {
            throw new Error(`Evaluation error: ${response.status}`);
        }
        
        const evaluation = await response.json();
        console.log('Evaluation received:', evaluation);
        
        state.evaluationResults = evaluation;
        displayEvaluationResults(evaluation);
        
    } catch (error) {
        console.error('Error getting evaluation:', error);
        // Show fallback results
        displayFallbackResults();
    } finally {
        state.isEvaluating = false;
    }
}

function displayEvaluationResults(evaluation) {
    // Hide loading, show results
    elements.evaluationLoading.style.display = 'none';
    elements.evaluationResults.style.display = 'block';
    
    // Overall Score
    elements.overallScore.textContent = evaluation.overall_score.toFixed(1);
    
    // Summary
    elements.evaluationSummary.textContent = evaluation.summary;
    
    // Category Scores
    const categories = [
        'Introduction',
        'Clinical Judgement',
        'Technical Knowledge - Clinical Procedures',
        'Ethics, Consent & Communication',
        'Productivity & Efficiency',
        'Technical Knowledge - Advanced Applications',
        'Mentorship & Independence',
        'Technical Knowledge - Diagnosis & Treatment Planning',
        'Fit & Professional Maturity',
        'Insight & Authenticity'
    ];
    
    elements.categoryScores.innerHTML = categories.map(category => {
        const score = evaluation.category_scores[category] || 0;
        const percentage = (score / 10) * 100;
        const color = score >= 8 ? 'indigo' : score >= 6 ? 'blue' : 'amber';
        
        return `
            <div class="space-y-2">
                <div class="flex justify-between items-center">
                    <span class="font-semibold text-slate-700">${category}</span>
                    <span class="text-lg font-bold text-${color}-700">${score.toFixed(1)}</span>
                </div>
                <div class="w-full bg-slate-200 rounded-full h-3">
                    <div class="bg-gradient-to-r from-${color}-500 to-${color}-600 h-3 rounded-full transition-all duration-500" 
                         style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    }).join('');
    
    // Strengths
    elements.strengthsList.innerHTML = evaluation.strengths.map(strength => `
        <li class="flex items-start gap-3">
            <i data-lucide="check-circle" class="text-green-600 flex-shrink-0" style="width: 20px; height: 20px; margin-top: 2px;"></i>
            <span class="text-slate-700">${strength}</span>
        </li>
    `).join('');
    
    // Areas for Improvement
    elements.improvementsList.innerHTML = evaluation.areas_for_improvement.map(area => `
        <li class="flex items-start gap-3">
            <i data-lucide="arrow-up-circle" class="text-amber-600 flex-shrink-0" style="width: 20px; height: 20px; margin-top: 2px;"></i>
            <span class="text-slate-700">${area}</span>
        </li>
    `).join('');
    
    // Detailed Feedback (split into paragraphs)
    const paragraphs = evaluation.detailed_feedback.split('\n\n').filter(p => p.trim());
    elements.detailedFeedback.innerHTML = paragraphs.map(paragraph => 
        `<p>${paragraph}</p>`
    ).join('');
    
    // Re-initialize icons
    setTimeout(() => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 100);
}

function displayFallbackResults() {
    // Hide loading, show results
    elements.evaluationLoading.style.display = 'none';
    elements.evaluationResults.style.display = 'block';
    
    // Show generic positive feedback
    elements.overallScore.textContent = '7.5';
    elements.evaluationSummary.textContent = 'Thank you for completing the interview practice session. You engaged well with the questions and demonstrated professional communication throughout.';
    
    elements.categoryScores.innerHTML = `
        <p class="text-slate-600 text-center py-8">
            Detailed evaluation unavailable. Please try again or contact support.
        </p>
    `;
    
    elements.strengthsList.innerHTML = `
        <li class="flex items-start gap-3">
            <i data-lucide="check-circle" class="text-green-600 flex-shrink-0" style="width: 20px; height: 20px;"></i>
            <span class="text-slate-700">Completed all interview questions</span>
        </li>
        <li class="flex items-start gap-3">
            <i data-lucide="check-circle" class="text-green-600 flex-shrink-0" style="width: 20px; height: 20px;"></i>
            <span class="text-slate-700">Maintained professional communication</span>
        </li>
    `;
    
    elements.improvementsList.innerHTML = `
        <li class="flex items-start gap-3">
            <i data-lucide="arrow-up-circle" class="text-amber-600 flex-shrink-0" style="width: 20px; height: 20px;"></i>
            <span class="text-slate-700">Practice more to refine your responses</span>
        </li>
    `;
    
    elements.detailedFeedback.innerHTML = `
        <p>Thank you for using the interview practice tool. Keep practicing to build your confidence and improve your interview skills.</p>
    `;
    
    setTimeout(() => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 100);
}

function downloadResults() {
    if (!state.evaluationResults) {
        alert('No evaluation results available to download.');
        return;
    }
    
    // Create a formatted text version of results
    const results = state.evaluationResults;
    const text = `
INTERVIEW EVALUATION RESULTS
============================
Candidate: ${state.userName}
Interview Type: ${state.interviewType.charAt(0).toUpperCase() + state.interviewType.slice(1)}
Date: ${new Date().toLocaleDateString()}

OVERALL SCORE: ${results.overall_score}/10

SUMMARY
${results.summary}

CATEGORY SCORES
${Object.entries(results.category_scores).map(([cat, score]) => 
    `${cat}: ${score}/10`
).join('\n')}

STRENGTHS
${results.strengths.map((s, i) => `${i + 1}. ${s}`).join('\n')}

AREAS FOR IMPROVEMENT
${results.areas_for_improvement.map((a, i) => `${i + 1}. ${a}`).join('\n')}

DETAILED FEEDBACK
${results.detailed_feedback}

============================
Generated by Dental Interview Practice AI
    `.trim();
    
    // Create and download file
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `interview-evaluation-${state.userName.replace(/\s+/g, '-')}-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
                <div class="mb-2 text-sm font-semibold text-indigo-600">Category: ${state.currentCategory}</div>
                <p class="question-text">${state.currentQuestion}</p>
                ${state.audioUrl ? `
                    <button onclick="replayQuestion()" class="replay-btn">
                        <i data-lucide="volume-2" style="width: 20px; height: 20px;"></i>
                        Replay Question
                    </button>
                ` : state.isGeneratingAudio ? `
                    <div class="mt-4 flex items-center justify-center gap-2 text-indigo-600">
                        <i data-lucide="loader-2" class="animate-spin" style="width: 20px; height: 20px;"></i>
                        <span class="text-sm">Preparing audio...</span>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    elements.questionContent.innerHTML = html;
    
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