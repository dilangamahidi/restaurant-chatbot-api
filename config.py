"""
Configurazioni e costanti per l'applicazione ristorante
"""

# Google Sheets Configuration
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SHEET_ID = "1QTaGoxeQur4Rh03tJETcRwExbmTvU1FF6TE1v0UjuMk"

# Info ristorante - AGGIORNATE PER RESTORAN
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
