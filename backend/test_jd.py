import json
import urllib.request
import urllib.error
import random

BASE_URL = "http://127.0.0.1:8000"

def make_request(path, method="GET", data=None, token=None, is_multipart=False, files=None):
    url = f"{BASE_URL}{path}"
    
    if is_multipart:
        # Prepare multipart/form-data for upload_resume endpoint
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
    print("--- Starting Backend Job Description & ATS Scoring Tests ---")
    
    # 1. Register user to get JWT
    rand_id = random.randint(10000, 99999)
    email = f"ats_tester_{rand_id}@example.com"
    password = "securepassword123"
    
    reg_data = {
        "name": "ATS Tester",
        "email": email,
        "password": password,
        "target_job_role": "Backend Developer",
        "experience_level": "1-3 years"
    }
    status, body = make_request("/auth/register", method="POST", data=reg_data)
    assert status == 201, f"Reg failed: {body}"
    token = body["access_token"]
    print("SUCCESS: Logged in and registered tester.")

    # 2. Test Resume Upload (pasted text)
    print("\n2. Testing Resume Upload (Pasted Text)...")
    resume_text = """
    John Doe - Backend Developer
    Email: john.doe@example.com
    Phone: (555) 123-4567
    
    Summary:
    Experienced Software Engineer specializing in backend systems.
    
    Experience:
    • Senior Software Engineer at TechCorp (June 2021 - Present)
      - Built REST APIs using Python and FastAPI.
      - Containerized services with Docker.
      - Maintained PostgreSQL databases.
    • Developer at SoftCo (January 2019 - May 2021)
      - Wrote microservices and designed database models.
      
    Education:
    Bachelor of Science in Computer Science - University of Technology (2018)
    
    Skills:
    Python, FastAPI, SQL, PostgreSQL, Docker, Git, REST, Microservices, API
    """
    
    upload_data = {"pasted_text": resume_text}
    status, body = make_request("/resumes", method="POST", data=upload_data, token=token, is_multipart=True)
    assert status == 201, f"Expected 201, got {status}: {body}"
    assert body["filename"] == "pasted_resume.txt", "Filename mismatch"
    resume_id = body["id"]
    print(f"SUCCESS: Resume uploaded. Assigned ID: {resume_id}")
    
    # 3. Test Job Description Creation
    print("\n3. Testing Job Description Creation (POST /jd)...")
    jd_data = {
        "role_title": "Senior Python Backend Developer",
        "raw_jd_text": "We are looking for a Senior Backend Developer. Requirements: Strong experience in Python, FastAPI, Docker, and PostgreSQL databases. Experience in microservices and Kubernetes is a plus."
    }
    status, body = make_request("/jd", method="POST", data=jd_data, token=token)
    assert status == 201, f"Expected 201, got {status}: {body}"
    jd_id = body["id"]
    print(f"SUCCESS: Job Description created. Assigned ID: {jd_id}")
    
    # 4. Test ATS Score Computation against the JD
    print("\n4. Testing ATS Scoring (GET /resumes/{id}/ats-score?jd_id={jd_id})...")
    status, body = make_request(f"/resumes/{resume_id}/ats-score?jd_id={jd_id}", method="GET", token=token)
    assert status == 200, f"Expected 200, got {status}: {body}"
    assert "score" in body, "Score missing"
    assert "details" in body, "Details missing"
    assert len(body["feedback_list"]) > 0 or body["score"] >= 80, "Score details incomplete"
    
    print(f"SUCCESS: ATS Score computed: {body['score']}/100")
    print(f"Details Breakdown:")
    for section, score_info in body["details"].items():
        print(f" - {section.capitalize()}: {score_info['score']}/{score_info['max']} (Feedback Count: {len(score_info['feedback'])})")
    
    print(f"Action Feedback List:")
    for feedback in body["feedback_list"]:
        print(f" - {feedback}")

    # 5. Test Job Description Parsing (POST /jd/parse)
    print("\n5. Testing Job Description Parsing and Role Extraction...")
    txt_jd_content = "Job Title: React Frontend developer\nDescription: Build user interfaces using React and Tailwind."
    files = {
        "file": ("test_jd.txt", txt_jd_content.encode("utf-8"), "text/plain")
    }
    status, body = make_request("/jd/parse", method="POST", token=token, is_multipart=True, files=files)
    assert status == 200, f"Expected 200, got {status}: {body}"
    assert body["role_title"] == "React Frontend developer", f"Role title extraction failed: expected 'React Frontend developer', got '{body['role_title']}'"
    assert "React and Tailwind" in body["raw_jd_text"], "Text parsing failed"
    print("SUCCESS: TXT Job Description parsed and role title extracted successfully.")

    txt_jd_content_fallback = "Frontend Software Engineer\nWe are looking for someone to build React apps."
    files_fallback = {
        "file": ("test_jd_fallback.txt", txt_jd_content_fallback.encode("utf-8"), "text/plain")
    }
    status, body = make_request("/jd/parse", method="POST", token=token, is_multipart=True, files=files_fallback)
    assert status == 200, f"Expected 200, got {status}: {body}"
    assert body["role_title"] == "Frontend Software Engineer", f"Fallback Role title extraction failed: expected 'Frontend Software Engineer', got '{body['role_title']}'"
    print("SUCCESS: Fallback Role title extracted successfully.")
        
    print("\n--- All Job Description & ATS Scoring Tests Passed! ---")

if __name__ == "__main__":
    run_tests()
