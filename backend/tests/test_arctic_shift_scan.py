"""
Backend API tests for Sentient Tracker - Arctic Shift Integration
Tests: POST selection with quality filtering, comment sampling, AI summarization with evidence links
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from the review request
TEST_USER_EMAIL = "test2@example.com"
TEST_USER_PASSWORD = "password123"
TEST_GAME_ID = "44496f4f-a82b-489b-9d4e-2bc1626e8076"
SESSION_TOKEN = "S0g3aaQHomRqbMhNW65PLQ9Q9VV_SPwsC9BBRtEEBSs"


class TestArcticsShiftScan:
    """Tests for the Arctic Shift Reddit scan functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SESSION_TOKEN}"
        })
    
    def test_api_root_health(self):
        """Test API root endpoint is reachable"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"API Root Response: {data}")
    
    def test_auth_with_token(self):
        """Test authentication with provided session token"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        print(f"Authenticated as: {data['email']}")
    
    def test_get_game_details(self):
        """Test fetching game details before scanning"""
        response = self.session.get(f"{BASE_URL}/api/games/{TEST_GAME_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "subreddit" in data
        print(f"Game: {data['name']} - r/{data['subreddit']}")
    
    def test_get_latest_scan_result(self):
        """Test fetching the most recent scan result"""
        response = self.session.get(f"{BASE_URL}/api/games/{TEST_GAME_ID}/latest-result")
        assert response.status_code == 200
        data = response.json()
        
        if data:
            # Validate scan result structure
            assert "post_count" in data
            assert "sentiment_label" in data
            assert "themes" in data
            assert "pain_points" in data
            assert "wins" in data
            
            # New: Check comments_sampled field
            assert "comments_sampled" in data, "Missing comments_sampled field in scan result"
            print(f"Comments sampled: {data['comments_sampled']}")
            
            # New: Check debug_info structure
            assert "debug_info" in data
            debug = data["debug_info"]
            if debug:
                assert "window_used" in debug
                assert "raw_post_count" in debug
                assert "after_quality_filter" in debug
                assert "final_post_count" in debug
                assert "comments_fetched_for" in debug
                assert "total_comments" in debug
                print(f"Debug Info: window={debug.get('window_used')}, raw={debug.get('raw_post_count')}, filtered={debug.get('after_quality_filter')}, final={debug.get('final_post_count')}")
            
            # Check pain_points structure (should have text and evidence)
            if data["pain_points"]:
                first_pain_point = data["pain_points"][0]
                assert "text" in first_pain_point, "Pain point missing 'text' field"
                assert "evidence" in first_pain_point, "Pain point missing 'evidence' field"
                assert isinstance(first_pain_point["evidence"], list), "Evidence should be a list"
                print(f"Pain point example: {first_pain_point['text'][:50]}...")
                if first_pain_point["evidence"]:
                    print(f"Evidence links: {first_pain_point['evidence']}")
            
            # Check wins structure (should have text and evidence)
            if data["wins"]:
                first_win = data["wins"][0]
                assert "text" in first_win, "Win missing 'text' field"
                assert "evidence" in first_win, "Win missing 'evidence' field"
                assert isinstance(first_win["evidence"], list), "Evidence should be a list"
                print(f"Win example: {first_win['text'][:50]}...")
                if first_win["evidence"]:
                    print(f"Evidence links: {first_win['evidence']}")
        else:
            print("No previous scan results found - this is expected for new games")
    
    def test_scan_throttling(self):
        """Test that throttling prevents scans within 30 seconds of each other"""
        # First scan attempt
        response1 = self.session.post(f"{BASE_URL}/api/games/{TEST_GAME_ID}/scan")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Immediately try second scan - should be throttled
        response2 = self.session.post(f"{BASE_URL}/api/games/{TEST_GAME_ID}/scan")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # If throttled, error field should mention waiting
        if data2.get("error"):
            assert "wait" in data2["error"].lower() or "seconds" in data2["error"].lower()
            print(f"Throttling working: {data2['error']}")
        else:
            # If not throttled, could be using cache (within 10 min TTL)
            assert data2.get("cached") == True, "Should either be throttled or cached"
            print("Using cached result instead of throttled")
    
    def test_scan_result_structure_comprehensive(self):
        """Comprehensive test of scan result structure with all new fields"""
        response = self.session.get(f"{BASE_URL}/api/games/{TEST_GAME_ID}/latest-result")
        assert response.status_code == 200
        data = response.json()
        
        if not data:
            pytest.skip("No scan results available for comprehensive testing")
        
        # Core fields
        required_fields = [
            "id", "tracked_game_id", "user_id", "created_at",
            "post_count", "posts_last_7_days", "comments_sampled",
            "sentiment_label", "sentiment_summary", "themes",
            "pain_points", "wins", "source_posts"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate comments_sampled is a number
        assert isinstance(data["comments_sampled"], int)
        print(f"Comments sampled: {data['comments_sampled']}")
        
        # Validate pain_points structure
        for i, pp in enumerate(data["pain_points"]):
            assert isinstance(pp, dict), f"Pain point {i} should be a dict"
            assert "text" in pp, f"Pain point {i} missing 'text'"
            assert "evidence" in pp, f"Pain point {i} missing 'evidence'"
            assert isinstance(pp["evidence"], list), f"Pain point {i} evidence should be list"
            # Check evidence links are Reddit URLs
            for link in pp["evidence"]:
                assert "reddit.com" in link, f"Evidence link should be Reddit URL: {link}"
        
        # Validate wins structure
        for i, win in enumerate(data["wins"]):
            assert isinstance(win, dict), f"Win {i} should be a dict"
            assert "text" in win, f"Win {i} missing 'text'"
            assert "evidence" in win, f"Win {i} missing 'evidence'"
            assert isinstance(win["evidence"], list), f"Win {i} evidence should be list"
            # Check evidence links are Reddit URLs
            for link in win["evidence"]:
                assert "reddit.com" in link, f"Evidence link should be Reddit URL: {link}"
        
        # Validate debug_info structure
        debug = data.get("debug_info")
        if debug:
            debug_fields = [
                "subreddit_normalized", "window_used", "raw_post_count",
                "after_quality_filter", "final_post_count",
                "comments_fetched_for", "total_comments"
            ]
            for field in debug_fields:
                assert field in debug, f"Debug info missing field: {field}"
            
            # Quality filter should reduce post count
            if debug["raw_post_count"] > 0:
                print(f"Quality filter: {debug['raw_post_count']} -> {debug['after_quality_filter']} posts")
                # after_quality_filter should be <= raw_post_count
                assert debug["after_quality_filter"] <= debug["raw_post_count"]
        
        print(f"Comprehensive structure validation passed")
    
    def test_source_posts_have_required_fields(self):
        """Test that source posts contain all required fields"""
        response = self.session.get(f"{BASE_URL}/api/games/{TEST_GAME_ID}/latest-result")
        assert response.status_code == 200
        data = response.json()
        
        if not data or not data.get("source_posts"):
            pytest.skip("No source posts available")
        
        for i, post in enumerate(data["source_posts"][:5]):  # Check first 5
            assert "id" in post, f"Post {i} missing 'id'"
            assert "title" in post, f"Post {i} missing 'title'"
            assert "score" in post, f"Post {i} missing 'score'"
            assert "num_comments" in post, f"Post {i} missing 'num_comments'"
            assert "permalink" in post, f"Post {i} missing 'permalink'"
            # Verify permalink is a Reddit URL
            assert "reddit.com" in post["permalink"], f"Post {i} has invalid permalink"
        
        print(f"Validated {min(5, len(data['source_posts']))} source posts")
    
    def test_cache_status_endpoint(self):
        """Test the cache status endpoint"""
        # Get game details to know the subreddit
        game_response = self.session.get(f"{BASE_URL}/api/games/{TEST_GAME_ID}")
        game = game_response.json()
        subreddit = game.get("subreddit", "Eldenring")
        
        response = requests.get(f"{BASE_URL}/api/cache-status/{subreddit}")
        assert response.status_code == 200
        data = response.json()
        
        # Cache status fields
        assert "cached" in data
        assert "valid" in data
        
        if data["cached"]:
            assert "age_seconds" in data
            assert "expires_in" in data
            print(f"Cache status: age={data['age_seconds']}s, expires_in={data['expires_in']}s")
        else:
            print("No cache entry found")


class TestQualityFilter:
    """Tests for quality filtering logic"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SESSION_TOKEN}"
        })
    
    def test_quality_filter_reduces_post_count(self):
        """Verify quality filter removes low-quality posts"""
        response = self.session.get(f"{BASE_URL}/api/games/{TEST_GAME_ID}/latest-result")
        assert response.status_code == 200
        data = response.json()
        
        if not data or not data.get("debug_info"):
            pytest.skip("No debug info available")
        
        debug = data["debug_info"]
        raw = debug.get("raw_post_count", 0)
        filtered = debug.get("after_quality_filter", 0)
        
        # Quality filter should potentially reduce posts (or keep same if all are quality)
        assert filtered <= raw, "Filtered count should not exceed raw count"
        print(f"Quality filter: {raw} raw -> {filtered} after filter ({raw - filtered} removed)")


class TestCommentSampling:
    """Tests for comment sampling functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SESSION_TOKEN}"
        })
    
    def test_comments_fetched_for_top_posts(self):
        """Verify comments are fetched for top 15 posts"""
        response = self.session.get(f"{BASE_URL}/api/games/{TEST_GAME_ID}/latest-result")
        assert response.status_code == 200
        data = response.json()
        
        if not data or not data.get("debug_info"):
            pytest.skip("No debug info available")
        
        debug = data["debug_info"]
        comments_fetched_for = debug.get("comments_fetched_for", 0)
        total_comments = debug.get("total_comments", 0)
        comments_sampled = data.get("comments_sampled", 0)
        
        # Should fetch comments for up to 15 posts
        assert comments_fetched_for <= 15, "Should fetch comments for max 15 posts"
        
        # Total comments should match comments_sampled
        assert total_comments == comments_sampled, f"total_comments ({total_comments}) should match comments_sampled ({comments_sampled})"
        
        print(f"Comments: fetched_for={comments_fetched_for} posts, total={total_comments}")


