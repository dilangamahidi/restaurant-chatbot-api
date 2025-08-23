# translations.py
TRANSLATIONS = {
    'en': {
        'reservation_confirmed': '🎉 Reservation confirmed for {name}! {guests} guests on {date} at {time}, Table {table}.',
        'no_availability': '😔 Sorry, no availability for {guests} guests on {date} at {time}.',
        'invalid_time': 'Sorry, we\'re only open from 9:00 AM to 9:00 PM.',
        'menu_header': '🍽️ {restaurant} Menu:',
        'breakfast': '☀️ BREAKFAST:',
        'lunch': '🍛 LUNCH:',
        'dinner': '🌅 DINNER:',
        'beverages': '🥤 BEVERAGES:',
        'opening_hours': '🕐 {restaurant} Opening Hours:',
        'contact_staff': '👨‍💼 Contact our staff:',
        'phone_needed': 'Please provide your phone number to find your reservation.'
    },
    'si': {
        'reservation_confirmed': '🎉 {name}ගේ වෙන්කර ගැනීම සනාථ කරන ලදී! {date} දින {time}ට {guests} දෙනෙකු, {table} මේසය.',
        'no_availability': '😔 සමාවන්න, {date} දින {time}ට {guests} දෙනෙකුට ඉඩ නැත.',
        'invalid_time': 'සමාවන්න, අපි විවෘත වන්නේ උදේ 9.00සිට රාත්‍රී 9.00 දක්වා පමණි.',
        'menu_header': '🍽️ {restaurant} මෙනුව:',
        'breakfast': '☀️ උදේ ආහාර:',
        'lunch': '🍛 දිවා ආහාර:',
        'dinner': '🌅 රාත්‍රී ආහාර:',
        'beverages': '🥤 පානීය:',
        'opening_hours': '🕐 {restaurant} විවෘත වේලාවන්:',
        'contact_staff': '👨‍💼 අපගේ කාර්ය මණ්ඩලය සම්බන්ධ කර ගන්න:',
        'phone_needed': 'ඔබේ වෙන්කර ගැනීම සොයා ගැනීමට කරුණාකර ඔබේ දුරකථන අංකය ලබා දෙන්න.'
    },
    'ta': {
        'reservation_confirmed': '🎉 {name}க்கான முன்பதிவு உறுதி! {date} அன்று {time}க்கு {guests} நபர்கள், மேஜை {table}.',
        'no_availability': '😔 மன்னிக்கவும், {date} அன்று {time}க்கு {guests} நபர்களுக்கு இடம் இல்லை.',
        'invalid_time': 'மன்னிக்கவும், நாங்கள் காலை 9.00 முதல் இரவு 9.00 வரை மட்டுமே திறந்திருக்கிறோம்.',
        'menu_header': '🍽️ {restaurant} பட்டியல்:',
        'breakfast': '☀️ காலை உணவு:',
        'lunch': '🍛 மதிய உணவு:',
        'dinner': '🌅 இரவு உணவு:',
        'beverages': '🥤 பானங்கள்:',
        'opening_hours': '🕐 {restaurant} திறந்திருக்கும் நேரம்:',
        'contact_staff': '👨‍💼 எங்கள் ஊழியர்களை தொடர்பு கொள்ளவும்:',
        'phone_needed': 'உங்கள் முன்பதிவை கண்டறிய தயவுசெய்து உங்கள் தொலைபேசி எண்ணை வழங்கவும்.'
    }
}

def get_text(key, lang='en', **kwargs):
    """Get translated text with formatting"""
    try:
        text = TRANSLATIONS[lang].get(key, TRANSLATIONS['en'][key])
        return text.format(**kwargs)
    except:
        return TRANSLATIONS['en'].get(key, key)
