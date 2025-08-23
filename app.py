"""
Main Flask application for restaurant - Modularized with multilingual support
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

# Ensure UTF-8 encoding for multilingual support
app.config['JSON_AS_ASCII'] = False


def detect_language_fallback(text):
    """Detect language if Dialogflow doesn't provide it"""
    # Sinhala characters
    sinhala_chars = set('අආඇඈඉඊඋඌඍඎඏඐඑඒඓඔඕඖකඛගඝඞචඡජඣඤටඨඩඪණතථදධනපඵබභමයරලවශෂසහළ')
    # Tamil characters  
    tamil_chars = set('அஆஇஈஉஊஎஏஐஒஓஔகஙசஞடணதநபமயரலவழளறனஷஸஹ')
    
    if any(char in sinhala_chars for char in text):
        return 'si'
    elif any(char in tamil_chars for char in text):
        return 'ta'
    else:
        return 'en'


def handle_intent(query_result, language_code):
    """Handle intent with language support"""
    intent = query_result.get('intent', {})
    intent_name = intent.get('displayName', '')
    parameters = query_result.get('parameters', {})
    
    # Log incoming request for debugging
    print(f"🔧 Intent: {intent_name}")
    print(f"🔧 Language: {language_code}")
    print(f"🔧 Parameters: {parameters}")
    
    # Pass language to handlers that support it
    if hasattr(globals().get(f'handle_{intent_name.replace(".", "_")}', lambda x: None), '__code__'):
        # Check if handler accepts language parameter
        try:
            # Try to pass language to handlers
            if intent_name == 'make.reservation':
                return handle_make_reservation(parameters, language_code)
            elif intent_name == 'check.table.specific':
                return handle_check_table_specific(parameters, language_code)
            elif intent_name == 'modify.reservation':
                return handle_modify_reservation(parameters, language_code)
            elif intent_name == 'cancel.reservation':
                return handle_cancel_reservation(parameters, language_code)
            elif intent_name == 'check.my.reservation':
                return handle_check_my_reservation(parameters, language_code)
            elif intent_name == 'show.menu':
                return handle_show_menu(parameters, language_code)
            elif intent_name == 'opening.hours':
                return handle_opening_hours(language_code)
            elif intent_name in ['restaurant.info']:
                return handle_restaurant_info(language_code)
            elif intent_name == 'contact.human':
                return handle_contact_human(language_code)
            elif intent_name == 'restaurant.location':
                return handle_restaurant_location(language_code)
            elif intent_name == 'modify.reservation.date':
                return handle_modify_reservation_date(parameters, language_code)
            elif intent_name == 'modify.reservation.time':
                return handle_modify_reservation_time(parameters, language_code)
            elif intent_name == 'modify.reservation.guests':
                return handle_modify_reservation_guests(parameters, language_code)
        except TypeError:
            # Fallback to original handlers without language parameter
            pass
    
    # Fallback to original intent routing (without language support)
    return handle_intent_fallback(intent_name, parameters, language_code)


def handle_intent_fallback(intent_name, parameters, language_code):
    """Fallback intent handler for compatibility"""
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
        # Default welcome response for unrecognized intents (multilingual)
        from translations import get_text
        response_text = get_text('welcome', language_code, 
                                restaurant=RESTAURANT_INFO['name'], 
                                description=RESTAURANT_INFO['description'])
        return jsonify({'fulfillmentText': response_text})


def handle_error(error, language_code='en'):
    """Handle errors with multilingual support"""
    print(f"❌ WEBHOOK ERROR: {error}")
    print(f"❌ TRACEBACK: {traceback.format_exc()}")
    
    # Multilingual error messages
    error_messages = {
        'en': f"I'm experiencing technical difficulties. Please call us at {RESTAURANT_INFO['phone']} for immediate assistance.",
        'si': f"මට තාක්ෂණික ගැටළුවක් ඇති වී ඇත. කරුණාකර {RESTAURANT_INFO['phone']} අමතන්න.",
        'ta': f"எனக்கு தொழில்நுட்ப சிக்கல் உள்ளது. தயவுசெய்து {RESTAURANT_INFO['phone']} அழைக்கவும்."
    }
    
    error_message = error_messages.get(language_code, error_messages['en'])
    
    return jsonify({
        'fulfillmentText': error_message
    })


@app.route('/')
def home():
    """Health check endpoint that returns basic application status"""
    return jsonify({
        'message': f'{RESTAURANT_INFO["name"]} API Running!', 
        'status': 'OK',
        'model_loaded': get_model_status(),
        'supported_languages': ['en', 'si', 'ta']
    })


@app.route('/dialogflow-webhook', methods=['POST'])
def dialogflow_webhook():
    """Main webhook endpoint for Dialogflow with multilingual support"""
    try:
        # Extract JSON request from Dialogflow
        req = request.get_json()
        
        # Validate that request data exists
        if not req:
            return jsonify({'fulfillmentText': 'No request data received.'})
        
        # Parse Dialogflow request structure
        query_result = req.get('queryResult', {})
        
        # Detect language
        language_code = query_result.get('languageCode', 'en')
        
        # Fallback language detection if not provided by Dialogflow
        if language_code == 'en':
            query_text = query_result.get('queryText', '')
            detected_lang = detect_language_fallback(query_text)
            if detected_lang != 'en':
                language_code = detected_lang
        
        # Handle the intent with language support
        return handle_intent(query_result, language_code)
        
    except Exception as e:
        # Get language for error handling
        try:
            language_code = request.get_json().get('queryResult', {}).get('languageCode', 'en')
        except:
            language_code = 'en'
            
        return handle_error(e, language_code)


@app.route('/test')
def test():
    """Test endpoint to verify ML model functionality"""
    from ml_utils import find_available_table
    
    # Check if ML model is loaded before testing
    if not get_model_status():
        return jsonify({'error': 'Model not loaded'})
    
    # Test availability check with sample data
    result = find_available_table(4, 5, 19)  # 4 guests, Saturday, 7PM
    
    return jsonify({
        'model_loaded': get_model_status(),
        'test_result': result,
        'restaurant': RESTAURANT_INFO['name'],
        'supported_languages': ['en', 'si', 'ta']
    })


@app.route('/ping')
def ping():
    """Keep-alive endpoint to prevent cold starts in cloud deployment"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': get_model_status(),
        'uptime': 'running',
        'languages': ['en', 'si', 'ta']
    })


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


@app.route('/test-translation')
def test_translation():
    """Test endpoint for multilingual functionality"""
    try:
        from translations import get_text
        
        test_results = {}
        for lang in ['en', 'si', 'ta']:
            test_results[lang] = {
                'welcome': get_text('welcome', lang, restaurant=RESTAURANT_INFO['name'], description=RESTAURANT_INFO['description']),
                'reservation_confirmed': get_text('reservation_confirmed', lang, name='Test', guests=2, date='Tomorrow', time='7PM', table=5),
                'menu_header': get_text('menu_header', lang, restaurant=RESTAURANT_INFO['name'])
            }
        
        return jsonify({
            'status': 'Translation test completed',
            'results': test_results
        })
    except ImportError:
        return jsonify({
            'error': 'Translation module not found',
            'message': 'Please create translations.py module'
        })


# Application entry point for production deployment
if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Run application with production-ready settings
    app.run(host='0.0.0.0', port=port, debug=False)
