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
    print("--- Starting Backend Answer Evaluation Tests ---")
    
    # 1. Register user
    rand_id = random.randint(10000, 99999)
    email = f"eval_tester_{rand_id}@example.com"
    password = "securepassword123"
    
    reg_data = {
        "name": "Evaluation Tester",
        "email": email,
        "password": password,
        "target_job_role": "Backend Developer",
        "experience_level": "1-3 years"
    }
    status, body = make_request("/auth/register", method="POST", data=reg_data)
    assert status == 201
    token = body["access_token"]

    # 2. Upload a resume
    resume_text = "Python and FastAPI developer. Wrote database code and maintained git repos."
    status, body = make_request("/resumes", method="POST", data={"pasted_text": resume_text}, token=token, is_multipart=True)
    resume_id = body["id"]
    
    # 3. Create JD
    jd_data = {"role_title": "Backend Developer", "raw_jd_text": "Requirements: Python, FastAPI, Docker, SQL."}
    status, body = make_request("/jd", method="POST", data=jd_data, token=token)
    jd_id = body["id"]

    # 4. Generate Interview Plan
    status, body = make_request("/interview-plans", method="POST", data={"resume_id": resume_id, "jd_id": jd_id}, token=token)
    plan_id = body["id"]

    # 5. Start Session
    status, body = make_request("/interviews/sessions", method="POST", data={"plan_id": plan_id}, token=token)
    session_id = body["id"]
    print("SUCCESS: Session created.")

    # 6. Get first question & submit short answer
    print("\n6. Submitting a brief/weak answer to Question 1...")
    status, body = make_request(f"/interviews/sessions/{session_id}/next", method="GET", token=token)
    q1 = body["question"]
    
    ans1_data = {
        "question_id": q1["id"],
        "input_type": "text",
        "answer_text": "I don't know."
    }
    status, ans1_body = make_request(f"/interviews/{session_id}/answers", method="POST", data=ans1_data, token=token, is_multipart=True)
    ans1_id = ans1_body["id"]

    # Evaluate Q1 Answer
    status, eval1_body = make_request(f"/answers/{ans1_id}/evaluate", method="POST", token=token)
    assert status == 201, f"Evaluation Q1 failed: {eval1_body}"
    assert eval1_body["overall_score"] < 50, f"Expected low score for brief response, got: {eval1_body['overall_score']}"
    print(f"SUCCESS: Q1 brief answer evaluated. Score: {eval1_body['overall_score']}")
    print(f" - Gaps list: {eval1_body['gaps']}")

    # 7. Get second question & submit detailed answer
    print("\n7. Submitting a detailed/strong answer to Question 2...")
    status, body = make_request(f"/interviews/sessions/{session_id}/next", method="GET", token=token)
    q2 = body["question"]
    topic = q2["topic_tag"]

    ans2_data = {
        "question_id": q2["id"],
        "input_type": "text",
        "answer_text": f"Regarding {topic}, I have implemented robust production setups for it. In TechCorp, I configured {topic} parameters to increase execution performance, handling state management and edge cases successfully under test scopes."
    }
    status, ans2_body = make_request(f"/interviews/{session_id}/answers", method="POST", data=ans2_data, token=token, is_multipart=True)
    ans2_id = ans2_body["id"]

    # Evaluate Q2 Answer
    status, eval2_body = make_request(f"/answers/{ans2_id}/evaluate", method="POST", token=token)
    assert status == 201, f"Evaluation Q2 failed: {eval2_body}"
    assert eval2_body["overall_score"] > 70, f"Expected higher score for detailed response, got: {eval2_body['overall_score']}"
    assert eval2_body["overall_score"] > eval1_body["overall_score"], "Detailed answer did not score higher than weak answer"
    print(f"SUCCESS: Q2 detailed answer evaluated. Score: {eval2_body['overall_score']}")
    print(f" - Strengths list: {eval2_body['strengths']}")
    print(f" - collapsible model_answer length: {len(eval2_body['model_answer'])} chars")
    
    print("\n--- All Answer Evaluation Tests Passed Successfully! ---")

if __name__ == "__main__":
    run_tests()
