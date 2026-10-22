import json
import urllib.request
import urllib.error
import random

BASE_URL = "http://127.0.0.1:8000"

def make_request(path, method="GET", data=None, token=None, is_multipart=False, files=None):
    url = f"{BASE_URL}{path}"
    
    if is_multipart:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = bytearray()
        
        if files:
            for field_name, (filename, content_bytes, content_type) in files.items():
                body.extend(f"--{boundary}\r\n".encode("utf-8"))
                body.extend(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"))
                body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
                body.extend(content_bytes)
                body.extend(b"\r\n")
                
        if data:
            for key, val in data.items():
                body.extend(f"--{boundary}\r\n".encode("utf-8"))
                body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
                body.extend(str(val).encode("utf-8"))
                body.extend(b"\r\n")
                
        body.extend(f"--{boundary}--\r\n".encode("utf-8"))
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body))
        }
        req_data = bytes(body)
    else:
        headers = {"Content-Type": "application/json"}
        req_data = json.dumps(data).encode("utf-8") if data else None
        
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            err_body = e.reason
        return e.code, err_body

def run_tests():
    print("--- Starting Backend Match Score & Skill Gap Analysis Tests ---")
    
    # 1. Register user to get JWT
    rand_id = random.randint(10000, 99999)
    email = f"match_tester_{rand_id}@example.com"
    password = "securepassword123"
    
    reg_data = {
        "name": "Match Tester",
        "email": email,
        "password": password,
        "target_job_role": "Backend Developer",
        "experience_level": "1-3 years"
    }
    status, body = make_request("/auth/register", method="POST", data=reg_data)
    assert status == 201, f"Reg failed: {body}"
    token = body["access_token"]
    print("SUCCESS: Logged in and registered tester.")

    # 2. Upload Resume with specific skills (Python, FastAPI, SQL, Docker)
    print("\n2. Testing Resume Upload...")
    resume_text = """
    John Doe - Backend Developer
    Email: john.doe@example.com
    Phone: (555) 123-4567
    
    Summary:
    Experienced Software Engineer specializing in Python backend systems.
    
    Experience:
    • Senior Software Engineer at TechCorp (June 2021 - Present)
      - Wrote REST APIs using Python and FastAPI.
      - Containerized services with Docker.
      - Maintained PostgreSQL databases and wrote complex SQL queries.
      
    Skills:
    Python, FastAPI, SQL, PostgreSQL, Docker, Git, REST APIs, APIs
    """
    
    upload_data = {"pasted_text": resume_text}
    status, body = make_request("/resumes", method="POST", data=upload_data, token=token, is_multipart=True)
    assert status == 201, f"Expected 201, got {status}: {body}"
    resume_id = body["id"]
    print(f"SUCCESS: Resume uploaded. Assigned ID: {resume_id}")
    
    # 3. Create JD asking for Python, FastAPI, Docker, and some missing skills (Kubernetes, AWS, CI/CD)
    print("\n3. Testing Job Description Creation...")
    jd_data = {
        "role_title": "Senior Python Backend Developer",
        "raw_jd_text": """
        Requirements:
        - Strong experience in Python, FastAPI, Docker.
        - Experience with Kubernetes cluster deployment.
        - Cloud experience with AWS is required.
        - Knowledge of CI/CD pipelines (Jenkins or GitHub Actions).
        - Familiarity with SQL and microservices.
        """
    }
    status, body = make_request("/jd", method="POST", data=jd_data, token=token)
    assert status == 201, f"Expected 201, got {status}: {body}"
    jd_id = body["id"]
    print(f"SUCCESS: Job Description created. Assigned ID: {jd_id}")
    
    # 4. Test Match Endpoint POST /resumes/{id}/match
    print("\n4. Testing POST /resumes/{id}/match ...")
    match_request_data = {"jd_id": jd_id}
    status, body = make_request(f"/resumes/{resume_id}/match", method="POST", data=match_request_data, token=token)
    
    assert status == 200, f"Expected 200, got {status}: {body}"
    assert "match_score" in body, "match_score missing"
    assert "tfidf_score" in body, "tfidf_score missing"
    assert "semantic_score" in body, "semantic_score missing"
    assert "matched_skills" in body, "matched_skills missing"
    assert "missing_skills" in body, "missing_skills missing"
    
    print(f"SUCCESS: Match scores calculated:")
    print(f" - TF-IDF Cosine Similarity: {body['tfidf_score']}%")
    print(f" - Semantic Embedding Similarity: {body['semantic_score']}%")
    print(f" - Blended Match Score: {body['match_score']}%")
    
    print("\nMatched Skills:")
    for skill in body["matched_skills"]:
        print(f" - {skill['name']} (JD Frequency: {skill['frequency']})")
        
    print("\nMissing Skills:")
    for skill in body["missing_skills"]:
        print(f" - {skill['name']} (JD Frequency: {skill['frequency']})")
        
    # Verify sorting
    for i in range(len(body["matched_skills"]) - 1):
        assert body["matched_skills"][i]["frequency"] >= body["matched_skills"][i+1]["frequency"], "Matched skills not sorted"
    for i in range(len(body["missing_skills"]) - 1):
        assert body["missing_skills"][i]["frequency"] >= body["missing_skills"][i+1]["frequency"], "Missing skills not sorted"
        
    # Verify specific matches/missing
    matched_names = [s["name"] for s in body["matched_skills"]]
    missing_names = [s["name"] for s in body["missing_skills"]]
    
    assert "Python" in matched_names, "Python should be matched"
    assert "FastAPI" in matched_names, "FastAPI should be matched"
    assert "Docker" in matched_names, "Docker should be matched"
    
    assert "Kubernetes" in missing_names, "Kubernetes should be missing"
    assert "AWS" in missing_names, "AWS should be missing"
    assert "CI/CD" in missing_names, "CI/CD should be missing"
    
    print("\n--- All Match Score & Skill Gap Analysis Tests Passed Successfully! ---")

if __name__ == "__main__":
    run_tests()
