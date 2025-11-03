"""
Test script to verify all endpoints are properly defined and accessible
Run this to check if all routes are registered correctly
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("🔍 Testing imports...")
    
    # Test schema imports
    from app.schemas.session import (
        CreatePlanRequest,
        CreatePlanResponse,
        SessionResponse,
        HealthResponse,
        ChatRequest,
        ChatResponse,
        StreamChatRequest,
        GraphStateResponse
    )
    print("✅ All schemas imported successfully")
    
    # Test route imports
    from app.api.routes import health, sessions, chat
    print("✅ All route modules imported successfully")
    
    # Test router
    from app.api.router import api_router
    print("✅ API router imported successfully")
    
    # Check registered routes
    print("\n📋 Registered Routes:")
    print("=" * 60)
    
    routes_by_tag = {}
    for route in api_router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            tags = getattr(route, 'tags', ['Untagged'])
            tag = tags[0] if tags else 'Untagged'
            
            if tag not in routes_by_tag:
                routes_by_tag[tag] = []
            
            methods = ', '.join(route.methods)
            routes_by_tag[tag].append(f"  {methods:8} /api/v1{route.path}")
    
    # Print organized by tag
    for tag, routes in sorted(routes_by_tag.items()):
        print(f"\n🏷️  {tag}:")
        for route in sorted(routes):
            print(route)
    
    print("\n" + "=" * 60)
    
    # Count endpoints
    total_routes = sum(len(routes) for routes in routes_by_tag.values())
    print(f"\n✅ Total Endpoints: {total_routes}")
    
    # Expected endpoints
    expected = {
        "Health": 2,
        "Sessions": 4,
        "Chat": 3
    }
    
    print("\n📊 Endpoint Summary:")
    all_good = True
    for tag, expected_count in expected.items():
        actual_count = len(routes_by_tag.get(tag, []))
        status = "✅" if actual_count == expected_count else "❌"
        print(f"  {status} {tag}: {actual_count}/{expected_count} endpoints")
        if actual_count != expected_count:
            all_good = False
    
    if all_good:
        print("\n🎉 All endpoints are properly registered!")
        print("💡 Start the server with: uvicorn app.main:app --reload --port 8001")
        print("📖 API docs available at: http://localhost:8001/docs")
    else:
        print("\n⚠️  Some endpoints are missing!")
        sys.exit(1)
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\n💡 Make sure to install dependencies first:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
