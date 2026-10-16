#!/usr/bin/env python3
"""
Test script for LaunchDarkly SDK Exporter
"""

import requests
import sys

def test_endpoints():
    """Test all Flask endpoints"""
    base_url = "http://localhost:8000"

    print("🧪 Testing LaunchDarkly SDK Exporter endpoints...\n")

    # Test index endpoint
    print("1. Testing / (index) endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200 and "LaunchDarkly SDK Exporter" in response.text:
            print("   ✅ Index endpoint working")
        else:
            print(f"   ❌ Index endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Index endpoint error: {e}")
        return False

    # Test health endpoint
    print("2. Testing /health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health endpoint working - Status: {data.get('status')}")
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health endpoint error: {e}")
        return False

    # Test metrics endpoint
    print("3. Testing /metrics endpoint...")
    try:
        response = requests.get(f"{base_url}/metrics")
        if response.status_code == 200:
            metrics = response.text
            # Check for our custom metrics
            if "launchdarkly_sdk_clients_by_type_and_version" in metrics:
                print("   ✅ Metrics endpoint working - Custom metrics found")
            else:
                print("   ⚠️  Metrics endpoint working but no custom metrics yet")

            # Verify no default metrics
            if "process_cpu_seconds_total" in metrics or "python_info" in metrics:
                print("   ⚠️  Warning: Default Python metrics are present (should be disabled)")
            else:
                print("   ✅ Default metrics successfully disabled")
        else:
            print(f"   ❌ Metrics endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Metrics endpoint error: {e}")
        return False

    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_endpoints()
    sys.exit(0 if success else 1)
