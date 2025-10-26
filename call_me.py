"""
Trigger Twilio calls to test the AI Voice Agent
"""

from twilio.rest import Client
import os
from dotenv import load_dotenv
import time

load_dotenv()

# Your credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Your Indian number
YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER", "+919582350455")

# Your ngrok URL
NGROK_URL = os.getenv("NGROK_URL", "https://325cbfd4c0cc.ngrok-free.app")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def call_me_with_ai():
    """Twilio calls YOU and connects to AI agent"""
    
    print("=" * 60)
    print("📞 CALLING YOU WITH AI AGENT")
    print("=" * 60)
    print(f"📱 Your phone: {YOUR_PHONE_NUMBER}")
    print(f"📞 From Twilio: {TWILIO_PHONE_NUMBER}")
    print(f"🌐 AI Server: {NGROK_URL}")
    print("=" * 60)
    
    if "your-ngrok-url" in NGROK_URL:
        print("\n❌ ERROR: NGROK_URL not set!")
        print("\n📍 Setup Instructions:")
        print("1. Run: ngrok http 8000")
        print("2. Copy https URL (e.g., https://abc123.ngrok.io)")
        print("3. Add to .env: NGROK_URL=https://abc123.ngrok.io")
        return None
    
    try:
        # Make the call
        call = client.calls.create(
            to=YOUR_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{NGROK_URL}/voice",
            status_callback=f"{NGROK_URL}/call-status",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            method='POST'
        )
        
        print("\n✅ Call initiated successfully!")
        print(f"📊 Call SID: {call.sid}")
        print(f"📍 Status: {call.status}")
        print("\n🔔 Your phone will ring in 5-10 seconds...")
        print("🎙️ When you answer, the AI agent will greet you!")
        print("\n💡 Try saying:")
        print("   - 'Where is my vehicle?'")
        print("   - 'When will it be delivered?'")
        print("   - 'I want to cancel my booking'")
        print("=" * 60)
        
        return call.sid
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check .env file has correct Twilio credentials")
        print("2. Make sure ngrok is running: ngrok http 8000")
        print("3. Update NGROK_URL in .env")
        print("4. Ensure FastAPI server is running: python main.py")
        print("5. Check phone number format (include country code)")
        return None


def get_call_status(call_sid: str):
    """Get status of a call"""
    
    try:
        call = client.calls(call_sid).fetch()
        print(f"📊 Call Status: {call.status}")
        print(f"   Duration: {call.duration}s")
        print(f"   Sid: {call.sid}")
        return call
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def list_recent_calls():
    """List recent calls"""
    
    try:
        calls = client.calls.stream(limit=5)
        print("\n📞 Recent Calls:")
        print("-" * 60)
        for call in calls:
            print(f"📱 {call.from_} -> {call.to}")
            print(f"   Status: {call.status} | Duration: {call.duration}s")
            print(f"   SID: {call.sid}")
            print()
        print("-" * 60)
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "call":
            call_id = call_me_with_ai()
            if call_id:
                time.sleep(2)
                get_call_status(call_id)
        
        elif command == "status" and len(sys.argv) > 2:
            get_call_status(sys.argv[2])
        
        elif command == "list":
            list_recent_calls()
        
        else:
            print("Usage:")
            print("  python call_me.py call         - Call you now")
            print("  python call_me.py status SID   - Get call status")
            print("  python call_me.py list         - List recent calls")
    else:
        # Default: make a call
        call_me_with_ai()