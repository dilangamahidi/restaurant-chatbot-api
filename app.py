from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np

app = Flask(__name__)
CORS(app)

# Carica modello ML
try:
    model = joblib.load('restaurant_model_client.pkl')
    print("✅ ML Model loaded!")
except:
    print("❌ Model not found!")
    model = None

RESTAURANT_INFO = {
    "name": "Your Restaurant Name",
    "phone": "+1 (555) 123-4567",
    "email": "info@yourrestaurant.com"
}

MENU = {
    "appetizers": ["Caesar Salad", "Bruschetta", "Calamari Rings"],
    "main_courses": ["Grilled Salmon", "Pasta Carbonara", "Ribeye Steak"],
    "desserts": ["Tiramisu", "Chocolate Cake", "Gelato"],
    "beverages": ["Wine Selection", "Craft Beer", "Coffee"]
}

def check_table_availability(table_number, guest_count, day_of_week, hour_of_day):
    if model is None:
        return False
    try:
        input_data = np.array([[table_number, guest_count, day_of_week, hour_of_day]])
        prediction = model.predict(input_data)[0]
        return prediction == 0
    except:
        return False

@app.route('/')
def home():
    return jsonify({'message': 'Restaurant API Running!', 'status': 'OK'})

@app.route('/dialogflow-webhook', methods=['POST'])
def dialogflow_webhook():
    try:
        req = request.get_json()
        intent_name = req.get('queryResult', {}).get('intent', {}).get('displayName', '')
        parameters = req.get('queryResult', {}).get('parameters', {})
        
        if intent_name == 'check.availability':
            guests = parameters.get('guest_count', 2)
            guest_count = int(guests) if guests else 2
            
            day_of_week = 5  # Saturday
            hour_of_day = 19  # 7 PM
            
            for table_number in range(1, 21):
                if check_table_availability(table_number, guest_count, day_of_week, hour_of_day):
                    response_text = f"Great! Table {table_number} is available for {guest_count} guests. Would you like to make a reservation? I'll need your name and phone number."
                    break
            else:
                response_text = f"Sorry, no tables available for {guest_count} guests at that time. Would you like to try a different time? Call us at {RESTAURANT_INFO['phone']}."
                
        elif intent_name == 'show.menu':
            menu_text = "Here's our menu:\n\n"
            menu_text += "🥗 Appetizers: " + ", ".join(MENU['appetizers']) + "\n"
            menu_text += "🍽️ Main Courses: " + ", ".join(MENU['main_courses']) + "\n"
            menu_text += "🍰 Desserts: " + ", ".join(MENU['desserts']) + "\n"
            menu_text += "🥤 Beverages: " + ", ".join(MENU['beverages'])
            response_text = menu_text
            
        elif intent_name == 'restaurant.info':
            response_text = f"We are {RESTAURANT_INFO['name']}. You can reach us at {RESTAURANT_INFO['phone']} or {RESTAURANT_INFO['email']}."
            
        else:
            response_text = "Hello! Welcome to our restaurant. How can I help you today?"
        
        return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        return jsonify({'fulfillmentText': f"Sorry, I'm having technical difficulties. Please call {RESTAURANT_INFO['phone']}."})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
