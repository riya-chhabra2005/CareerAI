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
    print("--- Starting Backend Progress Dashboard Aggregator Tests ---")
    
    # 1. Register user
    rand_id = random.randint(10000, 99999)
    email = f"dash_tester_{rand_id}@example.com"
    password = "securepassword123"
    
    reg_data = {
        "name": "Dashboard Tester",
        "email": email,
        "password": password,
        "target_job_role": "Backend Lead",
        "experience_level": "5+ years"
    }
    status, body = make_request("/auth/register", method="POST", data=reg_data)
    assert status == 201
    token = body["access_token"]

    # 2. Upload a resume
    resume_text = "Experienced Backend Python Engineer. Wrote REST API microservices and containerized with Docker. Used Git."
    status, body = make_request("/resumes", method="POST", data={"pasted_text": resume_text}, token=token, is_multipart=True)
    resume_id = body["id"]
    
    # 3. Create JD
    jd_data = {"role_title": "Backend Python Lead", "raw_jd_text": "Requirements: Python, Docker, Git, Kubernetes, SQL."}
    status, body = make_request("/jd", method="POST", data=jd_data, token=token)
    jd_id = body["id"]

    # 4. Generate Prep Plan
    status, body = make_request("/interview-plans", method="POST", data={"resume_id": resume_id, "jd_id": jd_id}, token=token)
    plan_id = body["id"]

    # 5. Start Session
    status, body = make_request("/interviews/sessions", method="POST", data={"plan_id": plan_id}, token=token)
    session_id = body["id"]

    # 6. Submit brief answer (Q1)
    status, body = make_request(f"/interviews/sessions/{session_id}/next", method="GET", token=token)
    q1 = body["question"]
    ans1_data = {"question_id": q1["id"], "input_type": "text", "answer_text": "I don't know."}
    status, ans1 = make_request(f"/interviews/{session_id}/answers", method="POST", data=ans1_data, token=token, is_multipart=True)
    make_request(f"/answers/{ans1['id']}/evaluate", method="POST", token=token)

    # 7. Submit detailed answer (Q2)
    status, body = make_request(f"/interviews/sessions/{session_id}/next", method="GET", token=token)
    q2 = body["question"]
    ans2_data = {"question_id": q2["id"], "input_type": "text", "answer_text": f"Regarding {q2['topic_tag']}, I built production-grade modules in TechCorp using FastAPI, Docker, and Git to deploy scalable features, tracking unit test metrics at 95% coverage."}
    status, ans2 = make_request(f"/interviews/{session_id}/answers", method="POST", data=ans2_data, token=token, is_multipart=True)
    make_request(f"/answers/{ans2['id']}/evaluate", method="POST", token=token)
    
    # 8. Hit GET /dashboard
    print("\n8. Testing GET /dashboard endpoint...")
    status, body = make_request("/dashboard", method="GET", token=token)
    assert status == 200, f"Dashboard retrieval failed: {body}"
    
    # Assert correctness of aggregated fields
    assert body["latest_ats_score"] is not None, "Latest ATS score is null"
    assert body["latest_match_score"] is not None, "Latest Match score is null"
    assert body["questions_attempted"] == 2, f"Attempted questions count mismatched, got: {body['questions_attempted']}"
    assert body["avg_interview_score"] is not None, "Average interview score is null"
    assert len(body["score_history"]) == 2, "Score history length incorrect"
    assert len(body["topic_performance"]) == 2, "Topic performance length incorrect"
    assert len(body["weak_topics"]) == 1, "Weak topics count incorrect"
    assert q1["topic_tag"] in body["weak_topics"], "Weak topic tag missing from results"
    assert len(body["recent_sessions"]) == 1, "Recent session count incorrect"
    
    print("\nSUCCESS: Aggregated progress dashboard metrics verified:")
    print(f" - ATS Score: {body['latest_ats_score']}")
    print(f" - Match Score: {body['latest_match_score']}")
    print(f" - Rolling Avg Score: {body['avg_interview_score']}%")
    print(f" - Score History: {body['score_history']}")
    print(f" - Topic Performance: {body['topic_performance']}")
    print(f" - Weak Topics: {body['weak_topics']}")
    print(f" - Recent Sessions: {body['recent_sessions']}")
    
    print("\n--- All Progress Dashboard Analytics Tests Passed Successfully! ---")

if __name__ == "__main__":
    run_tests()