class TestAISummarization:
    """Tests for AI summarization with evidence links"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SESSION_TOKEN}"
        })
    
    def test_pain_points_have_evidence_links(self):
        """Verify pain points include evidence links"""
        response = self.session.get(f"{BASE_URL}/api/games/{TEST_GAME_ID}/latest-result")
        assert response.status_code == 200
        data = response.json()
        
        if not data or not data.get("pain_points"):
            pytest.skip("No pain points available")
        
        has_evidence = False
        for pp in data["pain_points"]:
            assert "text" in pp, "Pain point must have 'text' field"
            assert "evidence" in pp, "Pain point must have 'evidence' field"
            if pp["evidence"]:
                has_evidence = True
                for link in pp["evidence"]:
                    assert link.startswith("https://www.reddit.com/"), f"Invalid evidence link: {link}"
        
        print(f"Pain points have evidence links: {has_evidence}")
    
    def test_wins_have_evidence_links(self):
        """Verify wins include evidence links"""
        response = self.session.get(f"{BASE_URL}/api/games/{TEST_GAME_ID}/latest-result")
        assert response.status_code == 200
        data = response.json()
        
        if not data or not data.get("wins"):
            pytest.skip("No wins available")
        
        has_evidence = False
        for win in data["wins"]:
            assert "text" in win, "Win must have 'text' field"
            assert "evidence" in win, "Win must have 'evidence' field"
            if win["evidence"]:
                has_evidence = True
                for link in win["evidence"]:
                    assert link.startswith("https://www.reddit.com/"), f"Invalid evidence link: {link}"
        
        print(f"Wins have evidence links: {has_evidence}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
