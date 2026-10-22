import re

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", 
    "about", "against", "between", "into", "through", "during", "before", "after", 
    "above", "below", "of", "to", "from", "up", "down", "in", "out", "on", "off", "over", 
    "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", 
    "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", 
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will", 
    "just", "should", "now", "is", "are", "was", "were", "be", "been", "being", "have", 
    "has", "had", "having", "do", "does", "did", "doing", "would", "could", "about", 
    "required", "preferred", "experience", "skills", "ability", "duties", "responsibilities",
    "must", "work", "job", "candidate", "role", "team", "working", "using", "knowledge"
}

TECH_KEYWORDS = {
    "react", "angular", "vue", "javascript", "typescript", "html", "css", "nodejs", "node", 
    "express", "python", "django", "flask", "fastapi", "sql", "postgresql", "mysql", "mongodb", 
    "aws", "azure", "docker", "kubernetes", "git", "github", "agile", "scrum", "jira", "ci/cd", 
    "jenkins", "graphql", "rest", "apis", "api", "testing", "jest", "cypress", "selenium", 
    "java", "spring", "c++", "c#", "ruby", "rails", "php", "laravel", "redux", "sass", "webpack", 
    "microservices", "serverless", "linux", "tableau", "powerbi", "excel", "pandas", "numpy", 
    "scikit-learn", "tensorflow", "pytorch", "machine", "learning", "data", "analytics", 
    "statistics", "product", "management", "devops", "cloud", "security", "terraform", 
    "monitoring", "ansible", "figma", "ui", "ux", "design"
}

ROLE_DEFAULT_KEYWORDS = {
    "frontend": ["react", "javascript", "typescript", "html", "css", "redux", "git", "testing", "api", "webpack"],
    "backend": ["python", "fastapi", "sql", "postgresql", "docker", "node", "api", "git", "microservices", "ci/cd"],
    "fullstack": ["react", "node", "javascript", "python", "sql", "docker", "git", "api", "css", "testing"],
    "data": ["python", "sql", "pandas", "numpy", "tableau", "excel", "statistics", "machine learning", "powerbi", "git"],
    "devops": ["docker", "kubernetes", "aws", "ci/cd", "linux", "terraform", "git", "jenkins", "security", "monitoring"],
    "software": ["java", "python", "c++", "sql", "git", "data structures", "algorithms", "testing", "api", "agile"]
}

def clean_words(text: str) -> set:
    # Remove punctuation, lowercase, and tokenize
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    return set(words)

