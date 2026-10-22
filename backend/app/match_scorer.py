import re
import numpy as np

# A comprehensive mapping of lowercase keywords and common aliases to standard display names
SKILL_MAP = {
    "react": "React",
    "angular": "Angular",
    "vue": "Vue.js",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "html": "HTML",
    "css": "CSS",
    "nodejs": "Node.js",
    "node": "Node.js",
    "express": "Express.js",
    "python": "Python",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "aws": "AWS",
    "azure": "Azure",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "git": "Git",
    "github": "GitHub",
    "agile": "Agile",
    "scrum": "Scrum",
    "jira": "Jira",
    "ci/cd": "CI/CD",
    "jenkins": "Jenkins",
    "graphql": "GraphQL",
    "rest": "REST APIs",
    "apis": "APIs",
    "api": "APIs",
    "testing": "Testing",
    "jest": "Jest",
    "cypress": "Cypress",
    "selenium": "Selenium",
    "java": "Java",
    "spring": "Spring Boot",
    "c++": "C++",
    "c#": "C#",
    "ruby": "Ruby",
    "rails": "Ruby on Rails",
    "php": "PHP",
    "laravel": "Laravel",
    "redux": "Redux",
    "sass": "Sass",
    "webpack": "Webpack",
    "microservices": "Microservices",
    "serverless": "Serverless",
    "linux": "Linux",
    "tableau": "Tableau",
    "powerbi": "Power BI",
    "excel": "Excel",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit-learn": "Scikit-Learn",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "machine learning": "Machine Learning",
    "data analytics": "Data Analytics",
    "analytics": "Data Analytics",
    "statistics": "Statistics",
    "product management": "Product Management",
    "devops": "DevOps",
    "cloud": "Cloud Computing",
    "security": "Security",
    "terraform": "Terraform",
    "monitoring": "Monitoring",
    "ansible": "Ansible",
    "figma": "Figma",
    "ui": "UI Design",
    "ux": "UX Design",
    "design": "Design",
    "data structures": "Data Structures",
    "algorithms": "Algorithms"
}

def extract_skills(text: str) -> dict:
    """
    Extracts skills from text and returns a dictionary of {normalized_skill_name: frequency_count}.
    Handles multi-word skills first to prevent substring matching conflicts.
    """
    if not text:
        return {}
        
    text_lower = text.lower()
    extracted = {}
    
    # Sort keys by length descending to match multi-word phrases (e.g. 'machine learning') before single words ('machine')
    for skill_kw in sorted(SKILL_MAP.keys(), key=len, reverse=True):
        escaped = re.escape(skill_kw)
        
        # Word boundary lookbehind/lookahead supporting special characters like C++, C#, CI/CD
        pattern = rf'(?<![a-zA-Z0-9_#+]){escaped}(?![a-zA-Z0-9_#+])'
        
        matches = re.findall(pattern, text_lower)
        if matches:
            normalized = SKILL_MAP[skill_kw]
            extracted[normalized] = extracted.get(normalized, 0) + len(matches)
            
            # Replace matched skill with spaces to avoid sub-matching (e.g. "learning" after matching "machine learning")
            text_lower = re.sub(pattern, " " * len(skill_kw), text_lower)
            
    return extracted

def calculate_tfidf_similarity(resume_text: str, jd_text: str) -> float:
    """
    Calculates TF-IDF cosine similarity between the resume text and the JD text.
    """
    if not resume_text.strip() or not jd_text.strip():
        return 0.0
        
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return float(sim[0][0])
    except Exception as e:
        print(f"Error in TF-IDF similarity calculation: {e}")
        return 0.0

# Singleton instance of FastEmbed TextEmbedding, lazily initialized
_embedding_model = None
_model_initialized = False

def get_embedding_model():
    global _embedding_model, _model_initialized
    if not _model_initialized:
        try:
            from fastembed import TextEmbedding
            # This is lightweight and will download a small model (~133MB BGE-small-en-v1.5) on first usage.
            _embedding_model = TextEmbedding()
        except Exception as e:
            print(f"Warning: Could not initialize fastembed model: {e}. Fallback logic will be used.")
            _embedding_model = None
        _model_initialized = True
    return _embedding_model

def calculate_fallback_semantic_similarity(resume_text: str, jd_text: str) -> float:
    """
    Computes a Jaccard skill-overlap score as a semantic fallback if fastembed is unavailable.
    """
    resume_skills = set(extract_skills(resume_text).keys())
    jd_skills = set(extract_skills(jd_text).keys())
    
    if not jd_skills:
        return 0.0
        
    intersection = resume_skills.intersection(jd_skills)
    union = resume_skills.union(jd_skills)
    
    if not union:
        return 0.0
        
    return float(len(intersection) / len(union))

def calculate_semantic_similarity(resume_text: str, jd_text: str) -> float:
    """
    Calculates dense sentence embeddings cosine similarity between resume and JD texts.
    """
    if not resume_text.strip() or not jd_text.strip():
        return 0.0
        
    model = get_embedding_model()
    if model is None:
        return calculate_fallback_semantic_similarity(resume_text, jd_text)
        
    try:
        # Generate embeddings
        embeddings = list(model.embed([resume_text, jd_text]))
        emb_resume = embeddings[0]
        emb_jd = embeddings[1]
        
        # Compute cosine similarity using numpy
        dot_prod = np.dot(emb_resume, emb_jd)
        norm_res = np.linalg.norm(emb_resume)
        norm_jd = np.linalg.norm(emb_jd)
        
        if norm_res == 0 or norm_jd == 0:
            return 0.0
            
        return float(dot_prod / (norm_res * norm_jd))
    except Exception as e:
        print(f"Error during semantic embedding matching: {e}. Falling back to Jaccard similarity.")
        return calculate_fallback_semantic_similarity(resume_text, jd_text)

def calculate_blend_match(resume_text: str, jd_text: str) -> dict:
    """
    Blends TF-IDF and semantic similarity scores, extracts matched and missing skills,
    and returns a match summary.
    """
    tfidf_sim = calculate_tfidf_similarity(resume_text, jd_text)
    semantic_sim = calculate_semantic_similarity(resume_text, jd_text)
    
    # Clip similarities to [0.0, 1.0]
    tfidf_pct = max(0.0, min(1.0, tfidf_sim)) * 100
    semantic_pct = max(0.0, min(1.0, semantic_sim)) * 100
    
    # Blend: 40% TF-IDF + 60% Semantic embedding similarity
    blend_pct = (0.4 * tfidf_pct) + (0.6 * semantic_pct)
    match_score = round(blend_pct)
    
    # Skills gap analysis
    jd_skills = extract_skills(jd_text)
    resume_skills = extract_skills(resume_text)
    
    matched_skills = []
    missing_skills = []
    
    for skill_name, freq in jd_skills.items():
        if skill_name in resume_skills:
            matched_skills.append({
                "name": skill_name,
                "frequency": freq
            })
        else:
            missing_skills.append({
                "name": skill_name,
                "frequency": freq
            })
            
    # Sort both lists by frequency descending
    matched_skills.sort(key=lambda x: x["frequency"], reverse=True)
    missing_skills.sort(key=lambda x: x["frequency"], reverse=True)
    
    return {
        "match_score": match_score,
        "tfidf_score": round(tfidf_pct),
        "semantic_score": round(semantic_pct),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills
    }
