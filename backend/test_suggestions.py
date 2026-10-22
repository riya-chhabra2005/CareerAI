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
    print("--- Starting Backend Suggestions Scorer & Verification Tests ---")
    
    # 1. Register user
    rand_id = random.randint(10000, 99999)
    email = f"sug_tester_{rand_id}@example.com"
    password = "securepassword123"
    
    reg_data = {
        "name": "Suggestions Tester",
        "email": email,
        "password": password,
        "target_job_role": "Backend Developer",
        "experience_level": "1-3 years"
    }
    status, body = make_request("/auth/register", method="POST", data=reg_data)
    assert status == 201, f"Reg failed: {body}"
    token = body["access_token"]
    print("SUCCESS: Registered tester.")

    # 2. Upload a resume with NO "Projects" and NO "Summary" section, with non-quantified experience bullet points,
    # and containing skills: Python, FastAPI, SQL.
    print("\n2. Testing Resume Upload...")
    resume_text = """
    John Doe - Backend Developer
    Email: john.doe@example.com
    Phone: (555) 123-4567
    
    Experience:
    • Software Engineer at TechCorp (June 2021 - Present)
      - Wrote microservices and designed database models.
      - Developed REST APIs using Python and FastAPI.
      - Fixed bugs in database schemas.
      
    Skills:
    Python, FastAPI, SQL
    """
    
    upload_data = {"pasted_text": resume_text}
    status, body = make_request("/resumes", method="POST", data=upload_data, token=token, is_multipart=True)
    assert status == 201, f"Expected 201, got {status}: {body}"
    resume_id = body["id"]
    print(f"SUCCESS: Resume uploaded. Assigned ID: {resume_id}")
    
    # 3. Create JD asking for Python, FastAPI, Docker, Kubernetes, and AWS
    print("\n3. Testing Job Description Creation...")
    jd_data = {
        "role_title": "Senior Python Backend Developer",
        "raw_jd_text": """
        Requirements:
        - Strong experience in Python, FastAPI.
        - Experience with Kubernetes cluster deployment.
        - Cloud experience with AWS is required.
        - Knowledge of Docker and Docker Compose.
        """
    }
    status, body = make_request("/jd", method="POST", data=jd_data, token=token)
    assert status == 201, f"Expected 201, got {status}: {body}"
    jd_id = body["id"]
    print(f"SUCCESS: Job Description created. Assigned ID: {jd_id}")
    
    # 4. Test Suggestions Endpoint POST /resumes/{id}/suggestions
    print("\n4. Testing POST /resumes/{id}/suggestions ...")
    suggestions_request_data = {"jd_id": jd_id}
    status, body = make_request(f"/resumes/{resume_id}/suggestions", method="POST", data=suggestions_request_data, token=token)
    
    assert status == 200, f"Expected 200, got {status}: {body}"
    assert "suggestions" in body, "suggestions list missing"
    suggestions = body["suggestions"]
    assert len(suggestions) > 0, "No suggestions returned"
    
    print(f"SUCCESS: Suggestions generated ({len(suggestions)} suggestions):")
    for idx, sug in enumerate(suggestions):
        print(f"\nSuggestion #{idx+1}:")
        print(f" - Category: {sug['category']}")
        print(f" - Explanation: {sug['explanation']}")
        if sug.get('example_rewrite'):
            print(f" - Example Rewrite: {sug['example_rewrite']}")
        print(f" - Requires Verification: {sug['requires_verification']}")
        if sug.get('unverified_skills'):
            print(f" - Unverified Skills: {sug['unverified_skills']}")
            
    # Verify that missing section suggestions were triggered
    categories = [s["category"] for s in suggestions]
    assert "Missing Sections" in categories, "Missing Sections category should be present"
    assert "Quantify Your Impact" in categories, "Quantify Your Impact category should be present"
    assert "Wording" in categories, "Wording category should be present"
    
    # Verify anti-hallucination flagging:
    # A suggestion to add 'Kubernetes' or 'AWS' (which are missing from the resume text)
    # should have requires_verification = True.
    verification_needed_found = False
    for sug in suggestions:
        if sug["requires_verification"]:
            verification_needed_found = True
            # The unverified skills should correspond to the missing ones in JD
            for unv_skill in sug["unverified_skills"]:
                assert unv_skill in ["Kubernetes", "AWS", "Docker", "Cloud Computing"], f"Unexpected unverified skill flagged: {unv_skill}"
                
    assert verification_needed_found, "Anti-hallucination check failed to flag unverified skills (Kubernetes or AWS)."
    print("\nSUCCESS: Anti-hallucination verification checks correctly identified unverified skills.")
    
    print("\n--- All Suggestions Engine Tests Passed Successfully! ---")

if __name__ == "__main__":
    run_tests()
