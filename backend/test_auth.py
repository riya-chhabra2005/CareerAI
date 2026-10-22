import json
import urllib.request
import urllib.error
import random

BASE_URL = "http://127.0.0.1:8000"

def make_request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    req_data = json.dumps(data).encode("utf-8") if data else None
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
    print("--- Starting Backend Auth Verification Tests ---")
    
    # Generate unique email for testing
    rand_id = random.randint(1000, 9999)
    email = f"test_{rand_id}@example.com"
    password = "securepassword123"
    name = "Test User"
    target_job_role = "Software Engineer"
    experience_level = "1–3 years"
    
    # 1. Register a new user
    print("\n1. Testing User Registration (POST /auth/register)...")
    reg_data = {
        "name": name,
        "email": email,
        "password": password,
        "target_job_role": target_job_role,
        "experience_level": experience_level
    }
    status, body = make_request("/auth/register", method="POST", data=reg_data)
    assert status == 201, f"Expected 201, got {status}: {body}"
    assert "access_token" in body, "access_token missing in response"
    assert body["user"]["email"] == email, "Email mismatch"
    token = body["access_token"]
    print("SUCCESS: Registered user and obtained JWT.")
    
    # 2. Attempt duplicate registration
    print("\n2. Testing Duplicate Registration Prevention...")
    status, body = make_request("/auth/register", method="POST", data=reg_data)
    assert status == 400, f"Expected 400, got {status}: {body}"
    print("SUCCESS: Duplicate registration correctly blocked with status 400.")
    
    # 3. Login with valid credentials
    print("\n3. Testing User Login (POST /auth/login)...")
    login_data = {"email": email, "password": password}
    status, body = make_request("/auth/login", method="POST", data=login_data)
    assert status == 200, f"Expected 200, got {status}: {body}"
    assert "access_token" in body, "access_token missing in response"
    login_token = body["access_token"]
    print("SUCCESS: Logged in and obtained JWT.")
    
    # 4. Login with invalid password
    print("\n4. Testing Login with Invalid Password...")
    bad_login_data = {"email": email, "password": "wrongpassword"}
    status, body = make_request("/auth/login", method="POST", data=bad_login_data)
    assert status == 401, f"Expected 401, got {status}: {body}"
    print("SUCCESS: Invalid credentials correctly blocked with status 401.")
    
    # 5. Access profile page without token (should fail)
    print("\n5. Testing Profile Access without JWT (GET /auth/me)...")
    status, body = make_request("/auth/me", method="GET")
    assert status == 403, f"Expected 403 (unauthorized/no credentials), got {status}: {body}"
    print("SUCCESS: Anonymous request blocked with status 403.")
    
    # 6. Access profile page with valid token (should succeed)
    print("\n6. Testing Profile Access with valid JWT...")
    status, body = make_request("/auth/me", method="GET", token=login_token)
    assert status == 200, f"Expected 200, got {status}: {body}"
    assert body["email"] == email, "Profile email mismatch"
    print(f"SUCCESS: Profile retrieved successfully. Name: {body['name']}, Role: {body['target_job_role']}, Experience: {body['experience_level']}")
    
    # 7. Update profile details
    print("\n7. Testing Profile Update (PUT /auth/me)...")
    update_data = {
        "name": "Updated Test User",
        "target_job_role": "Senior Engineer",
        "experience_level": "3–5 years"
    }
    status, body = make_request("/auth/me", method="PUT", data=update_data, token=login_token)
    assert status == 200, f"Expected 200, got {status}: {body}"
    assert body["name"] == "Updated Test User", "Name update failed"
    assert body["target_job_role"] == "Senior Engineer", "Job role update failed"
    assert body["experience_level"] == "3–5 years", "Experience level update failed"
    print("SUCCESS: Profile updated successfully.")
    
    print("\n--- All Backend Verification Tests Passed! ---")

if __name__ == "__main__":
    run_tests()
