"""
AI Career Counselor - Career Engine Module

This module handles career recommendations based on user profile.
Uses intelligent scoring algorithm to match users with suitable careers.

Author: Mahnoor
Date: 2024
Version: 2.0
"""

import json
import os
import logging
from typing import Dict, List, Tuple, Any, Optional


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")

JSON_FILES = [
    "computer_science.json",
    "medical.json",
    "engineering.json",
    "business.json",
    "sciences.json",
    "social_sciences.json",
    "arts_and_design.json",
    "other_professional_fields.json"
]

EDUCATION_MAP = {
    "matric": ["General Career Options", "Engineering", "Business"],
    "ics": [
        "Computer Science",
        "Software Engineer",
        "AI Engineer",
        "Data Scientist",
        "Cybersecurity Specialist",
        "Information Technology",
        "Mobile App Developer",
        "Web Developer"
    ],
    "fsc pre-engineering": [
        "Engineering",
        "Computer Science",
        "AI Engineer",
        "Mechanical Engineer",
        "Electrical Engineer",
        "Civil Engineer",
        "Data Scientist"
    ],
    "fsc pre-medical": [
        "Doctor (General Practitioner)",
        "Nurse",
        "Pharmacist",
        "Physiotherapist",
        "Dentist",
        "Healthcare",
        "Health Sciences"
    ],
    "i.com": [
        "Business Analyst",
        "Financial Analyst",
        "Marketing Manager",
        "Business",
        "Finance",
        "Accounting",
        "HR Manager"
    ],
    "fa": [
        "Teacher/Educator",
        "Lawyer",
        "Psychologist",
        "Arts",
        "Law",
        "Social Sciences",
        "Psychology"
    ],
    "bscs": [
        "Software Engineer",
        "Data Scientist",
        "AI Engineer",
        "Mobile App Developer",
        "Web Developer",
        "Database Administrator",
        "Cybersecurity Specialist"
    ],
    "bba": [
        "Business Analyst",
        "Marketing Manager",
        "HR Manager",
        "Financial Analyst",
        "Business"
    ],
    "llb": ["Lawyer", "Legal Services"],
    "mbbs": ["Doctor (General Practitioner)", "Healthcare", "Surgery"],
    "engineering": [
        "Software Engineer",
        "Mechanical Engineer",
        "Electrical Engineer",
        "Civil Engineer",
        "Data Scientist"
    ],
    "other": ["Teacher/Educator", "Business Analyst", "Research Scientist"]
}

SCORING_WEIGHTS = {
    "education": 30,
    "skills": 40,
    "interests": 30
}


def load_career_database() -> Dict[str, Dict[str, Any]]:
    """Load all career JSON files from the data folder."""
    career_database = {}
    
    if not os.path.exists(DATA_FOLDER):
        logger.warning(f"Data folder not found at {DATA_FOLDER}")
        return career_database
    
    loaded_count = 0
    
    for filename in JSON_FILES:
        filepath = os.path.join(DATA_FOLDER, filename)
        
        try:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    
                    if isinstance(data, dict):
                        career_database.update(data)
                        loaded_count += len(data)
                        logger.info(f"Loaded {filename}: {len(data)} careers")
                    else:
                        logger.warning(f"Invalid format in {filename}")
            else:
                logger.warning(f"File not found: {filename}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {filename}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading {filename}: {str(e)}")
    
    logger.info(f"Successfully loaded {loaded_count} careers total")
    return career_database


CAREER_DATABASE = load_career_database()


def normalize_education(education: str) -> str:
    """Normalize education input."""
    education = education.lower().strip()
    
    for key in EDUCATION_MAP.keys():
        if education == key or key in education:
            return key
    
    return education


def parse_user_input(input_string: str) -> List[str]:
    """Parse comma-separated user input."""
    items = [
        item.strip().lower()
        for item in input_string.split(",")
        if item.strip()
    ]
    return items if items else ["general"]


def calculate_match_score(career_skills: List[str], user_skills: List[str]) -> Tuple[int, int]:
    """Calculate skill match score."""
    if not career_skills:
        return 0, 1
        
    matched = 0
    
    for user_skill in user_skills:
        for career_skill in career_skills:
            skill_lower = str(career_skill).lower()
            user_skill_lower = str(user_skill).lower()
            
            if (user_skill_lower in skill_lower or 
                skill_lower in user_skill_lower or
                len(user_skill_lower) > 3 and user_skill_lower in skill_lower):
                matched += 1
                break
    
    return matched, len(career_skills)


def get_education_bonus_careers(education: str) -> List[str]:
    """Get careers related to education level."""
    normalized_edu = normalize_education(education)
    return EDUCATION_MAP.get(normalized_edu, [])


