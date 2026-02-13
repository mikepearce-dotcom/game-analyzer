#!/usr/bin/env python3
"""
Quick test to verify if we can get successful Reddit data from any subreddit
"""
import requests
import json

def test_reddit_access():
    """Test direct Reddit access to see what subreddits work"""
    subreddits = ['Python', 'programming', 'technology', 'news', 'pics', 'funny']
    
    for subreddit in subreddits:
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=5"
        headers = {"User-Agent": "SentientTracker/1.0 (Game Community Pulse MVP)"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"\n🔍 Testing r/{subreddit}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                post_count = len(data.get('data', {}).get('children', []))
                print(f"   ✅ SUCCESS - Found {post_count} posts")
                if post_count > 0:
                    first_post = data['data']['children'][0]['data']
                    print(f"   Sample: {first_post.get('title', 'No title')[:50]}...")
                return subreddit  # Return first working subreddit
            elif response.status_code == 403:
                print(f"   ❌ FORBIDDEN - Private or banned")
            elif response.status_code == 404:
                print(f"   ❌ NOT FOUND")
            else:
                print(f"   ❌ ERROR - {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION - {e}")
    
    return None

if __name__ == "__main__":
    print("🔍 Testing Reddit API Access")
    print("=" * 30)
    
    working_subreddit = test_reddit_access()
    
    if working_subreddit:
        print(f"\n✅ Found working subreddit: r/{working_subreddit}")
        print("Reddit API access is functional")
    else:
        print(f"\n⚠️ No accessible subreddits found")
        print("This may be due to Reddit API restrictions or rate limiting")