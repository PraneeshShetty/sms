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
    scam_pattern = re.compile(
        r'congratulations|you have won|lottery|prize|urgent|act now|account blocked|verify your pin|share your otp|kyc|bit\.ly',
        re.IGNORECASE
    )
    
    if re.search(scam_pattern, message_body):
        return "⚠️ WARNING: This message looks like a scam. Do not click any links or share personal information. Stay safe!"
    else:
        return "✅ This message appears to be safe. Always be careful with unknown senders."

@app.route("/sms", methods=['POST'])
def handle_sms():
    """
    This function is the webhook that the Android SMS Gateway app will call.
    It receives the SMS, analyzes it, and returns a JSON reply for the app.
    """
    try:
        # --- NEW CODE BLOCK STARTS HERE ---
        # First, check if the request from the phone is correctly formatted as JSON
        if not request.is_json:
            raw_body = request.get_data(as_text=True)
            print(f"Error: Request is not JSON. Raw body received: '{raw_body}'")
            # Return a specific JSON error to help us debug
            return jsonify({
                "payload": {
                    "success": False, 
                    "error": "Request Content-Type header was not application/json"
                }
            }), 400 # 400 is the code for a "Bad Request"
        # --- NEW CODE BLOCK ENDS HERE ---

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
        print(f"An error occurred in the main block: {e}")
        return jsonify({"payload": {"success": False, "error": "A server error occurred"}}), 500