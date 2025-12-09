import os
from twilio.rest import Client
from crewai.tools import BaseTool
import dotenv

dotenv.load_dotenv()
# Twilio client initialized once
client = Client(
    os.getenv("TWILIO_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)


class SendRealSMSTool(BaseTool):
    """Send an SMS using Twilio."""
    name: str = "send_real_sms"
    description: str = "Send an SMS to a given phone number using Twilio."

    def _run(self, to: str, message: str) -> str:
        sms = client.messages.create(
            body=message,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=os.getenv("NOTIFY_TO")
        )
        return f"SMS sent successfully! SID={sms.sid}"


class CallProviderRealTool(BaseTool):
    """Place a real call using Twilio."""
    name: str = "call_provider_real"
    description: str = "Call a provider using Twilio."

    def _run(self, to: str) -> str:
        call = client.calls.create(
            to=os.getenv("NOTIFY_TO"),
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            url="http://demo.twilio.com/docs/voice.xml"
        )
        return f"CALL PLACED! SID={call.sid}"
