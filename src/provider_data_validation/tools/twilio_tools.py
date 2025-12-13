import os
from twilio.rest import Client
from crewai.tools import BaseTool
import dotenv

dotenv.load_dotenv()

# DEMO MODE - Set to True to skip actual SMS sending for hackathon
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# Twilio client initialized once
if not DEMO_MODE:
    client = Client(
        os.getenv("TWILIO_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )
else:
    client = None  # No Twilio client in demo mode


class SendRealSMSTool(BaseTool):
    """Send an SMS using Twilio.
    
    DEMO MODE: When DEMO_MODE=true, no actual SMS is sent (for hackathon demos).
    """
    name: str = "send_real_sms"
    description: str = "Send an SMS to a given phone number using Twilio."

    def _run(self, to: str, message: str) -> str:
        if DEMO_MODE:
            print(f"[TWILIO DEMO] Would send SMS to: {to}")
            print(f"[TWILIO DEMO] Message: {message[:100]}...")
            return f"SMS sent: SMdemo{hash(message) % 100000}"
        
        # REAL MODE: Override 'to' parameter with NOTIFY_TO from .env
        demo_number = os.getenv("NOTIFY_TO")
        
        print(f"[TWILIO] Demo Mode Override:")
        print(f"[TWILIO] Provider phone (ignored): {to}")
        print(f"[TWILIO] Actually sending to: {demo_number}")
        
        sms = client.messages.create(
            body=message,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=demo_number  # Using demo number instead of actual provider phone
        )
        print(f"[TWILIO] SMS queued successfully! SID: {sms.sid}")
        return f"SMS sent: {sms.sid}"


class CallProviderRealTool(BaseTool):
    """Place a real call using Twilio.
    
    DEMO MODE: All calls are placed to NOTIFY_TO from .env instead of
    the actual provider's phone number. This is for safety during testing.
    """
    name: str = "call_provider_real"
    description: str = "Call a provider using Twilio."

    def _run(self, to: str) -> str:
        # DEMO MODE: Override 'to' parameter with NOTIFY_TO from .env
        # This calls your demo phone instead of actual provider
        demo_number = os.getenv("NOTIFY_TO")
        
        call = client.calls.create(
            to=demo_number,  # Using demo number instead of actual provider phone
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            url="http://demo.twilio.com/docs/voice.xml"
        )
        return f"Call placed: {call.sid}"
