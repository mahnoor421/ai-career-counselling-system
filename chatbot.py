"""
AI Career Counselor - Chatbot Module

This module handles all chatbot interactions for the AI Career Counseling application.
It manages user conversations, career recommendations, and follow-up queries.

Author: Mahnoor
Date: 2024
Version: 2.0
"""

import json
import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from career_engine import recommend_careers


# =====================================
# LOGGING CONFIGURATION
# =====================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# =====================================
# CONSTANTS
# =====================================

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")

JSON_FILES = [
    "medical.json",
    "computer_science.json",
    "engineering.json",
    "business.json",
    "sciences.json",
    "social_sciences.json",
    "arts_and_design.json",
    "other_professional_fields.json"
]

GREETING_KEYWORDS = ["hi", "hello", "hey", "salam", "assalamualaikum", "start"]

CHAT_STEPS = {
    0: "initial",
    1: "education",
    2: "interests",
    3: "skills",
    4: "goals",
    5: "results"
}


# =====================================
# LOAD CAREER DATABASE
# =====================================

def load_career_database() -> Dict[str, Dict[str, Any]]:
    """
    Load all career JSON files from the data folder.
    
    Returns:
        Dict: Career database with career names as keys
        
    Raises:
        FileNotFoundError: If data folder doesn't exist
    """
    career_database = {}
    
    if not os.path.exists(DATA_FOLDER):
        logger.warning(f"Data folder not found at {DATA_FOLDER}")
        return career_database
    
    for file_name in JSON_FILES:
        file_path = os.path.join(DATA_FOLDER, file_name)
        
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if isinstance(data, dict):
                        career_database.update(data)
                        logger.info(f"✓ Loaded {file_name}: {len(data)} careers")
                    else:
                        logger.warning(f"Invalid format in {file_name}")
            else:
                logger.warning(f"File not found: {file_name}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading {file_name}: {str(e)}")
    
    logger.info(f"✓ Total careers loaded: {len(career_database)}")
    return career_database


# Load the database
CAREER_DATABASE = load_career_database()


# =====================================
# BUILD CAREER KEYWORDS INDEX
# =====================================

def build_career_keywords() -> Dict[str, List[str]]:
    """
    Create a keyword index for faster career searches.
    
    Returns:
        Dict: Career names mapped to their keywords
    """
    career_keywords = {}
    
    for career_name, details in CAREER_DATABASE.items():
        if not isinstance(details, dict):
            continue
        
        # Collect all relevant keywords
        keywords = [
            career_name.lower(),
            *[str(s).lower() for s in details.get("skills", [])],
            *[str(i).lower() for i in details.get("interests", [])],
            *[str(e).lower() for e in details.get("education", [])],
            *[str(s).lower() for s in details.get("required_skills", [])],
            *[str(r).lower() for r in details.get("roadmap", [])],
        ]
        
        # Remove duplicates and store
        career_keywords[career_name] = list(set(keywords))
    
    logger.info(f"✓ Built keyword index for {len(career_keywords)} careers")
    return career_keywords


CAREER_KEYWORDS = build_career_keywords()


# =====================================
# HELPER FUNCTIONS
# =====================================

def get_career_detail(career_name: str, key: str) -> List[Any]:
    """
    Safely retrieve a career detail.
    
    Args:
        career_name: Name of the career
        key: Detail key to retrieve (e.g., 'skills', 'education')
        
    Returns:
        List: The requested detail or empty list if not found
    """
    try:
        details = CAREER_DATABASE.get(career_name, {})
        
        if not isinstance(details, dict):
            return []
        
        value = details.get(key, [])
        return value if isinstance(value, list) else []
        
    except Exception as e:
        logger.error(f"Error getting career detail: {str(e)}")
        return []


def initialize_chat_session(session: Dict) -> Dict:
    """
    Initialize chat session if not exists.
    
    Args:
        session: Flask session object
        
    Returns:
        Dict: Chat session data
    """
    if "career_chat" not in session:
        session["career_chat"] = {
            "step": 0,
            "education": "",
            "interests": "",
            "skills": "",
            "goal": "",
            "last_career": "",
            "recommended": [],
            "conversation_history": []
        }
    
    return session["career_chat"]


