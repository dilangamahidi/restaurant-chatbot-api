"""
Handlers per la gestione delle informazioni del ristorante
"""
from flask import jsonify

# Importa da nostri moduli
from config import RESTAURANT_INFO, MENU


def handle_show_menu(parameters):
    """Gestisce visualizzazione menu - MULTIPLE MESSAGES"""
    menu_category = parameters.get('menu-category', '').lower()
    
    if menu_category and menu_category in MENU:
        items = MENU[menu_category]
        response_text = f"🍽️ {menu_category.title()} Menu:\n\n" + "\n".join([f"{i}. {item}" for i, item in enumerate(items, 1)])
        return jsonify({'fulfillmentText': response_text})
    else:
        # Dividi in messaggi separati
        rich_response = {
            "fulfillmentText": f"🍽️ {RESTAURANT_INFO['name']} Menu:",
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [f"🍽️ {RESTAURANT_INFO['name']} Menu:"]
                    }
                },
                {
                    "text": {
                        "text": [f"☀️ BREAKFAST:\n" + "\n".join([f"• {item}" for item in MENU['breakfast']])]
                    }
                },
                {
                    "text": {
                        "text": [f"🍛 LUNCH:\n" + "\n".join([f"• {item}" for item in MENU['lunch']])]
                    }
                },
                {
                    "text": {
                        "text": [f"🌅 DINNER:\n" + "\n".join([f"• {item}" for item in MENU['dinner']])]
                    }
                },
                {
                    "text": {
                        "text": [f"🥤 BEVERAGES:\n" + "\n".join([f"• {item}" for item in MENU['beverages']])]
                    }
                },
            ]
        }
        return jsonify(rich_response)


def handle_opening_hours():
    """Gestisce orari apertura - MULTIPLE MESSAGES"""
    rich_response = {
        "fulfillmentText": f"🕐 {RESTAURANT_INFO['name']} Opening Hours:",
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [f"🕐 {RESTAURANT_INFO['name']} Opening Hours:"]
                }
            },
            {
                "text": {
                    "text": ["📅 Monday - Saturday:\n09:00 AM - 09:00 PM"]
                }
            },
            {
                "text": {
                    "text": ["📅 Sunday:\n10:00 AM - 08:00 PM"]
                }
            },
        ]
    }
    return jsonify(rich_response)


def handle_restaurant_info():
    """Gestisce info ristorante - MULTIPLE MESSAGES"""
    rich_response = {
        "fulfillmentText": f"🍽️ {RESTAURANT_INFO['name']}",
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [f"🍽️ {RESTAURANT_INFO['name']}"]
                }
            },
            {
                "text": {
                    "text": [f"{RESTAURANT_INFO['description']}"]
                }
            },
            {
                "text": {
                    "text": [f"📍 Address:\n{RESTAURANT_INFO['address']}"]
                }
            },
            {
                "text": {
                    "text": [f"📞 Phone:\n{RESTAURANT_INFO['phone']}"]
                }
            },
            {
                "text": {
                    "text": [f"📧 Email:\n{RESTAURANT_INFO['email']}"]
                }
            },
            {
                "text": {
                    "text": ["🕐 Hours:\nMon-Sat 9AM-9PM\nSun 10AM-8PM"]
                }
            }
        ]
    }
    return jsonify(rich_response)


def handle_contact_human():
    """Gestisce contatto umano - MULTIPLE MESSAGES"""
    rich_response = {
        "fulfillmentText": "👨‍💼 Contact our staff:",
        "fulfillmentMessages": [
            {
                "text": {
                    "text": ["👨‍💼 Contact our staff:"]
                }
            },
            {
                "text": {
                    "text": [f"📞 Call:\n{RESTAURANT_INFO['phone']}"]
                }
            },
            {
                "text": {
                    "text": [f"📧 Email:\n{RESTAURANT_INFO['email']}"]
                }
            },
        ]
    }
    return jsonify(rich_response)


def handle_restaurant_location():
    """Gestisce richiesta location ristorante - MULTIPLE MESSAGES"""
    rich_response = {
        "fulfillmentText": f"📍 {RESTAURANT_INFO['name']} Location:",
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [f"📍 {RESTAURANT_INFO['name']} Location:"]
                }
            },
            {
                "text": {
                    "text": [f"🏠 Address:\n{RESTAURANT_INFO['address']}"]
                }
            },
        ]
    }
    return jsonify(rich_response)
