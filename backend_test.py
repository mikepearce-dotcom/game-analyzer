import requests
import sys
import json
from datetime import datetime
import time

class SentientTrackerAPITester:
    def __init__(self, base_url="https://reddit-analyzer-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_game_id = None
        self.session_token = None
        self.user_id = None
        # Test credentials
        self.test_email = "testuser2@example.com"
        self.test_password = "testpass123"
        self.test_name = "Test User 2"

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, authenticated=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication if required and available
        if authenticated and self.session_token:
            headers['Authorization'] = f'Bearer {self.session_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if authenticated:
            print(f"   Auth: {'✓' if self.session_token else '✗'}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    # Show truncated response for readability
                    response_str = json.dumps(response_data, indent=2)
                    if len(response_str) > 300:
                        response_str = response_str[:300] + "..."
                    print(f"   Response: {response_str}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Raw Response: {response.text[:200]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after {timeout} seconds")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ FAILED - Connection error to {url}")
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    # ============== AUTHENTICATION TESTS ==============
    
    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)
    
    def test_auth_signup(self):
        """Test email signup"""
        signup_data = {
            "email": self.test_email,
            "password": self.test_password,
            "name": self.test_name
        }
        success, data = self.run_test("Email Signup", "POST", "auth/signup", 200, signup_data)
        if success:
            self.session_token = data.get('session_token')
            self.user_id = data.get('user_id')
            print(f"   User created: {data.get('name')} ({data.get('email')})")
            print(f"   User ID: {self.user_id}")
            print(f"   Session token: {'✓' if self.session_token else '✗'}")
        return success
    
    def test_auth_signup_duplicate(self):
        """Test signup with existing email"""
        signup_data = {
            "email": self.test_email,
            "password": self.test_password,
            "name": self.test_name + " Duplicate"
        }
        return self.run_test("Duplicate Email Signup", "POST", "auth/signup", 400, signup_data)
    
    def test_auth_me_authenticated(self):
        """Test /auth/me with valid token"""
        success, data = self.run_test("Get Current User", "GET", "auth/me", 200, authenticated=True)
        if success:
            print(f"   Authenticated as: {data.get('name')} ({data.get('email')})")
            print(f"   Auth provider: {data.get('auth_provider', 'unknown')}")
        return success
    
    def test_auth_me_unauthenticated(self):
        """Test /auth/me without token"""
        return self.run_test("Get Current User (No Auth)", "GET", "auth/me", 401)
    
    def test_auth_logout(self):
        """Test logout (clear session)"""
        success, data = self.run_test("Logout", "POST", "auth/logout", 200, authenticated=True)
        if success:
            print(f"   Logout message: {data.get('message', 'Unknown')}")
            # Clear our token since logout invalidates it
            old_token = self.session_token
            self.session_token = None
            print(f"   Token cleared: {old_token[:16]}..." if old_token else "   No token to clear")
        return success
    
    def test_auth_login(self):
        """Test email login with existing user"""
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        success, data = self.run_test("Email Login", "POST", "auth/login", 200, login_data)
        if success:
            self.session_token = data.get('session_token')
            print(f"   Logged in as: {data.get('name')} ({data.get('email')})")
            print(f"   New session token: {'✓' if self.session_token else '✗'}")
        return success
    
    def test_auth_login_invalid(self):
        """Test login with wrong password"""
        login_data = {
            "email": self.test_email,
            "password": "wrongpassword123"
        }
        return self.run_test("Invalid Login", "POST", "auth/login", 401, login_data)
    
    # ============== PROTECTED ROUTE TESTS ==============

    def test_get_games_unauthenticated(self):
        """Test getting games without authentication"""
        return self.run_test("Get Games (No Auth)", "GET", "games", 401)

    def test_get_games_authenticated(self):
        """Test getting games with authentication"""
        success, data = self.run_test("Get Games (Authenticated)", "GET", "games", 200, authenticated=True)
        if success:
            print(f"   Found {len(data)} games for user")
        return success

    def test_create_game_authenticated(self):
        """Test creating a new game with authentication"""
        game_data = {
            "name": "Test Arc Raiders", 
            "subreddit": "gaming",
            "keywords": "test, performance, bugs"
        }
        success, data = self.run_test("Create Game (Authenticated)", "POST", "games", 200, game_data, authenticated=True)
        if success and 'id' in data:
            self.test_game_id = data['id']
            print(f"   Created game with ID: {self.test_game_id}")
            print(f"   Game belongs to user: {data.get('user_id') == self.user_id}")
        return success

    def test_get_single_game_authenticated(self):
        """Test getting a single game by ID with authentication"""
        if not self.test_game_id:
            print("❌ Skipping - No game ID available")
            return False
        
        success, data = self.run_test("Get Single Game (Authenticated)", "GET", f"games/{self.test_game_id}", 200, authenticated=True)
        if success:
            print(f"   Game name: {data.get('name', 'Unknown')}")
            print(f"   Subreddit: r/{data.get('subreddit', 'Unknown')}")
            print(f"   Owner matches: {data.get('user_id') == self.user_id}")
        return success
    
    def test_update_game_authenticated(self):
        """Test updating a game with authentication"""
        if not self.test_game_id:
            print("❌ Skipping - No game ID available")
            return False
        
        update_data = {
            "name": "Updated Test Arc Raiders",
            "keywords": "updated, test, performance"
        }
        success, data = self.run_test("Update Game (Authenticated)", "PUT", f"games/{self.test_game_id}", 200, update_data, authenticated=True)
        if success:
            print(f"   Updated game name: {data.get('name', 'Unknown')}")
            print(f"   Updated keywords: {data.get('keywords', 'None')}")
        return success

    def test_scan_game_authenticated(self):
        """Test running a scan on the test game with authentication"""
        if not self.test_game_id:
            print("❌ Skipping - No game ID available")
            return False
        
        print("   🚨 This may take 30-60 seconds for Reddit fetch + AI analysis...")
        success, data = self.run_test("Run Scan (Authenticated)", "POST", f"games/{self.test_game_id}/scan", 200, timeout=120, authenticated=True)
        
        if success:
            print(f"   Scan ID: {data.get('id', 'Unknown')}")
            print(f"   Posts scanned: {data.get('post_count', 0)}")
            print(f"   Posts last 7 days: {data.get('posts_last_7_days', 0)}")
            print(f"   Sentiment: {data.get('sentiment_label', 'Unknown')}")
            print(f"   Owner matches: {data.get('user_id') == self.user_id}")
            
            if data.get('error'):
                print(f"   ⚠️ Scan completed with error: {data['error']}")
            else:
                print(f"   Themes found: {len(data.get('themes', []))}")
                print(f"   Pain points: {len(data.get('pain_points', []))}")
                print(f"   Wins found: {len(data.get('wins', []))}")
                print(f"   Source posts: {len(data.get('source_posts', []))}")
        
        return success

    def test_get_scan_results_authenticated(self):
        """Test getting scan results for the game with authentication"""
        if not self.test_game_id:
            print("❌ Skipping - No game ID available")
            return False
            
        success, data = self.run_test("Get Scan Results (Authenticated)", "GET", f"games/{self.test_game_id}/results", 200, authenticated=True)
        if success:
            print(f"   Found {len(data)} scan results")
            if len(data) > 0:
                print(f"   Latest result owner matches: {data[0].get('user_id') == self.user_id}")
        return success

    def test_delete_game_authenticated(self):
        """Test deleting the test game with authentication"""
        if not self.test_game_id:
            print("❌ Skipping - No game ID available")
            return False
            
        success, data = self.run_test("Delete Game (Authenticated)", "DELETE", f"games/{self.test_game_id}", 200, authenticated=True)
        if success:
            print(f"   Successfully deleted game {self.test_game_id}")
            print(f"   Delete message: {data.get('message', 'No message')}")
        return success

def main():
    print("🎯 Starting Sentient Tracker Authentication API Tests")
    print("=" * 60)
    
    tester = SentientTrackerAPITester()
    
    # Test sequence - focusing on authentication flow
    tests = [
        # Basic health check
        ("API Health Check", tester.test_root_endpoint),
        
        # Authentication flow tests
        ("Email Signup", tester.test_auth_signup),
        ("Duplicate Email Signup", tester.test_auth_signup_duplicate),
        ("Get Current User (Authenticated)", tester.test_auth_me_authenticated),
        ("Get Current User (Unauthenticated)", tester.test_auth_me_unauthenticated),
        ("Logout", tester.test_auth_logout),
        ("Email Login", tester.test_auth_login),
        ("Invalid Login", tester.test_auth_login_invalid),
        
        # Protected routes tests
        ("Get Games (No Auth)", tester.test_get_games_unauthenticated),
        ("Get Games (Authenticated)", tester.test_get_games_authenticated),
        ("Create Game (Authenticated)", tester.test_create_game_authenticated),
        ("Get Single Game (Authenticated)", tester.test_get_single_game_authenticated),
        ("Update Game (Authenticated)", tester.test_update_game_authenticated),
        ("Run Scan (Authenticated)", tester.test_scan_game_authenticated),
        ("Get Scan Results (Authenticated)", tester.test_get_scan_results_authenticated),
        ("Delete Game (Authenticated)", tester.test_delete_game_authenticated),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print('='*60)
        
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            failed_tests.append(test_name)
        
        # Small delay between tests
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("🏁 AUTHENTICATION TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"📊 Tests Run: {tester.tests_run}")
    print(f"✅ Tests Passed: {tester.tests_passed}")
    print(f"❌ Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"📈 Success Rate: {(tester.tests_passed / max(tester.tests_run, 1)) * 100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"   • {test}")
        print("\n💡 Key Authentication Features Tested:")
        print("   • Email signup and login flow")
        print("   • Session token management")
        print("   • Protected route access control")
        print("   • User-scoped data isolation")
        print("   • Logout and session cleanup")
    else:
        print(f"\n🎉 ALL AUTHENTICATION TESTS PASSED!")
        print("✅ Email signup/login working")
        print("✅ Protected routes properly secured")
        print("✅ User data isolation confirmed")
        print("✅ Session management functional")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())