def save_conversation(chat: Dict, user_msg: str, bot_response: str):
    """Save conversation for history."""
    if "conversation_history" not in chat:
        chat["conversation_history"] = []
    
    chat["conversation_history"].append({
        "user": user_msg,
        "bot": bot_response
    })


# =====================================
# RESPONSE TEMPLATES
# =====================================

class ChatResponses:
    """Contains all chat response templates."""
    
    GREETING = """
👋 <b>Welcome to AI Career Counselor!</b>

I'm here to help you discover your perfect career path by understanding your:
• Education background
• Interests and passions
• Current skills
• Career preferences

Let's explore 70+ career paths across different fields:

💻 Computer Science | 🩺 Medical | ⚙️ Engineering | 📊 Business
⚖️ Law | 🎨 Arts & Design | 🔬 Sciences | 🌾 Agriculture
📚 Education | 💼 Commerce

<b>Let's begin! 🚀</b>

━━━━━━━━━━━━━━━━━━━━━━

<b>Question 1 of 4:</b> What is your current education level?

<i>Examples: Matric, ICS, FSc Pre-Engineering, BSCS, BBA, MBBS, LLB</i>
"""

    EDUCATION_RECORDED = lambda msg: f"""
✅ <b>Education Recorded!</b>

Your Education: <b>{msg.upper()}</b>

━━━━━━━━━━━━━━━━━━━━━━

<b>Question 2 of 4:</b> Which subjects or fields interest you most?

<i>Examples: Artificial Intelligence, Programming, Medicine, Biology, Finance, Law, Psychology, Design, Architecture, Journalism</i>

<i>Tip: You can enter multiple interests separated by commas</i>
"""

    INTERESTS_RECORDED = lambda msg: f"""
✅ <b>Interests Recorded!</b>

Your Interests: <b>{msg.title()}</b>

━━━━━━━━━━━━━━━━━━━━━━

<b>Question 3 of 4:</b> What skills do you already have?

<i>Examples: Python, Java, Communication, Leadership, Research, Graphic Design, Problem Solving, Creativity, Public Speaking</i>

<i>Tip: Enter multiple skills separated by commas</i>
"""

    SKILLS_RECORDED = lambda msg: f"""
✅ <b>Skills Recorded!</b>

Your Skills: <b>{msg.title()}</b>

━━━━━━━━━━━━━━━━━━━━━━

<b>Question 4 of 4:</b> What type of career do you prefer?

<i>Examples: High Salary, Government Job, Research, Business, Freelancing, Remote Work, Entrepreneurship, Teaching, Healthcare, Creative Field</i>
"""

    PROCESSING = "🔄 <b>Processing your profile...</b> Please wait a moment..."
    
    NO_INPUT = "⚠️ Please type something so I can help you."
    
    NO_RESULTS = """
❌ <b>No Suitable Career Found</b>

It seems we couldn't find matching careers with your inputs.

Please try:
• Providing more skills
• Exploring different interests
• Sharing your career goals

💡 Tip: You can also ask "Tell me about [Career Name]" to explore specific careers!
"""

    NO_COMPARE = """
⚠️ <b>Need Two Careers to Compare</b>

Please mention two different careers you'd like to compare.

<b>Example:</b> "Compare Data Scientist and AI Engineer"
"""
    
    FALLBACK = """
🤖 <b>I'm Here to Help!</b>

I can assist you with:

✅ Career information & descriptions
✅ Required skills & qualifications
✅ Educational pathways
✅ Career roadmaps
✅ Certifications needed
✅ Future scope & opportunities
✅ Career comparisons
✅ Skill gap analysis

<b>Try asking:</b>
• "Tell me about Data Scientist"
• "What skills do I need?"
• "Compare AI Engineer and Software Engineer"
• "Show me the roadmap"
• "What are the certifications?"
• "What's the future scope?"

━━━━━━━━━━━━━━━━━━━━━━

Type <b>'hi'</b> to start the career discovery process! 🚀
"""


