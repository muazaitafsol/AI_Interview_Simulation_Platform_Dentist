"""
Scoring Rubrics for Dental Interview Practice
Turn-by-Turn Evaluation System with Structured Rubrics
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
import json

# ============================================================================
# SCORING RUBRIC DEFINITIONS
# ============================================================================

class ScoringCriteria(BaseModel):
    """Individual scoring criterion"""
    name: str
    weight: float  # 0.0 to 1.0
    description: str
    scoring_guide: Dict[str, str]  # score_range -> description

class CategoryRubric(BaseModel):
    """Rubric for a specific interview category"""
    category: str
    criteria: List[ScoringCriteria]
    
# ============================================================================
# RUBRIC DEFINITIONS FOR EACH CATEGORY
# ============================================================================

INTERVIEW_RUBRICS = {
    "Introduction": CategoryRubric(
        category="Introduction",
        criteria=[
            ScoringCriteria(
                name="Relevance",
                weight=0.4,
                description="How well the answer addresses the question asked",
                scoring_guide={
                    "9-10": "Directly answers question with clear, relevant information",
                    "6-8": "Answers question but includes some tangential information",
                    "3-5": "Partially addresses question, significant off-topic content",
                    "0-2": "Does not answer question, completely off-topic, or says 'I don't know'"
                }
            ),
            ScoringCriteria(
                name="Clarity",
                weight=0.3,
                description="How clear and articulate the response is",
                scoring_guide={
                    "9-10": "Very clear, well-structured, easy to follow",
                    "6-8": "Generally clear but could be better organized",
                    "3-5": "Somewhat unclear, disorganized thoughts",
                    "0-2": "Confusing, incoherent, or no meaningful response"
                }
            ),
            ScoringCriteria(
                name="Depth",
                weight=0.3,
                description="Level of detail and thoughtfulness in the answer",
                scoring_guide={
                    "9-10": "Detailed, thoughtful response with specific examples",
                    "6-8": "Adequate detail but could elaborate more",
                    "3-5": "Surface-level response, lacks depth",
                    "0-2": "Minimal effort, no real substance"
                }
            )
        ]
    ),
    
    "Clinical Judgement": CategoryRubric(
        category="Clinical Judgement",
        criteria=[
            ScoringCriteria(
                name="Relevance",
                weight=0.3,
                description="How well the answer addresses the clinical scenario",
                scoring_guide={
                    "9-10": "Directly addresses scenario with appropriate clinical reasoning",
                    "6-8": "Addresses scenario but misses some key considerations",
                    "3-5": "Partially relevant, shows gaps in clinical thinking",
                    "0-2": "Not relevant, wrong approach, or admits not knowing"
                }
            ),
            ScoringCriteria(
                name="Clinical Accuracy",
                weight=0.4,
                description="Correctness of clinical knowledge and reasoning",
                scoring_guide={
                    "9-10": "Clinically accurate, demonstrates sound judgement",
                    "6-8": "Mostly accurate with minor gaps or oversights",
                    "3-5": "Contains significant clinical errors or misconceptions",
                    "0-2": "Clinically incorrect or dangerous approach"
                }
            ),
            ScoringCriteria(
                name="Decision-Making Process",
                weight=0.3,
                description="Quality of the reasoning and decision-making approach",
                scoring_guide={
                    "9-10": "Systematic, evidence-based approach with clear rationale",
                    "6-8": "Reasonable approach but could be more systematic",
                    "3-5": "Unclear reasoning, jumps to conclusions",
                    "0-2": "No clear reasoning process"
                }
            )
        ]
    ),
    
    "Technical Knowledge - Clinical Procedures": CategoryRubric(
        category="Technical Knowledge - Clinical Procedures",
        criteria=[
            ScoringCriteria(
                name="Relevance",
                weight=0.3,
                description="How well the answer addresses the technical question",
                scoring_guide={
                    "9-10": "Directly addresses procedure with accurate technical details",
                    "6-8": "Addresses question but misses some technical aspects",
                    "3-5": "Partially relevant, lacks key technical information",
                    "0-2": "Not relevant or admits not knowing the procedure"
                }
            ),
            ScoringCriteria(
                name="Technical Accuracy",
                weight=0.5,
                description="Correctness of technical/procedural knowledge",
                scoring_guide={
                    "9-10": "Technically accurate, demonstrates expertise",
                    "6-8": "Generally accurate with minor technical errors",
                    "3-5": "Significant technical errors or outdated information",
                    "0-2": "Incorrect technique or dangerous practice described"
                }
            ),
            ScoringCriteria(
                name="Completeness",
                weight=0.2,
                description="Coverage of important procedural steps or considerations",
                scoring_guide={
                    "9-10": "Comprehensive coverage of procedure and key considerations",
                    "6-8": "Covers main points but misses some details",
                    "3-5": "Incomplete, misses critical steps",
                    "0-2": "Minimal information provided"
                }
            )
        ]
    ),
    
    "Ethics, Consent & Communication": CategoryRubric(
        category="Ethics, Consent & Communication",
        criteria=[
            ScoringCriteria(
                name="Relevance",
                weight=0.3,
                description="How well the answer addresses the ethical/communication scenario",
                scoring_guide={
                    "9-10": "Directly addresses ethical considerations and communication needs",
                    "6-8": "Addresses main points but could be more thorough",
                    "3-5": "Partially addresses scenario, misses key ethical aspects",
                    "0-2": "Not relevant or admits uncertainty about ethics"
                }
            ),
            ScoringCriteria(
                name="Ethical Reasoning",
                weight=0.4,
                description="Quality of ethical analysis and professional standards",
                scoring_guide={
                    "9-10": "Strong ethical reasoning, considers all stakeholders",
                    "6-8": "Sound reasoning but could consider more perspectives",
                    "3-5": "Weak ethical reasoning, misses important considerations",
                    "0-2": "Poor ethical judgement or inappropriate response"
                }
            ),
            ScoringCriteria(
                name="Communication Approach",
                weight=0.3,
                description="Quality of proposed communication strategy",
                scoring_guide={
                    "9-10": "Excellent communication approach, empathetic and clear",
                    "6-8": "Good approach but could be more refined",
                    "3-5": "Basic approach, lacks empathy or clarity",
                    "0-2": "Poor communication strategy or avoids communication"
                }
            )
        ]
    ),
    
    "Productivity & Efficiency": CategoryRubric(
        category="Productivity & Efficiency",
        criteria=[
            ScoringCriteria(
                name="Relevance",
                weight=0.3,
                description="How well the answer addresses productivity/efficiency question",
                scoring_guide={
                    "9-10": "Directly addresses efficiency with practical strategies",
                    "6-8": "Addresses question but could be more specific",
                    "3-5": "Vague response, lacks concrete strategies",
                    "0-2": "Not relevant or admits no experience with efficiency"
                }
            ),
            ScoringCriteria(
                name="Practicality",
                weight=0.4,
                description="How realistic and implementable the approaches are",
                scoring_guide={
                    "9-10": "Highly practical, realistic strategies that work",
                    "6-8": "Generally practical but may have implementation challenges",
                    "3-5": "Somewhat unrealistic or overly theoretical",
                    "0-2": "Impractical or would not work in real settings"
                }
            ),
            ScoringCriteria(
                name="Balance",
                weight=0.3,
                description="Considers quality, safety, and efficiency together",
                scoring_guide={
                    "9-10": "Excellent balance between speed and quality/safety",
                    "6-8": "Considers balance but could be more nuanced",
                    "3-5": "Overemphasizes efficiency at expense of quality",
                    "0-2": "No consideration of quality or safety"
                }
            )
        ]
    ),
    
    "Technical Knowledge - Advanced Applications": CategoryRubric(
        category="Technical Knowledge - Advanced Applications",
        criteria=[
            ScoringCriteria(
                name="Relevance",
                weight=0.3,
                description="How well answer addresses the advanced technical topic",
                scoring_guide={
                    "9-10": "Directly addresses technology/technique with insight",
                    "6-8": "Addresses topic but could show more depth",
                    "3-5": "Basic understanding, lacks advanced perspective",
                    "0-2": "Not relevant or admits unfamiliarity"
                }
            ),
            ScoringCriteria(
                name="Technical Knowledge",
                weight=0.4,
                description="Depth of knowledge about advanced applications",
                scoring_guide={
                    "9-10": "Demonstrates advanced knowledge and current awareness",
                    "6-8": "Good knowledge but may have some gaps",
                    "3-5": "Basic knowledge, outdated or incomplete",
                    "0-2": "Minimal knowledge or significant misconceptions"
                }
            ),
            ScoringCriteria(
                name="Innovation Mindset",
                weight=0.3,
                description="Interest in learning and adopting new technologies",
                scoring_guide={
                    "9-10": "Shows enthusiasm and critical thinking about innovation",
                    "6-8": "Open to new technologies but somewhat cautious",
                    "3-5": "Resistant to change or shows little interest",
                    "0-2": "Dismissive of new technologies or change"
                }
            )
        ]
    ),
    
    "Mentorship & Independence": CategoryRubric(
        category="Mentorship & Independence",
        criteria=[
            ScoringCriteria(
                name="Relevance",
                weight=0.3,
                description="How well answer addresses learning/teaching question",
                scoring_guide={
                    "9-10": "Directly addresses learning or teaching with specific examples",
                    "6-8": "Addresses question but could provide better examples",
                    "3-5": "Vague response about learning or teaching",
                    "0-2": "Not relevant or admits no relevant experience"
                }
            ),
            ScoringCriteria(
                name="Self-Direction",
                weight=0.35,
                description="Shows ability to learn and work independently",
                scoring_guide={
                    "9-10": "Strong self-directed learning approach with examples",
                    "6-8": "Can work independently but may need some guidance",
                    "3-5": "Relies heavily on others, limited independence",
                    "0-2": "Overly dependent or resistant to learning"
                }
            ),
            ScoringCriteria(
                name="Teaching Ability",
                weight=0.35,
                description="Ability to mentor, teach, or explain to others",
                scoring_guide={
                    "9-10": "Excellent teaching approach, patient and clear",
                    "6-8": "Can teach but approach could be refined",
                    "3-5": "Limited teaching skills or patience",
                    "0-2": "Poor teaching ability or unwilling to help others"
                }
            )
        ]
    ),
    
    "Technical Knowledge - Diagnosis & Treatment Planning": CategoryRubric(
        category="Technical Knowledge - Diagnosis & Treatment Planning",
        criteria=[
            ScoringCriteria(
                name="Relevance",
                weight=0.3,
                description="How well answer addresses diagnostic/planning question",
                scoring_guide={
                    "9-10": "Directly addresses diagnosis or planning with clear reasoning",
                    "6-8": "Addresses question but could be more systematic",
                    "3-5": "Partially relevant, lacks clear diagnostic approach",
                    "0-2": "Not relevant or admits inability to diagnose/plan"
                }
            ),
            ScoringCriteria(
                name="Diagnostic Accuracy",
                weight=0.4,
                description="Correctness of diagnostic reasoning and planning",
                scoring_guide={
                    "9-10": "Accurate diagnosis, comprehensive treatment plan",
                    "6-8": "Generally accurate but may miss some considerations",
                    "3-5": "Diagnostic errors or incomplete treatment planning",
                    "0-2": "Significant errors that could harm patient care"
                }
            ),
            ScoringCriteria(
                name="Systematic Approach",
                weight=0.3,
                description="Uses structured, systematic diagnostic/planning process",
                scoring_guide={
                    "9-10": "Highly systematic, considers all relevant factors",
                    "6-8": "Generally systematic but could be more thorough",
                    "3-5": "Unsystematic, jumps to conclusions",
                    "0-2": "No clear systematic approach"
                }
            )
        ]
    ),
    
    "Fit & Professional Maturity": CategoryRubric(
        category="Fit & Professional Maturity",
        criteria=[
            ScoringCriteria(
                name="Relevance",
                weight=0.3,
                description="How well answer addresses the behavioral/fit question",
                scoring_guide={
                    "9-10": "Directly addresses question with relevant personal examples",
                    "6-8": "Addresses question but examples could be stronger",
                    "3-5": "Vague response, weak or irrelevant examples",
                    "0-2": "Not relevant or avoids answering"
                }
            ),
            ScoringCriteria(
                name="Self-Awareness",
                weight=0.35,
                description="Shows insight into own strengths, weaknesses, growth",
                scoring_guide={
                    "9-10": "High self-awareness, honest reflection on growth",
                    "6-8": "Good self-awareness but could be more insightful",
                    "3-5": "Limited self-awareness or overly defensive",
                    "0-2": "No self-awareness or refuses to acknowledge weaknesses"
                }
            ),
            ScoringCriteria(
                name="Professional Maturity",
                weight=0.35,
                description="Demonstrates mature, professional approach to challenges",
                scoring_guide={
                    "9-10": "Highly mature, handles challenges professionally",
                    "6-8": "Generally mature but may show some immaturity",
                    "3-5": "Immature reactions or poor professional judgement",
                    "0-2": "Significantly immature or unprofessional"
                }
            )
        ]
    ),
    
    "Insight & Authenticity": CategoryRubric(
        category="Insight & Authenticity",
        criteria=[
            ScoringCriteria(
                name="Relevance",
                weight=0.3,
                description="How well answer addresses the reflective question",
                scoring_guide={
                    "9-10": "Directly addresses question with honest reflection",
                    "6-8": "Addresses question but could be more reflective",
                    "3-5": "Surface-level response, avoids real reflection",
                    "0-2": "Not relevant or refuses to engage authentically"
                }
            ),
            ScoringCriteria(
                name="Authenticity",
                weight=0.4,
                description="Shows genuine, honest self-reflection",
                scoring_guide={
                    "9-10": "Highly authentic, honest about strengths and weaknesses",
                    "6-8": "Generally authentic but somewhat guarded",
                    "3-5": "Overly rehearsed or gives 'correct' answers",
                    "0-2": "Inauthentic, dishonest, or completely guarded"
                }
            ),
            ScoringCriteria(
                name="Growth Orientation",
                weight=0.3,
                description="Shows willingness to learn and grow from experiences",
                scoring_guide={
                    "9-10": "Strong growth mindset, learns from all experiences",
                    "6-8": "Open to growth but may be somewhat fixed in thinking",
                    "3-5": "Limited growth orientation or defensive",
                    "0-2": "Fixed mindset, resistant to feedback or growth"
                }
            )
        ]
    )
}

# Default rubric for categories not explicitly defined
DEFAULT_RUBRIC = CategoryRubric(
    category="General",
    criteria=[
        ScoringCriteria(
            name="Relevance",
            weight=0.4,
            description="How well the answer addresses the question",
            scoring_guide={
                "9-10": "Directly and completely addresses the question",
                "6-8": "Addresses question but could be more focused",
                "3-5": "Partially addresses question with significant gaps",
                "0-2": "Does not address question or admits not knowing"
            }
        ),
        ScoringCriteria(
            name="Accuracy",
            weight=0.4,
            description="Correctness of information provided",
            scoring_guide={
                "9-10": "Highly accurate and demonstrates expertise",
                "6-8": "Generally accurate with minor errors",
                "3-5": "Contains significant errors or misconceptions",
                "0-2": "Incorrect or demonstrates lack of knowledge"
            }
        ),
        ScoringCriteria(
            name="Depth",
            weight=0.2,
            description="Level of detail and thoughtfulness",
            scoring_guide={
                "9-10": "Detailed, comprehensive response",
                "6-8": "Adequate detail but could elaborate",
                "3-5": "Superficial, lacks depth",
                "0-2": "Minimal substance"
            }
        )
    ]
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_rubric_for_category(category: str) -> CategoryRubric:
    """Get the scoring rubric for a specific category"""
    return INTERVIEW_RUBRICS.get(category, DEFAULT_RUBRIC)

def calculate_weighted_score(criterion_scores: Dict[str, float], criteria: List[ScoringCriteria]) -> float:
    """Calculate weighted average score from criterion scores"""
    total_weight = sum(c.weight for c in criteria)
    weighted_sum = sum(criterion_scores.get(c.name, 0) * c.weight for c in criteria)
    return round(weighted_sum / total_weight, 1) if total_weight > 0 else 0.0

def format_rubric_for_prompt(rubric: CategoryRubric) -> str:
    """Format rubric into a string for LLM prompt"""
    lines = [f"CATEGORY: {rubric.category}", ""]
    lines.append("Evaluate the candidate's response using these criteria:")
    lines.append("")
    
    for i, criterion in enumerate(rubric.criteria, 1):
        lines.append(f"{i}. {criterion.name} (Weight: {criterion.weight * 100:.0f}%)")
        lines.append(f"   {criterion.description}")
        lines.append("")
        lines.append("   Scoring Guide:")
        for score_range, description in criterion.scoring_guide.items():
            lines.append(f"   • {score_range}: {description}")
        lines.append("")
    
    return "\n".join(lines)