def calculate_ats_score(resume_text: str, jd_text: str = "", target_role: str = "") -> dict:
    feedback_list = []
    
    # 1. Section Headings Analysis (Max: 20)
    heading_score = 0
    heading_feedback = []
    
    sections = {
        "Experience/Work History": ["experience", "work history", "employment", "professional history", "positions held"],
        "Education": ["education", "academic", "university", "degree", "schooling"],
        "Skills": ["skills", "technologies", "expertise", "core competencies", "technical skills"],
        "Projects": ["projects", "personal projects", "portfolio", "key projects"],
        "Summary/Objective": ["summary", "objective", "profile", "about me", "professional summary"]
    }
    
    resume_lower = resume_text.lower()
    for section_name, keywords in sections.items():
        found = False
        for kw in keywords:
            # Check for heading (usually starting a line or surrounded by spacing)
            pattern = r'(?:^|\n)\s*' + re.escape(kw) + r'\b'
            if re.search(pattern, resume_lower):
                found = True
                break
        if found:
            heading_score += 4
        else:
            heading_feedback.append(f"Missing a dedicated '{section_name.split('/')[0]}' section heading.")
            
    if heading_feedback:
        feedback_list.extend(heading_feedback)

    # 2. Bullet Points vs Dense Paragraphs (Max: 15)
    structure_score = 15
    structure_feedback = []
    
    # Count bullets: •, *, -, ▪, ◦
    bullets = re.findall(r'(?:^|\n)\s*(?:[•*▪◦]|\-\s+)', resume_text)
    bullet_count = len(bullets)
    
    if bullet_count >= 8:
        structure_score = 15
    elif bullet_count >= 4:
        structure_score = 8
        structure_feedback.append("Limited bullet points found. Use bullet points to list accomplishments rather than long sentences.")
    else:
        structure_score = 3
        structure_feedback.append("Very few or no bullet points detected. Dense paragraphs are highly discouraged by ATS systems.")
        
    if structure_feedback:
        feedback_list.extend(structure_feedback)

    # 3. Machine Readable Contact Info (Max: 15)
    contact_score = 0
    contact_feedback = []
    
    # Email check
    email_match = re.search(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', resume_text)
    if email_match:
        contact_score += 7
    else:
        contact_feedback.append("No machine-readable email address detected. Ensure your email is not in an image format.")
        
    # Phone check (basic check for standard digits structure)
    phone_match = re.search(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', resume_text)
    if phone_match:
        contact_score += 8
    else:
        contact_feedback.append("No machine-readable phone number detected. Ensure your contact info is text-based.")
        
    if contact_feedback:
        feedback_list.extend(contact_feedback)

    # 4. Date Formatting Consistency (Max: 15)
    dates_score = 15
    dates_feedback = []
    
    # Find any date structures: e.g. 2021, 05/2021, May 2021, Present
    date_patterns = [
        r'\b(?:19|20)\d{2}\b', # YYYY
        r'\b\d{1,2}/\d{2,4}\b', # MM/YY or MM/YYYY
        r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b', # Month YYYY
        r'\bpresent\b' # Present
    ]
    
    found_dates_count = 0
    for pattern in date_patterns:
        matches = re.findall(pattern, resume_lower)
        found_dates_count += len(matches)
        
    if found_dates_count >= 2:
        dates_score = 15
    elif found_dates_count == 1:
        dates_score = 7
        dates_feedback.append("Only one date marker found. Ensure all experience entries specify a clear timeframe (e.g. Month YYYY).")
    else:
        dates_score = 0
        dates_feedback.append("No clear date formatting detected (e.g., MM/YYYY or Month YYYY). ATS parsers cannot calculate your duration of experience.")
        
    if dates_feedback:
        feedback_list.extend(dates_feedback)

    # 5. Complex Layout / Columns Check (Max: 15)
    layout_score = 15
    layout_feedback = []
    
    # Check for consecutive spaces inside lines indicating multi-columns (e.g. 4+ spaces)
    lines_with_columns = 0
    for line in resume_text.split('\n'):
        if re.search(r'\s{5,}', line.strip()) and not line.strip().startswith(('•', '*', '-')):
            lines_with_columns += 1
            
    # Check for pipe delimiters representing tables
    pipes_count = len(re.findall(r'\|', resume_text))
    
    if lines_with_columns > 4 or pipes_count > 3:
        layout_score = 6
        layout_feedback.append("Detected possible multi-column formatting, sidebars, or tables. Simple layouts ensure parsing reliability.")
        
    if layout_feedback:
        feedback_list.extend(layout_feedback)

    # 6. Keyword Alignment Analysis (Max: 20)
    keyword_score = 20
    keyword_feedback = []
    missing_keywords = []
    
    resume_words = clean_words(resume_text)
    
    # Identify target keywords to look for
    target_keywords = set()
    if jd_text:
        jd_words = clean_words(jd_text)
        # Intersection of JD words and technical term bank
        target_keywords = jd_words.intersection(TECH_KEYWORDS)
        
        # If very few tech keywords found in JD, fall back to frequent nouns in JD
        if len(target_keywords) < 5:
            filtered_jd = [w for w in jd_words if w not in STOP_WORDS and len(w) > 2]
            # Take top 10 unique words
            target_keywords = set(filtered_jd[:10])
    else:
        # Fall back to target role defaults
        role_key = "software"
        target_role_lower = target_role.lower()
        for key in ROLE_DEFAULT_KEYWORDS:
            if key in target_role_lower:
                role_key = key
                break
        target_keywords = set(ROLE_DEFAULT_KEYWORDS[role_key])
        
    if target_keywords:
        matched_keywords = target_keywords.intersection(resume_words)
        match_count = len(matched_keywords)
        total_count = len(target_keywords)
        
        pct = (match_count / total_count) if total_count > 0 else 1.0
        keyword_score = round(20 * pct)
        
        missing = list(target_keywords - resume_words)
        if missing:
            suggest = [f"'{m}'" for m in missing[:5]]
            missing_keywords = missing[:5]
            keyword_feedback.append(f"Consider integrating these missing keyword terms: {', '.join(suggest)}.")
    else:
        keyword_score = 20
        
    if keyword_feedback:
        feedback_list.extend(keyword_feedback)

    # Final overall score
    overall_score = heading_score + structure_score + contact_score + dates_score + layout_score + keyword_score
    overall_score = min(max(overall_score, 0), 100)
    
    return {
        "score": overall_score,
        "details": {
            "headings": {
                "score": heading_score,
                "max": 20,
                "feedback": heading_feedback
            },
            "structure": {
                "score": structure_score,
                "max": 15,
                "feedback": structure_feedback
            },
            "contact": {
                "score": contact_score,
                "max": 15,
                "feedback": contact_feedback
            },
            "dates": {
                "score": dates_score,
                "max": 15,
                "feedback": dates_feedback
            },
            "layout": {
                "score": layout_score,
                "max": 15,
                "feedback": layout_feedback
            },
            "keywords": {
                "score": keyword_score,
                "max": 20,
                "feedback": keyword_feedback
            }
        },
        "feedback_list": feedback_list
    }
