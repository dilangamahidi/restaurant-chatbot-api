"""
Configuration and constants for the restaurant application
"""

# Google Sheets API Configuration
# These scopes define what permissions the application needs to access Google services
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',  # Permission to read and write Google Sheets
    'https://www.googleapis.com/auth/drive'          # Permission to access Google Drive files
]

# Google Sheets Document ID for storing reservation data
# This is the unique identifier for the specific spreadsheet where reservations are stored
# Format: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
SHEET_ID = "1CyXLrD9qltqODWzPI3Nx8bLec29dtm_thqBGf_bi35I"

# Restaurant Information - UPDATED FOR RESTORAN
# This dictionary contains all the essential business information
# Used throughout the application for contact details, confirmations, and customer communications
RESTAURANT_INFO = {
    "name": "Restoran",                                        # Restaurant brand name
    "phone": "0764272635",                                     # Primary contact number for customers
    "email": "dilangakavindu123@gmail.com",                   # Email for reservations and admin notifications
    "address": "Aluthgoga Road, Mawella, Nakulugamuwa, Matara",  # Full physical address for customer reference
    "description": {
        "en": "Matara's home of authentic Sri Lankan flavor",
        "si": "අව්‍යාජ ශ්‍රී ලාංකික රස සහිත මාතර නිවස",
        "ta": "உண்மையான இலங்கை சுவையின் மாத்தறை வீடு"
    }
}

# Menu Configuration
# Organized by meal categories for chatbot integration and customer browsing
MENU = {
    "en": {
        "breakfast": [
            "String Hoppers with Curry",
            "Milk Rice (Kiribath)",
            "Coconut Roti with Sambol",
            "Ceylon Tea"
        ],
        
        "lunch": [
            "Rice and Curry",
            "Kottu Roti",
            "Fried Rice",
            "Hoppers with Egg"
        ],
        
        "dinner": [
            "Fish Curry",
            "Chicken Curry",
            "Seafood Platter",
            "Vegetarian Curry"
        ],
        
        "beverages": [
            "King Coconut",
            "Ceylon Tea",
            "Fresh Juices",
            "Local Beer"
        ]
    },
    
    "si": {
        "breakfast": [
            "ඉදිඇප්ප කරි සමඟ",
            "කිරිබත්",
            "පොල්රොටි සම්බෝල සමඟ",
            "ලංකා තේ"
        ],
        
        "lunch": [
            "බත් සහ කරි",
            "කොත්තු රොටි",
            "පලපාන් බත්",
            "හොප්පර්ස් බිත්තර සමඟ"
        ],
        
        "dinner": [
            "මාලු කරි",
            "කුකුල් මස් කරි",
            "මුහුදු ආහාර පිඟාන",
            "නිර්මාංශ කරි"
        ],
        
        "beverages": [
            "කිං කොකනට්",
            "ලංකා තේ",
            "නැවුම් පලතුරු යුෂ",
            "දේශීය බියර්"
        ]
    },
    
    "ta": {
        "breakfast": [
            "இடியப்பம் கறியுடன்",
            "பால் சாதம் (கிරிபத්)",
            "தேங்காய் ரொட்டி சம்பாளுடன்",
            "லங்கா தேநீர்"
        ],
        
        "lunch": [
            "சாதம் மற்றும் கறி",
            "கொத்து ரொட்டி",
            "வறுத்த சாதம்",
            "ஹாப்பர்ஸ் முட்டையுடன்"
        ],
        
        "dinner": [
            "மீன் கறி",
            "கோழி கறி",
            "கடல்உணவு தட்டு",
            "சைவ கறி"
        ],
        
        "beverages": [
            "இராஜ தென்னம்பழம்",
            "லங்கா தேநீர்",
            "புதிய பழரசங்கள்",
            "உள்ளூர் பீர்"
        ]
    }
}