# =====================================
# MAIN CHATBOT FUNCTION
# =====================================

def get_bot_response(message: str, session: Dict) -> str:
    """
    Generate chatbot response based on user message.
    
    Args:
        message: User's input message
        session: Flask session object
        
    Returns:
        str: Chatbot's response
    """
    try:
        # Clean and normalize input
        message = message.strip().lower()
        
        # Check for empty input
        if not message:
            return ChatResponses.NO_INPUT
        
        # Initialize or retrieve chat session
        chat = initialize_chat_session(session)
        session["career_chat"] = chat
        
        logger.info(f"User message: {message} | Chat step: {chat['step']}")
        
        # =====================================
        # STEP 0: GREETING
        # =====================================
        
        if message in GREETING_KEYWORDS or chat["step"] == 0:
            chat["step"] = 1
            session["career_chat"] = chat
            return ChatResponses.GREETING
        
        # =====================================
        # STEP 1: EDUCATION
        # =====================================
        
        if chat["step"] == 1:
            chat["education"] = message
            chat["step"] = 2
            session["career_chat"] = chat
            return ChatResponses.EDUCATION_RECORDED(message)
        
        # =====================================
        # STEP 2: INTERESTS
        # =====================================
        
        if chat["step"] == 2:
            chat["interests"] = message
            chat["step"] = 3
            session["career_chat"] = chat
            return ChatResponses.INTERESTS_RECORDED(message)
        
        # =====================================
        # STEP 3: SKILLS
        # =====================================
        
        if chat["step"] == 3:
            chat["skills"] = message
            chat["step"] = 4
            session["career_chat"] = chat
            return ChatResponses.SKILLS_RECORDED(message)
        
        # =====================================
        # STEP 4: GOALS & RECOMMENDATIONS
        # =====================================
        
        if chat["step"] == 4:
            chat["goal"] = message
            
            # Get recommendations
            results = recommend_careers(
                chat["education"],
                chat["skills"],
                chat["interests"]
            )
            
            # Process results
            chat["recommended"] = []
            for item in results:
                if isinstance(item, tuple):
                    chat["recommended"].append(item[0])
                elif isinstance(item, dict):
                    chat["recommended"].append(
                        item.get("career", item.get("name", ""))
                    )
            
            if chat["recommended"]:
                chat["last_career"] = chat["recommended"][0]
            
            session["career_chat"] = chat
            
            # Build response
            if results:
                response = build_recommendations_response(chat, results)
                return response
            else:
                return ChatResponses.NO_RESULTS
        
        # =====================================
        # FOLLOW-UP: CAREER COMPARISON
        # =====================================
        
        if "compare" in message or "comparison" in message:
            return handle_career_comparison(message)
        
        # =====================================
        # FOLLOW-UP: SKILL GAP ANALYSIS
        # =====================================
        
        last_career = chat.get("last_career", "")
        
        if last_career and last_career in CAREER_DATABASE:
            details = CAREER_DATABASE[last_career]
            
            if "gap" in message or "missing" in message or "improve" in message:
                return handle_skill_gap_analysis(chat, last_career, details)
            
            # =====================================
            # FOLLOW-UP: SKILLS
            # =====================================
            
            if "skill" in message:
                return handle_skills_query(last_career, details)
            
            # =====================================
            # FOLLOW-UP: DEGREE/EDUCATION
            # =====================================
            
            if "degree" in message or "education" in message or "qualification" in message:
                return handle_education_query(last_career, details)
            
            # =====================================
            # FOLLOW-UP: ROADMAP
            # =====================================
            
            if "roadmap" in message or "steps" in message:
                return handle_roadmap_query(last_career, details)
            
            # =====================================
            # FOLLOW-UP: CERTIFICATIONS
            # =====================================
            
            if "certificate" in message or "certification" in message:
                return handle_certifications_query(last_career, details)
            
            # =====================================
            # FOLLOW-UP: FUTURE SCOPE
            # =====================================
            
            if "future" in message or "scope" in message or "jobs" in message or "salary" in message:
                return handle_future_scope_query(last_career, details)
        
        # =====================================
        # DIRECT CAREER SEARCH
        # =====================================
        
        response = search_career_in_database(message, chat, session)
        if response:
            return response
        
        # =====================================
        # FALLBACK RESPONSE
        # =====================================
        
        return ChatResponses.FALLBACK
        
    except Exception as e:
        logger.error(f"Error in get_bot_response: {str(e)}")
        return "❌ An error occurred. Please try again."