def score_career(
    career_name: str,
    career_details: Dict[str, Any],
    user_education: str,
    user_skills: List[str],
    user_interests: List[str]
) -> int:
    """Calculate compatibility score for a career."""
    score = 0.0
    
    try:
        career_education = career_details.get("education", [])
        edu_bonus_careers = get_education_bonus_careers(user_education)
        
        education_score = 0
        
        if career_education:
            for edu in career_education:
                if user_education.lower() in edu.lower():
                    education_score = SCORING_WEIGHTS["education"]
                    break
        
        if education_score == 0:
            for category in edu_bonus_careers:
                if category.lower() in career_name.lower():
                    education_score = SCORING_WEIGHTS["education"] * 0.8
                    break
            
            if education_score == 0 and edu_bonus_careers:
                education_score = SCORING_WEIGHTS["education"] * 0.4
        
        score += education_score
        
        career_skills = career_details.get("skills", [])
        if career_skills and user_skills:
            matched, total = calculate_match_score(career_skills, user_skills)
            if total > 0:
                skills_percentage = matched / total
                skills_score = skills_percentage * SCORING_WEIGHTS["skills"]
                score += skills_score
            else:
                score += SCORING_WEIGHTS["skills"] * 0.3
        elif not user_skills:
            score += SCORING_WEIGHTS["skills"] * 0.2
        
        career_interests = career_details.get("interests", [])
        
        career_name_lower = career_name.lower()
        career_desc = str(career_details.get("description", "")).lower()
        
        if career_interests or user_interests:
            matched_interests = 0
            total_interests = len(career_interests) if career_interests else 1
            
            for user_interest in user_interests:
                if career_interests:
                    for career_interest in career_interests:
                        interest_lower = str(career_interest).lower()
                        if (user_interest in interest_lower or 
                            interest_lower in user_interest):
                            matched_interests += 1
                            break
                
                if user_interest in career_name_lower:
                    matched_interests += 1
                    break
                
                if user_interest in career_desc:
                    matched_interests += 1
                    break
            
            if matched_interests > 0:
                interests_score = (matched_interests / max(len(user_interests), 1)) * SCORING_WEIGHTS["interests"]
                score += min(interests_score, SCORING_WEIGHTS["interests"])
            else:
                score += SCORING_WEIGHTS["interests"] * 0.2
        
        return max(0, min(100, round(score)))
        
    except Exception as e:
        logger.error(f"Error scoring career {career_name}: {str(e)}")
        return 0


def recommend_careers(
    education: str,
    skills: str,
    interests: str,
    top_n: int = 15
) -> List[Tuple[str, int]]:
    """Generate career recommendations based on user profile."""
    try:
        if not CAREER_DATABASE:
            logger.error("Career database is empty!")
            return []
        
        logger.info(f"Generating recommendations for: Education={education}, Skills={skills}, Interests={interests}")
        
        normalized_education = normalize_education(education)
        parsed_skills = parse_user_input(skills)
        parsed_interests = parse_user_input(interests)
        
        logger.info(f"Parsed: Education={normalized_education}, Skills={parsed_skills}, Interests={parsed_interests}")
        
        scores = {}
        
        for career_name, career_details in CAREER_DATABASE.items():
            if not isinstance(career_details, dict):
                continue
            
            score = score_career(
                career_name,
                career_details,
                normalized_education,
                parsed_skills,
                parsed_interests
            )
            
            if score > 0:
                scores[career_name] = score
        
        if not scores:
            logger.warning("No careers scored above 0!")
            for career_name in list(CAREER_DATABASE.keys())[:20]:
                scores[career_name] = 50
        
        ranked = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        results = ranked[:top_n]
        
        logger.info(f"Generated {len(results)} recommendations")
        for career, score in results[:5]:
            logger.info(f"  - {career}: {score}%")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in recommend_careers: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def get_career_details(career_name: str) -> Any:
    """Get detailed information about a career."""
    for db_name, db_details in CAREER_DATABASE.items():
        if db_name.lower() == career_name.lower():
            return db_details
    return None


def search_careers(query: str) -> List[str]:
    """Search for careers matching query."""
    query = query.lower().strip()
    matches = []
    
    for career_name in CAREER_DATABASE.keys():
        if query in career_name.lower():
            matches.append(career_name)
    
    return matches


def get_all_careers() -> List[str]:
    """Get list of all available careers."""
    return list(CAREER_DATABASE.keys())


def initialize_engine() -> bool:
    """Initialize the career recommendation engine."""
    try:
        if not CAREER_DATABASE:
            logger.error("Career database is empty!")
            return False
        
        logger.info("Career engine initialized successfully")
        logger.info(f"Total careers: {len(CAREER_DATABASE)}")
        logger.info(f"Education options: {len(EDUCATION_MAP)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing career engine: {str(e)}")
        return False


if __name__ != "__main__":
    initialize_engine()