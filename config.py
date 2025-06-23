# config.py
# Configurazioni centrali per il Restaurant Chatbot

import os

# Google Sheets Configuration
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SHEET_ID = "1QTaGoxeQur4Rh03tJETcRwExbmTvU1FF6TE1v0UjuMk"

# Restaurant Information
RESTAURANT_INFO = {
    "name": "Restoran",
    "phone": "0764272635",
    "email": "dilangakavindu123@gmail.com",
    "address": "Aluthgoga Road, Mawella, Nakulugamuwa, Matara",
    "description": "Matara's home of authentic Sri Lankan flavor"
}

# Menu Sri Lankano
MENU = {
    "breakfast": ["String Hoppers with Curry", "Milk Rice (Kiribath)", "Coconut Roti with Sambol", "Ceylon Tea"],
    "lunch": ["Rice and Curry", "Kottu Roti", "Fried Rice", "Hoppers with Egg"],
    "dinner": ["Fish Curry", "Chicken Curry", "Seafood Platter", "Vegetarian Curry"],
    "beverages": ["King Coconut", "Ceylon Tea", "Fresh Juices", "Local Beer"]
}

# ML Model Configuration
MODEL_PATH = 'restaurant_model_client.pkl'

# Table Configuration
TOTAL_TABLES = 20
TABLE_CATEGORIES = {
    'small': range(1, 9),    # Tables 1-8 for 1-2 guests
    'medium': range(9, 16),  # Tables 9-15 for 3-4 guests
    'large': range(16, 21)   # Tables 16-20 for 5+ guests
}

# Restaurant Hours
RESTAURANT_HOURS = {
    'weekday': {'open': 9, 'close': 21},    # 9 AM - 9 PM
    'sunday': {'open': 10, 'close': 20}     # 10 AM - 8 PM
}

# Validation Rules
VALIDATION = {
    'min_guests': 1,
    'max_guests': 20,
    'min_name_length': 2,
    'phone_pattern': r'^[\d\s\-\+\(\)]+$',
    'email_pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
}

# Debug Configuration
DEBUG_MODE = os.environ.get('DEBUG', 'False').lower() == 'true'
VERBOSE_LOGGING = os.environ.get('VERBOSE_LOGGING', 'True').lower() == 'true'

# Word to Number Mapping for Guests
WORD_TO_NUMBER = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
}

# Day of Week Mapping
DAY_NAME_TO_NUMBER = {
    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
    'friday': 4, 'saturday': 5, 'sunday': 6,
    'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
}

DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Google Sheets Column Mapping (1-based)
SHEET_COLUMNS = {
    'timestamp': 1,  # Column A
    'name': 2,       # Column B
    'phone': 3,      # Column C
    'email': 4,      # Column D
    'guests': 5,     # Column E
    'date': 6,       # Column F
    'time': 7,       # Column G
    'table': 8,      # Column H
    'status': 9      # Column I
}

# Default Values
DEFAULTS = {
    'guest_count': 2,
    'day_of_week': 5,    # Saturday
    'hour_of_day': 19,   # 7 PM
    'table_number': 1
}

# Error Messages
ERROR_MESSAGES = {
    'no_model': "ML Model not available",
    'sheets_error': "Error connecting to Google Sheets",
    'parsing_error': "Error parsing date/time",
    'no_availability': "No tables available",
    'validation_error': "Validation failed",
    'general_error': f"Technical difficulties. Please call us at {RESTAURANT_INFO['phone']}"
}

# Success Messages
SUCCESS_MESSAGES = {
    'reservation_created': "🎉 Reservation Confirmed!",
    'reservation_updated': "✅ Reservation updated successfully!",
    'reservation_cancelled': "✅ Reservation cancelled successfully!"
}