# =====================================
# HELPER FUNCTIONS FOR RESPONSES
# =====================================

def build_recommendations_response(chat: Dict, results: List) -> str:
    """Build career recommendations response."""
    response = """
🎯 <b>Your AI Career Recommendations</b>

Based on your education, interests, and skills, here are your best matches:

━━━━━━━━━━━━━━━━━━━━━━

"""
    
    for idx, item in enumerate(results[:5], 1):
        if isinstance(item, tuple):
            career, score = item[0], item[1]
        else:
            career = item.get("career", item.get("name", "Unknown"))
            score = item.get("score", item.get("match_percentage", 0))
        
        response += f"""
<b>{idx}. ⭐ {career}</b>
📊 Match Score: <b>{score}%</b>

"""
    
    response += f"""
━━━━━━━━━━━━━━━━━━━━━━

💬 <b>You can now ask:</b>
• What skills does <b>{chat["last_career"]}</b> require?
• What's the degree required?
• Show me the roadmap
• What certifications do I need?
• What's the future scope?

📌 Type a career name to explore it in detail! 🚀
"""
    return response


def handle_career_comparison(message: str) -> str:
    """Handle career comparison requests."""
    careers_found = []
    
    for career_name in CAREER_DATABASE.keys():
        if career_name.lower() in message:
            careers_found.append(career_name)
    
    if len(careers_found) < 2:
        return ChatResponses.NO_COMPARE
    
    response = """
📊 <b>Career Comparison</b>

━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for career in careers_found[:2]:
        details = CAREER_DATABASE[career]
        
        response += f"""

<b>🎯 {career}</b>

<b>🛠 Skills:</b>
"""
        
        skills = details.get("skills", details.get("required_skills", []))
        for skill in skills[:5]:
            response += f"• {skill}\n"
        
        response += f"""
<b>🎓 Education:</b>
"""
        
        education = details.get("education", [])
        for edu in education[:3]:
            response += f"• {edu}\n"
        
        response += f"""
<b>💰 Salary Range:</b> {details.get("salary_range", "Not specified")}

━━━━━━━━━━━━━━━━━━━━━━
"""
    
    response += """

💡 <b>You can ask:</b>
• Which one has higher salary?
• Which is better for me?
• What's the roadmap for each?
"""
    
    return response


def handle_skill_gap_analysis(chat: Dict, career: str, details: Dict) -> str:
    """Handle skill gap analysis."""
    user_skills = [s.strip().lower() for s in chat.get("skills", "").split(",")]
    required_skills = details.get("skills", details.get("required_skills", []))
    
    matched = []
    missing = []
    
    for skill in required_skills:
        if any(user_skill in skill.lower() or skill.lower() in user_skill for user_skill in user_skills):
            matched.append(skill)
        else:
            missing.append(skill)
    
    response = f"""
📊 <b>Skill Gap Analysis for {career}</b>

━━━━━━━━━━━━━━━━━━━━━━

✅ <b>Your Current Skills ({len(matched)})</b>

"""
    
    if matched:
        for skill in matched:
            response += f"✔️ {skill}\n"
    else:
        response += "No matching skills found\n"
    
    response += f"""

❌ <b>Skills You Need to Learn ({len(missing)})</b>

