"""
Main Flask application for restaurant
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import traceback
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Import from our modules
from config import RESTAURANT_INFO
from ml_utils import get_model_status

# Import modularized handlers for different functionality areas
from reservation_handlers import (
    handle_make_reservation,
    handle_modify_reservation,
    handle_modify_reservation_date,
    handle_modify_reservation_time,
    handle_modify_reservation_guests,
    handle_cancel_reservation,
    handle_check_my_reservation,
    handle_check_table_specific
)
from info_handlers import (
    handle_show_menu,
    handle_opening_hours,
    handle_restaurant_info,
    handle_contact_human,
    handle_restaurant_location
)

# Initialize Flask application with CORS support for cross-origin requests
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes to allow frontend integration


@app.route('/')
def home():
    """Health check endpoint that returns basic application status"""
    return jsonify({
        'message': f'{RESTAURANT_INFO["name"]} API Running!', 
        'status': 'OK',
        'model_loaded': get_model_status()  # Check if ML model is properly loaded
    })


@app.route('/dialogflow-webhook', methods=['POST'])
def dialogflow_webhook():
    """Main webhook endpoint for Dialogflow with improved error handling"""
    try:
        # Extract JSON request from Dialogflow
        req = request.get_json()
        
        # Validate that request data exists
        if not req:
            return jsonify({'fulfillmentText': 'No request data received.'})
        
        # Parse Dialogflow request structure
        query_result = req.get('queryResult', {})
        intent = query_result.get('intent', {})
        intent_name = intent.get('displayName', '')
        parameters = query_result.get('parameters', {})
        
        # Log incoming request for debugging
        print(f"🔧 Intent: {intent_name}")
        print(f"🔧 Parameters: {parameters}")
        
        # Intent router - dispatch to appropriate handler based on intent name
        # Reservation management intents
        if intent_name == 'make.reservation':
            return handle_make_reservation(parameters)
        elif intent_name == 'check.table.specific':
            return handle_check_table_specific(parameters)
        elif intent_name == 'modify.reservation':
            return handle_modify_reservation(parameters)
        elif intent_name == 'cancel.reservation':
            return handle_cancel_reservation(parameters)
        elif intent_name == 'check.my.reservation':
            return handle_check_my_reservation(parameters)
        
        # Information request intents
        elif intent_name == 'show.menu':
            return handle_show_menu(parameters)
        elif intent_name == 'opening.hours':
            return handle_opening_hours()
        elif intent_name in ['restaurant.info']:
            return handle_restaurant_info()
        elif intent_name == 'contact.human':
            return handle_contact_human()
        elif intent_name == 'restaurant.location':
            return handle_restaurant_location()
        
        # Specific reservation modification intents
        elif intent_name == 'modify.reservation.date':
            return handle_modify_reservation_date(parameters)
        elif intent_name == 'modify.reservation.time':
            return handle_modify_reservation_time(parameters)
        elif intent_name == 'modify.reservation.guests':
            return handle_modify_reservation_guests(parameters)
        else:
            # Default welcome response for unrecognized intents
            response_text = f"🍽️ Welcome to {RESTAURANT_INFO['name']}! {RESTAURANT_INFO['description']}. I can help you check availability, make reservations, view our menu, or provide information. How can I assist you?"
            return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        # Global error handler for webhook failures
        print(f"❌ WEBHOOK ERROR: {e}")
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        
        # Return user-friendly error message with contact information
        return jsonify({
            'fulfillmentText': f"I'm experiencing technical difficulties. Please call us at {RESTAURANT_INFO['phone']} for immediate assistance."
        })

# Debug endpoint for ML model troubleshooting
@app.route('/debug-ml')
def debug_ml():
    """Endpoint for debugging ML model functionality"""
    from ml_utils import test_ml_model, get_model_status
    
    # Run comprehensive ML model tests
    test_ml_model()
    
    return jsonify({
        'model_loaded': get_model_status(),
        'status': 'Debug completed - check console logs'
    })

# Application entry point for production deployment
if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Run application with production-ready settings
    app.run(host='0.0.0.0', port=port, debug=False)
