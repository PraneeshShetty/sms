# File: app.py

import re
from flask import Flask, request, jsonify

# Create the Flask application
app = Flask(__name__)

def analyze_sms(message_body):
    """
    This is the core logic. It checks an SMS for suspicious keywords.
    Returns a reply message string.
    """
    # Using 're.IGNORECASE' to make the search case-insensitive
    scam_pattern = re.compile(
        r'congratulations|you have won|lottery|prize|urgent|act now|account blocked|verify your pin|share your otp|kyc|bit\.ly',
        re.IGNORECASE
    )
    
    if re.search(scam_pattern, message_body):
        # If any keyword is found, create a fraud warning
        return "⚠️ WARNING: This message looks like a scam. Do not click any links or share personal information. Stay safe!"
    else:
        # Otherwise, the message is likely safe
        return "✅ This message appears to be safe. Always be careful with unknown senders."

@app.route("/sms", methods=['POST'])
def handle_sms():
    """
    This function is the webhook that the Android SMS Gateway app will call.
    It receives the SMS, analyzes it, and returns a JSON reply for the app.
    """
    try:
        # Get the JSON data sent by the SMS Gateway app
        data = request.json
        incoming_msg = data.get('message', '')
        sender_number = data.get('from', '')
        
        print(f"Received message from {sender_number}: '{incoming_msg}'")
        
        # Analyze the message to get the correct reply
        response_text = analyze_sms(incoming_msg)
        
        # This JSON structure tells the Android app what SMS to send back
        reply = {
            "payload": {
                "success": True,
                "messages": [
                    {
                        "to": sender_number,
                        "message": response_text
                    }
                ]
            }
        }
        
        return jsonify(reply)

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"payload": {"success": False, "error": "Server error"}}), 500