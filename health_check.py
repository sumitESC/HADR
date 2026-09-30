import urllib.request
import urllib.error
import sys

def check_url(url, name):
    print(f"Checking {name} at {url} ...")
    try:
        # We use a user-agent header because some services block default urllib agents
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=10)
        
        # Check if response status is 200 OK
        if response.status == 200:
            print(f"✅ {name} is UP! (Status Code: 200)")
            return True
        else:
            print(f"⚠️ {name} returned status code: {response.status}")
            return False
            
    except urllib.error.HTTPError as e:
        print(f"❌ {name} returned an HTTP Error: {e.code} - {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"❌ {name} is DOWN or unreachable! Error: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ {name} encountered an unexpected error: {e}")
        return False

def main():
    frontend_url = "https://hadr-ov0q.onrender.com/"
    backend_url = "https://hadr1.onrender.com/"

    print("========================================")
    print("        HADR SYSTEM HEALTH CHECK        ")
    print("========================================")
    
    frontend_ok = check_url(frontend_url, "Frontend Dashboard")
    backend_ok = check_url(backend_url, "Backend API")

    print("\n----------------------------------------")
    if frontend_ok and backend_ok:
        print("🎉 ALL SYSTEMS ARE OPERATIONAL!")
        sys.exit(0)
    else:
        print("⚠️ WARNING: SOME SYSTEMS ARE DOWN OR UNREACHABLE.")
        sys.exit(1)

if __name__ == "__main__":
    main()
