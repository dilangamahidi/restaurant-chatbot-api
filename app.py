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


# ✅ AGGIUNTO QUI - PRIMA del if __name__ == '__main__':
@app.route('/debug-ml')
def debug_ml():
    """Endpoint per debuggare il modello ML"""
    from ml_utils import test_ml_model, get_model_status
    
    # Testa il modello
    test_ml_model()
    
    return jsonify({
        'model_loaded': get_model_status(),
        'status': 'Debug completed - check console logs'
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Aggiungi questo test alla fine del tuo app.py per debug
@app.route('/test-sheets', methods=['GET'])
def test_sheets_endpoint():
    """Endpoint di test per Google Sheets"""
    try:
        from sheets_manager import init_google_sheets, save_reservation_to_sheets
        
        print("🔧 Testing Google Sheets connection...")
        
        # Test 1: Connessione
        sheet = init_google_sheets()
        if not sheet:
            return jsonify({"status": "error", "message": "Cannot connect to Google Sheets"})
        
        # Test 2: Lettura headers
        try:
            headers = sheet.row_values(1)
            print(f"📊 Sheet headers: {headers}")
        except Exception as e:
            headers = f"Error reading headers: {e}"
        
        # Test 3: Conteggio righe
        try:
            all_values = sheet.get_all_values()
            row_count = len(all_values)
            print(f"📊 Total rows: {row_count}")
        except Exception as e:
            row_count = f"Error counting rows: {e}"
        
        # Test 4: Test data
        test_reservation = {
            'name': 'TEST USER',
            'phone': '1234567890', 
            'email': 'test@test.com',
            'guests': 2,
            'date': '2024-01-01',
            'time': '12:00',
            'table': 1
        }
        
        # Test 5: Scrittura
        try:
            save_result = save_reservation_to_sheets(test_reservation)
            print(f"📊 Save result: {save_result}")
        except Exception as e:
            save_result = f"Error saving: {e}"
        
        return jsonify({
            "status": "success",
            "sheet_connected": True,
            "headers": headers,
            "row_count": row_count,
            "save_test": save_result,
            "sheet_id": "1CyXLrD9qltqODWzPI3Nx8bLec29dtm_thqBGf_bi35I"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc()
        })
