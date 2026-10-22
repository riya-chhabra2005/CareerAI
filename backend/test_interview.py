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
    print("--- Starting Backend Mock Interview Portal & Voice Transcription Tests ---")
    
    # 1. Register user
    rand_id = random.randint(10000, 99999)
    email = f"int_tester_{rand_id}@example.com"
    password = "securepassword123"
    
    reg_data = {
        "name": "Interview Tester",
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
    resume_text = "Python and FastAPI developer. Wrote database code and maintained git repos."
    status, body = make_request("/resumes", method="POST", data={"pasted_text": resume_text}, token=token, is_multipart=True)
    assert status == 201, "Resume upload failed"
    resume_id = body["id"]
    
    # 3. Create JD
    jd_data = {"role_title": "Backend Developer", "raw_jd_text": "Requirements: Python, FastAPI, Docker, SQL."}
    status, body = make_request("/jd", method="POST", data=jd_data, token=token)
    assert status == 201, "JD creation failed"
    jd_id = body["id"]

    # 4. Generate Interview Plan
    plan_request_data = {"resume_id": resume_id, "jd_id": jd_id}
    status, body = make_request("/interview-plans", method="POST", data=plan_request_data, token=token)
    assert status == 201, "Plan creation failed"
    plan_id = body["id"]
    print("SUCCESS: Plan and questions generated.")

    # 5. Start Interview Session POST /interviews/sessions
    print("\n5. Testing POST /interviews/sessions ...")
    status, body = make_request("/interviews/sessions", method="POST", data={"plan_id": plan_id}, token=token)
    assert status == 201, f"Expected 201, got {status}: {body}"
    session_id = body["id"]
    print(f"SUCCESS: Interview session started. Session ID: {session_id}")

    # 6. Loop through questions to answer them
    print("\n6. Simulating Mock Interview Session flow...")
    completed = False
    question_index = 0
    dummy_wav_bytes = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x40\x1f\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00"

    while not completed:
        # Fetch next question
        status, body = make_request(f"/interviews/sessions/{session_id}/next", method="GET", token=token)
        assert status == 200, f"Failed next question fetch: {body}"
        
        completed = body["completed"]
        if completed:
            print("SUCCESS: Session completed condition hit.")
            break
            
        question = body["question"]
        qid = question["id"]
        question_index += 1
        print(f"\n Answering Question #{question_index} (ID: {qid}, Tag: {question['topic_tag']}):")
        print(f"   Q: {question['question_text']}")

        # Submit answer (odd questions: voice reply, even questions: text reply)
        if question_index % 2 == 1:
            # Voice reply upload simulation
            answer_data = {
                "question_id": qid,
                "input_type": "voice"
            }
            files = {
                "file": ("test_voice_reply.wav", dummy_wav_bytes, "audio/wav")
            }
            status, ans_body = make_request(f"/interviews/{session_id}/answers", method="POST", data=answer_data, token=token, is_multipart=True, files=files)
            assert status == 200, f"Voice submission failed: {ans_body}"
            assert ans_body["input_type"] == "voice", "Input type mismatched in DB answer"
            assert "audio_path" in ans_body and ans_body["audio_path"] is not None, "Audio path not set for voice answer"
            print(f"   A (VOICE): [Transcript] {ans_body['answer_text']}")
        else:
            # Text reply submission
            answer_data = {
                "question_id": qid,
                "input_type": "text",
                "answer_text": f"This is my typed response to the question regarding {question['topic_tag']} under test guidelines."
            }
            status, ans_body = make_request(f"/interviews/{session_id}/answers", method="POST", data=answer_data, token=token, is_multipart=True)
            assert status == 200, f"Text submission failed: {ans_body}"
            assert ans_body["input_type"] == "text", "Input type mismatched in DB answer"
            print(f"   A (TEXT): {ans_body['answer_text']}")

    # 7. Check that the session is marked completed in DB
    print("\n7. Verifying final session status...")
    status, body = make_request(f"/interviews/sessions/{session_id}/next", method="GET", token=token)
    assert status == 200, "Final check failed"
    assert body["completed"] is True, "Session did not auto-complete on final question submit"
    
    print("\n--- All Mock Interview Portal & Voice Tests Passed Successfully! ---")

if __name__ == "__main__":
    run_tests()
