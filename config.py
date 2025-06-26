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
    "description": "Matara's home of authentic Sri Lankan flavor"  # Brand description for marketing messages
}

# Menu Configuration
# Organized by meal categories for chatbot integration and customer browsing
MENU = {
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
}
