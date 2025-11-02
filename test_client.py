#!/usr/bin/env python3
"""
Simple client script to test the AI Medical Assistant API from your laptop.
Replace <PI_IP> with your Raspberry Pi's IP address.
"""

import requests
import sys

# Configuration - CHANGE THIS to your Raspberry Pi's IP address
PI_IP = "172.19.105.161"  # Replace with your Pi's IP
API_URL = f"http://{PI_IP}:8000"

def test_health():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{API_URL}/api/health")
        print("Health Check:")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"Service: {health_data.get('service', 'N/A')}")
            print(f"Model: {health_data.get('model', 'N/A')}")
            print(f"Version: {health_data.get('version', 'N/A')}\n")
        else:
            print(f"Response: {response.text}\n")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        print("Note: You can skip this check and go directly to http://<PI_IP>:8000 in your browser\n")
        return False

def ask_question(query):
    """Send a question to the API"""
    try:
        response = requests.post(
            f"{API_URL}/ask",
            json={"query": query},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response received:")
            print(f"Query: {query}")
            print(f"\n📋 Diagnosis/Assessment:")
            print(f"   {result.get('diagnosis', 'N/A')}")
            print(f"\n💡 Advice/Recommendations:")
            print(f"   {result.get('advice', 'N/A')}")
            print()
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}\n")
            return False
    except Exception as e:
        print(f"❌ Request failed: {e}\n")
        return False

def main():
    print(f"Testing AI Medical Assistant API at {API_URL}\n")
    
    # Test health endpoint
    if not test_health():
        print("⚠️  Server is not responding. Make sure:")
        print("   1. Server is running on the Raspberry Pi")
        print("   2. IP address is correct (currently:", PI_IP, ")")
        print("   3. Firewall allows connections on port 8000")
        sys.exit(1)
    
    # Test with example queries
    if len(sys.argv) > 1:
        # Use command line argument as query
        query = " ".join(sys.argv[1:])
        ask_question(query)
    else:
        # Use default example queries
        example_queries = [
            "What are the symptoms of a common cold?",
            "What should I do if I have a fever?",
        ]
        
        for query in example_queries:
            ask_question(query)
            input("Press Enter to continue to next question...")

if __name__ == "__main__":
    main()