"""
    
    if missing:
        for skill in missing:
            response += f"• {skill}\n"
    else:
        response += "✨ Excellent! You have all required skills!\n"
    
    response += """

━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>Recommendation:</b>
Focus on learning the missing skills to increase your career opportunities!
"""
    
    return response


def handle_skills_query(career: str, details: Dict) -> str:
    """Handle skills query."""
    skills = details.get("skills", details.get("required_skills", []))
    
    response = f"""
🛠 <b>Skills Required for {career}</b>

"""
    
    if skills:
        for skill in skills:
            response += f"• {skill}\n"
    else:
        response += "Not available"
    
    response += """

━━━━━━━━━━━━━━━━━━━━━━

<b>Would you like to know:</b>
• Degree required
• Career roadmap
• Certifications needed
• Future scope
"""
    
    return response


def handle_education_query(career: str, details: Dict) -> str:
    """Handle education query."""
    education = details.get("education", [])
    
    response = f"""
🎓 <b>Education Required for {career}</b>

"""
    
    if education:
        for item in education:
            response += f"• {item}\n"
    else:
        response += "Not available"
    
    response += """

━━━━━━━━━━━━━━━━━━━━━━

<b>You can also ask:</b>
• Skills required
• Career roadmap
• Future opportunities
"""
    
    return response


def handle_roadmap_query(career: str, details: Dict) -> str:
    """Handle roadmap query."""
    roadmap = details.get("roadmap", [])
    
    response = f"""
🛣 <b>Career Roadmap for {career}</b>

"""
    
    if roadmap:
        for idx, step in enumerate(roadmap, 1):
            response += f"{idx}. {step}\n"
    else:
        response += "Not available"
    
    response += """

━━━━━━━━━━━━━━━━━━━━━━

<b>Would you like to know:</b>
• Certifications needed
• Future scope
• Salary expectations
"""
    
    return response


def handle_certifications_query(career: str, details: Dict) -> str:
    """Handle certifications query."""
    certs = details.get("certifications", details.get("required_skills", []))
    
    response = f"""
🏆 <b>Recommended Certifications for {career}</b>

"""
    
    if certs:
        for cert in certs:
            response += f"• {cert}\n"
    else:
        response += "No certifications available"
    
    return response


def handle_future_scope_query(career: str, details: Dict) -> str:
    """Handle future scope query."""
    future = details.get(
        "future_scope",
        f"{career} has excellent career opportunities both nationally and internationally."
    )
    
    response = f"""
📈 <b>Future Scope of {career}</b>

{future}

━━━━━━━━━━━━━━━━━━━━━━

💡 <b>Would you like to:</b>
• Explore another career?
• Compare with similar careers?
• Analyze skill gaps?
"""
    
    return response


def search_career_in_database(message: str, chat: Dict, session: Dict) -> Optional[str]:
    """Search for a career in the database."""
    for career_name, details in CAREER_DATABASE.items():
        if not isinstance(details, dict):
            continue
        
        if career_name.lower() in message:
            chat["last_career"] = career_name
            session["career_chat"] = chat
            
            education = details.get("education", [])
            skills = details.get("skills", details.get("required_skills", []))
            description = details.get("description", "No description available")
            
            response = f"""
🎯 <b>{career_name}</b>

📝 {description}

━━━━━━━━━━━━━━━━━━━━━━

🎓 <b>Education Required</b>

"""
            
            if education:
                for item in education:
                    response += f"• {item}\n"
            else:
                response += "Not specified\n"
            
            response += """

🛠 <b>Key Skills</b>

"""
            
            if skills:
                for skill in skills[:5]:
                    response += f"• {skill}\n"
            else:
                response += "Not specified\n"
            
            response += """

━━━━━━━━━━━━━━━━━━━━━━

💬 <b>You can now ask:</b>
• What skills are required?
• What's the degree?
• Show me the roadmap
• What certifications?
• What's the future scope?
• Analyze my skill gap

📌 Type another career name to explore more! 🚀
"""
            
            return response
    
    return None

