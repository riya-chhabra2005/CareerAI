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
    print("--- Starting Backend Study Plan & Checklist Progression Tests ---")
    
    # 1. Register user
    rand_id = random.randint(10000, 99999)
    email = f"study_tester_{rand_id}@example.com"
    password = "securepassword123"
    
    reg_data = {
        "name": "Study Tester",
        "email": email,
        "password": password,
        "target_job_role": "Backend Engineer",
        "experience_level": "1-3 years"
    }
    status, body = make_request("/auth/register", method="POST", data=reg_data)
    assert status == 201
    token = body["access_token"]

    # 2. Upload a resume
    status, body = make_request("/resumes", method="POST", data={"pasted_text": "Experienced Python developer."}, token=token, is_multipart=True)
    resume_id = body["id"]
    
    # 3. Create JD
    status, body = make_request("/jd", method="POST", data={"role_title": "Backend Python Engineer", "raw_jd_text": "Python backend developer."}, token=token)
    jd_id = body["id"]

    # 4. Generate Study Plan POST /study-plans (14 days)
    print("\n4. Testing POST /study-plans (14 days)...")
    status, body = make_request("/study-plans", method="POST", data={"duration": 14}, token=token)
    assert status == 201, f"Expected 201, got {status}: {body}"
    assert body["duration"] == 14, "Duration mismatched"
    assert len(body["days"]) == 14, f"Expected exactly 14 day records, got {len(body['days'])}"
    
    plan_id = body["id"]
    day_1 = body["days"][0]
    day_1_id = day_1["id"]
    day_1_items = day_1["action_items"]
    assert len(day_1_items) == 3, "Day 1 must contain exactly 3 action items"
    assert len(day_1["completed_items"]) == 0, "Initial completed items list must be empty"
    print(f"SUCCESS: Created 14-day study plan. Day 1: {day_1['theme']}")

    # 5. Check off task PUT /study-plan-days/{day_1_id}
    print("\n5. Testing PUT /study-plan-days/{id} ...")
    checked_item = day_1_items[0]
    update_data = {"completed_items": [checked_item]}
    status, body = make_request(f"/study-plan-days/{day_1_id}", method="PUT", data=update_data, token=token)
    assert status == 200, f"Expected 200, got {status}: {body}"
    assert checked_item in body["completed_items"], "Checked item missing from completed_items response"
    print(f"SUCCESS: Checked off task: '{checked_item}'")

    # 6. Fetch Latest study plan GET /study-plans/latest
    print("\n6. Testing GET /study-plans/latest ...")
    status, body = make_request("/study-plans/latest", method="GET", token=token)
    assert status == 200
    print("Latest Plan Response:", json.dumps(body, indent=2))
    assert body["id"] == plan_id, "Latest plan ID mismatch"
    assert checked_item in body["days"][0]["completed_items"], "Checked items not persisted in database query"
    print("SUCCESS: Study plan details and checklist states successfully verified!")

    print("\n--- All Personalized Study Plan Tests Passed Successfully! ---")

if __name__ == "__main__":
    run_tests()
