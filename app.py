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
    # --- Tier 1: High-priority UPI scam patterns (the most dangerous) ---
    # Looks for phrases asking for a PIN to RECEIVE money or approving a "collect request".
    upi_scam_pattern = re.compile(
        r'enter.*upi pin.*receive money|approve.*request.*receive|payment request.*approve|requested money from you|claim.*cashback.*pin',
        re.IGNORECASE
    )

    # --- Tier 2: High-priority OTP scam patterns ---
    # Looks for phrases asking you to share a secret code to authorize something.
    otp_scam_pattern = re.compile(
        r'share.*otp|share.*one time password|enter.*otp.*authorize|forward this code',
        re.IGNORECASE
    )

    # --- Tier 3: General scam patterns ---
    # Looks for urgency, fake lottery wins, and suspicious links.
    general_scam_pattern = re.compile(
        r'congratulations|you have won|lottery|prize|urgent|act now|account blocked|verify your pin|kyc|bit\.ly',
        re.IGNORECASE
    )

    # We now check for scams in order of how dangerous they are.
    if re.search(upi_scam_pattern, message_body):
        # Provide a very specific UPI warning
        return "⚠️ UPI SCAM ALERT! Never enter your UPI PIN to receive money. This message is trying to steal from your account. DO NOT APPROVE."

    if re.search(otp_scam_pattern, message_body):
        # Provide a specific OTP warning
        return "⚠️ OTP SCAM ALERT! Never share an OTP with anyone. This message is trying to gain access to your account."

    if re.search(general_scam_pattern, message_body):
        # Provide the general warning for other types of scams
        return "⚠️ WARNING: This message looks like a scam. Do not click any links or share personal information."

    # If no patterns match, the message is likely safe.
    return "✅ This message appears to be safe. Always be careful with unknown senders."


@app.route("/sms", methods=['POST'])
def handle_sms():
    """
    This function is the webhook that the Android SMS Gateway app will call.
    It receives the SMS, analyzes it, and returns a JSON reply for the app.
    """
    try:
        if not request.is_json:
            raw_body = request.get_data(as_text=True)
            print(f"Error: Request is not JSON. Raw body received: '{raw_body}'")
            return jsonify({
                "payload": { "success": False, "error": "Request Content-Type was not application/json"}
            }), 400

        data = request.json
        incoming_msg = data.get('message', '')
        sender_number = data.get('from', '')
        
        print(f"Received message from {sender_number}: '{incoming_msg}'")
        
        response_text = analyze_sms(incoming_msg)
        
        reply = {
            "payload": {
                "success": True,
                "messages": [
                    { "to": sender_number, "message": response_text }
                ]
            }
        }
        return jsonify(reply)

    except Exception as e:
        print(f"An error occurred in the main block: {e}")
        return jsonify({"payload": {"success": False, "error": "A server error occurred"}}), 500