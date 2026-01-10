"""
Quick test script to verify backend connectivity before running the dashboard.
"""

import requests
import sys

BACKEND_URL = "http://localhost:8000"
TEST_USER_ID = "4b0939d1-7595-414e-bbd9-597f41c39e99"

def test_backend_health():
    """Test if backend is responding."""
    try:
        response = requests.get(f"{BACKEND_URL}/")
        assert response.status_code == 200
        print("✅ Backend is online")
        return True
    except Exception as e:
        print(f"❌ Backend is not responding: {e}")
        return False

def test_reports_endpoint():
    """Test if reports endpoint works."""
    try:
        response = requests.get(f"{BACKEND_URL}/reports/savings/{TEST_USER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "category_breakdown" in data
        assert "top_recommendation" in data
        print("✅ Reports endpoint working")
        return True
    except Exception as e:
        print(f"❌ Reports endpoint failed: {e}")
        return False

def test_opportunities_endpoint():
    """Test if opportunities endpoint works."""
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/opportunities/{TEST_USER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Opportunities endpoint working ({len(data)} opportunities found)")
        return True
    except Exception as e:
        print(f"❌ Opportunities endpoint failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing backend connectivity...\n")
    
    tests = [
        test_backend_health(),
        test_reports_endpoint(),
        test_opportunities_endpoint()
    ]
    
    print("\n" + "="*50)
    if all(tests):
        print("✅ All tests passed! You can run the dashboard with:")
        print("   streamlit run app.py")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the backend:")
        print("   docker-compose up -d")
        print("   docker-compose logs backend")
        sys.exit(1)

