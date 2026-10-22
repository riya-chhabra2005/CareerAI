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
    print("--- Starting Backend Interview Prep Plan Scorer & Database Tests ---")
    
    # 1. Register user
    rand_id = random.randint(10000, 99999)
    email = f"prep_tester_{rand_id}@example.com"
    password = "securepassword123"
    
    reg_data = {
        "name": "Prep Tester",
        "email": email,
        "password": password,
        "target_job_role": "Backend Developer",
        "experience_level": "1-3 years"
    }
    status, body = make_request("/auth/register", method="POST", data=reg_data)
    assert status == 201, f"Reg failed: {body}"
    token = body["access_token"]
    print("SUCCESS: Registered tester.")

    # 2. Upload a resume
    print("\n2. Testing Resume Upload...")
    resume_text = """
    John Doe - Backend Developer
    Email: john.doe@example.com
    Phone: (555) 123-4567
    
    Experience:
    • Software Engineer at TechCorp (June 2021 - Present)
      - Wrote REST APIs using Python and FastAPI.
      - Containerized services with Docker.
      - Maintained PostgreSQL databases.
      
    Skills:
    Python, FastAPI, SQL, PostgreSQL, Docker, Git
    """
    
    upload_data = {"pasted_text": resume_text}
    status, body = make_request("/resumes", method="POST", data=upload_data, token=token, is_multipart=True)
    assert status == 201, f"Expected 201, got {status}: {body}"
    resume_id = body["id"]
    print(f"SUCCESS: Resume uploaded. Assigned ID: {resume_id}")
    
    # 3. Create JD asking for Python, FastAPI, Docker, and Kubernetes
    print("\n3. Testing Job Description Creation...")
    jd_data = {
        "role_title": "Senior Python Backend Developer",
        "raw_jd_text": "Requirements: Strong experience in Python, FastAPI, Docker, and Kubernetes deployment."
    }
    status, body = make_request("/jd", method="POST", data=jd_data, token=token)
    assert status == 201, f"Expected 201, got {status}: {body}"
    jd_id = body["id"]
    print(f"SUCCESS: Job Description created. Assigned ID: {jd_id}")
    
    # 4. Generate Interview Plan POST /interview-plans
    print("\n4. Testing POST /interview-plans ...")
    plan_request_data = {
        "resume_id": resume_id,
        "jd_id": jd_id
    }
    status, body = make_request("/interview-plans", method="POST", data=plan_request_data, token=token)
    assert status == 201, f"Expected 201, got {status}: {body}"
    assert "id" in body, "id missing from response"
    assert "role_title" in body, "role_title missing from response"
    assert "questions" in body, "questions missing from response"
    
    plan_id = body["id"]
    questions = body["questions"]
    assert len(questions) == 9, f"Expected exactly 9 questions, got {len(questions)}"
    print(f"SUCCESS: Interview Plan created (ID: {plan_id}) with {len(questions)} questions.")

    for q in questions:
        assert q["plan_id"] == plan_id, "Plan ID link mismatched in question"
        assert q["type"] in ["technical", "coding", "hr"], f"Invalid question type: {q['type']}"
        assert q["difficulty"] in ["Easy", "Medium", "Hard"], f"Invalid question difficulty: {q['difficulty']}"
        assert len(q["topic_tag"]) > 0, "Topic tag cannot be empty"
        print(f" - [{q['type'].upper()}][{q['difficulty']}][{q['topic_tag']}]: {q['question_text']}")

    # 5. Fetch Latest Interview Plan GET /interview-plans/latest
    print("\n5. Testing GET /interview-plans/latest ...")
    status, body = make_request("/interview-plans/latest", method="GET", token=token)
    assert status == 200, f"Expected 200, got {status}: {body}"
    assert body["id"] == plan_id, "Fetched plan ID mismatched latest created plan"
    assert len(body["questions"]) == 9, "Questions list incomplete on fetch"
    print("SUCCESS: Fetched the latest plan and verified database persistence.")

    print("\n--- All Interview Prep Plan Tests Passed Successfully! ---")

if __name__ == "__main__":
    run_tests()
