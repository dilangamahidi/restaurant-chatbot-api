"""
Main Flask application for restaurant - Modularized with multilingual support
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import json  # 🚨 AGGIUNTO: Import mancante
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
app.config['JSON_SORT_KEYS'] = False

# Imposta gli headers UTF-8 per tutte le risposte
@app.after_request
def after_request(response):
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

# 🚨 CORRETTO: Personalizza il JSON encoder per forzare UTF-8
class UnicodeJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        if isinstance(obj, dict):
            return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
        return super().encode(obj)

# 🚨 CORRETTO: Usa l'attributo corretto per Flask
app.json_encoder = UnicodeJSONEncoder


def detect_language_fallback(text):
    """Detect language if Dialogflow doesn't provide it - IMPROVED VERSION"""
    if not text:
        return 'en'
    
    text = str(text).lower()
    
    # Sinhala characters - expanded set
    sinhala_chars = set('අආඇඈඉඊඋඌඍඎඏඐඑඒඓඔඕඖකඛගඝඞචඡජඣඤටඨඩඪණතථදධනපඵබභමයරලවශෂසහළ')
    
    # Tamil characters - expanded set  
    tamil_chars = set('அஆஇஈஉஊஎஏஐஒஓஔகஙசஞடணதநபமயரலவழளறனஷஸஹ')
    
    # Sinhala common words
    sinhala_words = {
        'මේසයක්', 'වෙන්කර', 'ගන්න', 'මෙනුව', 'පෙන්වන්න', 'කෑම', 'තියෙන්නේ',
        'විවෘත', 'වේලාවන්', 'මොනවද', 'කවදද', 'ඉස්සන්', 'restaurant', 'එක',
        'දෙනෙකුට', 'හෙට', 'රාත්‍රී', 'උදේ', 'දිවා', 'අද', 'සඳුදා', 'අඟහරුවාදා'
    }
    
    # Tamil common words  
    tamil_words = {
        'மேஜை', 'முன்பதிவு', 'மெனு', 'காட்டுங்கள்', 'உணவு', 'இருக்கிறது',
        'நேரம்', 'திறந்திருக்கும்', 'எப்போது', 'இன்று', 'நாளை', 'இரவு', 'காலை'
    }
    
    # Count Sinhala characters
    sinhala_char_count = sum(1 for char in text if char in sinhala_chars)
    
    # Count Tamil characters
    tamil_char_count = sum(1 for char in text if char in tamil_chars)
    
    # Check for Sinhala words
    sinhala_word_count = sum(1 for word in sinhala_words if word in text)
    
    # Check for Tamil words
    tamil_word_count = sum(1 for word in tamil_words if word in text)
    
    print(f"🔧 Language detection: text='{text}'")
    print(f"🔧 Sinhala chars: {sinhala_char_count}, words: {sinhala_word_count}")
    print(f"🔧 Tamil chars: {tamil_char_count}, words: {tamil_word_count}")
    
    # Determine language based on character and word counts
    if sinhala_char_count > 0 or sinhala_word_count > 0:
        return 'si'
    elif tamil_char_count > 0 or tamil_word_count > 0:
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
    """Main webhook endpoint for Dialogflow with improved multilingual support"""
    try:
        # Extract JSON request from Dialogflow
        req = request.get_json()
        
        print(f"🔧 DEBUG - Full request: {req}")
        
        # Validate that request data exists
        if not req:
            return jsonify({'fulfillmentText': 'No request data received.'})
        
        # Parse Dialogflow request structure
        query_result = req.get('queryResult', {})
        query_text = query_result.get('queryText', '')
        
        # 🚨 DEBUG ENCODING AGGIUNTO
        print(f"🔧 DEBUG - Query text: '{query_text}'")
        print(f"🔧 RAW query_text: {repr(query_text)}")
        print(f"🔧 query_text UTF-8: {query_text.encode('utf-8')}")
        
        # Detect language
        language_code = query_result.get('languageCode', 'en')
        print(f"🔧 DEBUG - Dialogflow language: '{language_code}'")
        
        # ALWAYS check for language in query text regardless of Dialogflow language
        detected_lang = detect_language_fallback(query_text)
        print(f"🔧 DEBUG - Detected language: '{detected_lang}'")
        
        # Use detected language if it's not English or if Dialogflow didn't detect properly
        if detected_lang != 'en':
            language_code = detected_lang
            print(f"🔧 DEBUG - Using detected language: '{language_code}'")
        
        # Handle the intent with language support
        response = handle_intent(query_result, language_code)
        
        # 🚨 DEBUG RESPONSE AGGIUNTO
        print(f"🔧 RAW response: {repr(response.get_data())}")
        
        return response
        
    except Exception as e:
        print(f"❌ WEBHOOK ERROR: {e}")
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        
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


@app.route('/test-language', methods=['POST'])
def test_language():
    """Test endpoint for language detection"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        detected = detect_language_fallback(text)
        
        from translations import get_text
        welcome_msg = get_text('welcome', detected, restaurant=RESTAURANT_INFO['name'], description=RESTAURANT_INFO['description'])
        
        return jsonify({
            'input_text': text,
            'detected_language': detected,
            'welcome_message': welcome_msg,
            'available_languages': ['en', 'si', 'ta']
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/test-sinhala')
def test_sinhala():
    """Quick test for Sinhala"""
    test_phrases = [
        "මේසයක් වෙන්කර ගන්න",
        "මෙනුව පෙන්වන්න", 
        "විවෘත වේලාවන් මොනවද"
    ]
    
    results = {}
    for phrase in test_phrases:
        detected = detect_language_fallback(phrase)
        results[phrase] = detected
    
    response_data = {
        'test_results': results,
        'expected': 'si'
    }
    
    # Usa la stessa logica UTF-8 dell'altro endpoint
    json_string = json.dumps(response_data, ensure_ascii=False, indent=2)
    
    return Response(
        json_string,
        content_type='application/json; charset=utf-8'
    )


@app.route('/test-sinhala-direct')
def test_sinhala_direct():
    """Test diretto per caratteri singalesi"""
    from translations import get_text
    
    sinhala_text = get_text('welcome', 'si', 
                           restaurant=RESTAURANT_INFO['name'], 
                           description=RESTAURANT_INFO['description'])
    
    response_data = {
        'fulfillmentText': sinhala_text,
        'test_status': 'success',
        'language': 'si'
    }
    
    # Forza UTF-8 encoding
    json_string = json.dumps(response_data, ensure_ascii=False, indent=2)
    
    return Response(
        json_string,
        content_type='application/json; charset=utf-8'
    )

@app.route('/debug-webhook', methods=['POST'])
def debug_webhook():
    """Debug endpoint to see raw Dialogflow requests"""
    req = request.get_json()
    
    print("🔧 === FULL DIALOGFLOW REQUEST ===")
    print(json.dumps(req, indent=2, ensure_ascii=False))
    
    query_result = req.get('queryResult', {})
    intent_name = query_result.get('intent', {}).get('displayName', 'UNKNOWN')
    query_text = query_result.get('queryText', '')
    language_code = query_result.get('languageCode', 'unknown')
    
    response = {
        'fulfillmentText': f"DEBUG: Intent='{intent_name}', Query='{query_text}', Lang='{language_code}'"
    }
    
    return jsonify(response)


# Application entry point for production deployment
if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Run application with production-ready settings
    app.run(host='0.0.0.0', port=port, debug=False)
