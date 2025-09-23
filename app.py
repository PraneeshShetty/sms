import re
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse, Gather

# Initialize the Flask application
app = Flask(__name__)

# --- In-Memory Database for the MVP ---
# In a real application, you would use a proper database like SQLite, PostgreSQL, or a cloud DB.
# For a hackathon, a simple Python set is fast and easy.
# Pre-populate with a few known scam numbers (use E.164 format: [+][country code][number])
SCAM_NUMBERS = {"+14155552671", "+12125552368"} # Example numbers

# --- Logic for SMS Fraud Detection ---
def analyze_sms(message_body):
    """
    A simple rule-based engine to check for common scam phrases.
    Returns a tuple: (Classification, Response Message)
    """
    # Regex to find common scam keywords. 're.I' makes it case-insensitive.
    scam_pattern = re.compile(
        r'congratulations|you have won|lottery|prize|urgent|act now|account blocked|verify your pin|share your otp|kyc|bit\.ly',
        re.IGNORECASE
    )
    
    if re.search(scam_pattern, message_body):
        # If any keyword is found, classify as FRAUD
        classification = "FRAUD 🚨"
        response_text = "⚠️ WARNING: This message looks like a scam. Do not click any links or share personal information. Stay safe!"
    else:
        # Otherwise, classify as SAFE
        classification = "SAFE ✅"
        response_text = "✅ This message appears to be safe. Always be careful with unknown senders."
        
    print(f"Analyzed SMS. Classification: {classification}")
    return (classification, response_text)

# --- Webhook for Incoming SMS ---
@app.route("/sms", methods=['POST'])
def handle_sms():
    """Handles incoming SMS messages."""
    incoming_msg = request.values.get('Body', '').lower()
    print(f"Incoming SMS from {request.values.get('From')}: {incoming_msg}")
    
    # Analyze the message content
    _, response_text = analyze_sms(incoming_msg)
    
    # Create a TwiML response to send back a reply SMS
    resp = MessagingResponse()
    resp.message(response_text)
    
    return str(resp)

# --- Webhooks for Voice Calls (IVR) ---

# 1. Main entry point for calls
@app.route("/voice", methods=['POST'])
def handle_voice():
    """Handles incoming voice calls and presents the IVR menu."""
    resp = VoiceResponse()
    
    # Use <Gather> to collect the user's menu selection
    gather = Gather(num_digits=1, action='/handle-key', method='POST')
    gather.say(
        "Welcome to Fraud Guard. This call is in English. "
        "To check if a phone number is a scam, press 1. "
        "To report a scam number, press 2.",
        language="en-US" # Specify language for clarity
    )
    resp.append(gather)
    
    # If the user doesn't press a key, repeat the message
    resp.redirect('/voice')
    
    return str(resp)

# 2. Handle the key press from the main menu
@app.route("/handle-key", methods=['POST'])
def handle_key():
    """Handles the digit pressed by the user in the main IVR menu."""
    digit_pressed = request.values.get('Digits')
    resp = VoiceResponse()

    if digit_pressed == '1':
        # User wants to check a number
        gather = Gather(input='dtmf', num_digits=10, action='/check-number', method='POST')
        gather.say("Please enter the 10-digit phone number you want to check, then press the hash key.", language="en-US")
        resp.append(gather)
        resp.redirect('/voice') # If they don't enter anything, go back to the main menu
        return str(resp)
        
    elif digit_pressed == '2':
        # User wants to report a number
        gather = Gather(input='dtmf', num_digits=10, action='/report-number', method='POST')
        gather.say("Please enter the 10-digit scam number you want to report, then press the hash key.", language="en-US")
        resp.append(gather)
        resp.redirect('/voice') # If they don't enter anything, go back to the main menu
        return str(resp)

    else:
        # Invalid input
        resp.say("Sorry, that is not a valid choice. Please try again.", language="en-US")
        resp.redirect('/voice')
        return str(resp)

# 3. Check the number against our database
@app.route("/check-number", methods=['POST'])
def check_number():
    """Checks the entered number against the SCAM_NUMBERS set."""
    entered_number = request.values.get('Digits')
    # IMPORTANT: Format the number to the E.164 standard for reliable comparison
    # We assume an Indian number for this example. Adjust the country code as needed.
    formatted_number = f"+91{entered_number}"
    
    resp = VoiceResponse()
    if formatted_number in SCAM_NUMBERS:
        resp.say("This number has been previously reported for fraud. Please be very careful.", language="en-US")
    else:
        resp.say("We do not have any fraud reports for this number. However, always remain cautious.", language="en-US")
    
    resp.say("Thank you for using Fraud Guard. Goodbye.", language="en-US")
    resp.hangup()
    return str(resp)

# 4. Report a new scam number
@app.route("/report-number", methods=['POST'])
def report_number():
    """Adds the entered number to our SCAM_NUMBERS set."""
    entered_number = request.values.get('Digits')
    formatted_number = f"+91{entered_number}"
    
    # Add the number to our "database"
    SCAM_NUMBERS.add(formatted_number)
    print(f"New number reported: {formatted_number}. Current database: {SCAM_NUMBERS}")
    
    resp = VoiceResponse()
    resp.say("Thank you. The number has been successfully reported and added to our fraud database.", language="en-US")
    resp.say("Goodbye.", language="en-US")
    resp.hangup()
    return str(resp)


if __name__ == "__main__":
    # Run the Flask app. Debug=True allows for auto-reloading when you save changes.
    app.run(debug=True)