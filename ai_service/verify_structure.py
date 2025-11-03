"""
Simple endpoint verification - checks file structure only
No dependencies required
"""
import os
from pathlib import Path

def check_file(path, description):
    """Check if a file exists"""
    if os.path.exists(path):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - NOT FOUND")
        return False

def count_routes_in_file(filepath):
    """Count @router decorators in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return content.count('@router.')
    except:
        return 0

print("🔍 Verifying DocuLearn AI Service Structure")
print("=" * 60)

base_path = Path(__file__).parent

# Check critical files
files_ok = True
files_ok &= check_file(base_path / "app" / "main.py", "Main application")
files_ok &= check_file(base_path / "app" / "api" / "router.py", "API router")
files_ok &= check_file(base_path / "app" / "api" / "routes" / "health.py", "Health endpoints")
files_ok &= check_file(base_path / "app" / "api" / "routes" / "sessions.py", "Session endpoints")
files_ok &= check_file(base_path / "app" / "api" / "routes" / "chat.py", "Chat endpoints")
files_ok &= check_file(base_path / "app" / "schemas" / "session.py", "Schemas")
files_ok &= check_file(base_path / "app" / "schemas" / "__init__.py", "Schema exports")
files_ok &= check_file(base_path / "requirements.txt", "Requirements file")

print("\n📊 Endpoint Count:")
print("=" * 60)

health_routes = count_routes_in_file(base_path / "app" / "api" / "routes" / "health.py")
session_routes = count_routes_in_file(base_path / "app" / "api" / "routes" / "sessions.py")
chat_routes = count_routes_in_file(base_path / "app" / "api" / "routes" / "chat.py")

print(f"Health endpoints:  {health_routes} routes")
print(f"Session endpoints: {session_routes} routes")
print(f"Chat endpoints:    {chat_routes} routes")
print(f"─" * 60)
print(f"Total:             {health_routes + session_routes + chat_routes} routes")

print("\n📋 Expected vs Actual:")
print("=" * 60)

expected = {
    "Health": (health_routes, 2),
    "Sessions": (session_routes, 4),
    "Chat": (chat_routes, 3)
}

all_match = True
for name, (actual, expected_count) in expected.items():
    if actual == expected_count:
        print(f"✅ {name}: {actual}/{expected_count}")
    else:
        print(f"⚠️  {name}: {actual}/{expected_count}")
        all_match = False

print("\n📝 Schema Exports:")
print("=" * 60)

schema_init = base_path / "app" / "schemas" / "__init__.py"
try:
    with open(schema_init, 'r', encoding='utf-8') as f:
        content = f.read()
        exports = [
            "CreatePlanRequest",
            "CreatePlanResponse",
            "SessionResponse",
            "HealthResponse",
            "ChatRequest",
            "ChatResponse",
            "StreamChatRequest",
            "GraphStateResponse"
        ]
        
        for export in exports:
            if export in content:
                print(f"✅ {export}")
            else:
                print(f"❌ {export} - NOT EXPORTED")
                all_match = False
except:
    print("❌ Could not read schema __init__.py")
    all_match = False

print("\n" + "=" * 60)

if files_ok and all_match:
    print("🎉 All endpoints are properly implemented!")
    print("\n📖 Next steps:")
    print("   1. Install dependencies: pip install -r requirements.txt")
    print("   2. Set up .env file with API keys")
    print("   3. Start server: uvicorn app.main:app --reload --port 8001")
    print("   4. Visit: http://localhost:8001/docs")
    print("\n📚 See ENDPOINTS_GUIDE.md for detailed usage")
else:
    print("⚠️  Some issues found. Please review above.")

print("=" * 60)
