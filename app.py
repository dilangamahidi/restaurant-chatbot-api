"""
App Flask principale per il ristorante - Versione modularizzata e ridotta
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import traceback
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Importa da nostri moduli
from config import RESTAURANT_INFO
from ml_utils import get_model_status

# Importa gli handlers modularizzati
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

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return jsonify({
        'message': f'{RESTAURANT_INFO["name"]} API Running!', 
        'status': 'OK',
        'model_loaded': get_model_status()
    })


@app.route('/dialogflow-webhook', methods=['POST'])
def dialogflow_webhook():
    """Webhook principale per Dialogflow con controlli migliorati"""
    try:
        req = request.get_json()
        
        if not req:
            return jsonify({'fulfillmentText': 'No request data received.'})
        
        query_result = req.get('queryResult', {})
        intent = query_result.get('intent', {})
        intent_name = intent.get('displayName', '')
        parameters = query_result.get('parameters', {})
        
        print(f"🔧 Intent: {intent_name}")
        print(f"🔧 Parameters: {parameters}")
        
        # Router degli intent verso i rispettivi handler
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
        elif intent_name == 'modify.reservation.date':
            return handle_modify_reservation_date(parameters)
        elif intent_name == 'modify.reservation.time':
            return handle_modify_reservation_time(parameters)
        elif intent_name == 'modify.reservation.guests':
            return handle_modify_reservation_guests(parameters)
        else:
            # Default welcome
            response_text = f"🍽️ Welcome to {RESTAURANT_INFO['name']}! {RESTAURANT_INFO['description']}. I can help you check availability, make reservations, view our menu, or provide information. How can I assist you?"
            return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        print(f"❌ WEBHOOK ERROR: {e}")
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        
        return jsonify({
            'fulfillmentText': f"I'm experiencing technical difficulties. Please call us at {RESTAURANT_INFO['phone']} for immediate assistance."
        })


@app.route('/test')
def test():
    """Test endpoint per verificare funzionalità"""
    from ml_utils import find_available_table
    
    if not get_model_status():
        return jsonify({'error': 'Model not loaded'})
    
    # Test availability
    result = find_available_table(4, 5, 19)  # 4 guests, Saturday, 7PM
    
    return jsonify({
        'model_loaded': get_model_status(),
        'test_result': result,
        'restaurant': RESTAURANT_INFO['name']
    })


@app.route('/ping')
def ping():
    """Keep-alive endpoint per evitare cold starts"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': get_model_status(),
        'uptime': 'running'
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
