"""
Simple multilingual translation module for restaurant chatbot
Supports: English, Sinhala, Tamil
"""

TRANSLATIONS = {
    'en': {
        # Welcome Messages
        'welcome': '🍽️ Welcome to {restaurant}! {description}. I can help you check availability, make reservations, view our menu, or provide information. How can I assist you?',
        
        # Reservation Messages
        'reservation_confirmed': '🎉 Reservation confirmed for {name}! {guests} guests on {date} at {time}, Table {table}. Confirmation email will be sent shortly!',
        'reservation_received': '✅ Reservation received for {name}! {guests} guests on {date} at {time}. Our staff will contact you to confirm details.',
        'no_availability': '😔 Sorry, we don\'t have availability for {guests} guests on {date} at {time}. Please try a different time within our hours (9 AM - 9 PM).',
        'duplicate_reservation': '⚠️ You already have a reservation for {date} at {time}.',
        'invalid_time': 'Sorry, we\'re not open at {time}. Our restaurant is open from 9:00 AM to 9:00 PM. Please choose a time between 9 AM and 9 PM.',
        
        # Input Validation
        'name_needed': 'I need your full name to complete the reservation.',
        'phone_needed': 'I need your phone number to complete the reservation.',
        'email_needed': 'I need a valid email address to complete the reservation.',
        'datetime_needed': 'I need both the date and time for your reservation.',
        'phone_for_check': 'Please provide your phone number to find your reservation.',
        'valid_table_number': 'Please specify a table number between 1 and 20.',
        'valid_guest_count': 'I can accommodate between 1 and 20 guests. Please specify a valid number.',
        
        # Reservation Management
        'reservation_updated_date': '✅ Date updated successfully to {date}! Your table is now {table}.',
        'reservation_updated_time': '✅ Time updated successfully to {time}! Your table is now {table}.',
        'reservation_updated_guests': '✅ Guest count updated successfully to {guests} guests (was {old_guests})! Your table is now {table}.',
        'reservation_cancelled': '✅ Reservation cancelled successfully! Your reservation for {name} on {date} at {time} for {guests} guests (Table {table}) has been removed. We\'re sorry to see you cancel. We hope to see you again soon!',
        'reservation_not_found': 'I couldn\'t find any active reservations for phone number {phone}.',
        'multiple_reservations': 'You have {count} reservations. Please call us at {phone} to specify which one to modify.',
        'current_reservation': '📋 Your current reservation: {name} for {guests} guests on {date} at {time} (Table {table}). What would you like to modify?',
        'reservation_details': '📋 Your reservation: {name} ({phone}) - {guests} guests on {date} at {time} - Table {table} - Status: Confirmed.',
        
        # Menu
        'menu_header': '🍽️ {restaurant} Menu:',
        'breakfast': '☀️ BREAKFAST:',
        'lunch': '🍛 LUNCH:',
        'dinner': '🌅 DINNER:',
        'beverages': '🥤 BEVERAGES:',
        
        # Restaurant Info
        'opening_hours_header': '🕐 {restaurant} Opening Hours:',
        'weekday_hours': '📅 Monday - Saturday:\n09:00 AM - 09:00 PM',
        'sunday_hours': '📅 Sunday:\n10:00 AM - 08:00 PM',
        'restaurant_info_header': '🍽️ {restaurant}',
        'address_label': '📍 Address:\n{address}',
        'phone_label': '📞 Phone:\n{phone}',
        'email_label': '📧 Email:\n{email}',
        'hours_summary': '🕐 Hours:\nMon-Sat 9AM-9PM\nSun 10AM-8PM',
        'contact_staff': '👨‍💼 Contact our staff:',
        'location_header': '📍 {restaurant} Location:',
        'location_address': '🏠 Address:\n{address}',
        
        # Table Availability
        'table_available': '✅ Good news! Table {table} is available on {date} at {time}!',
        'table_unavailable': '😔 Sorry, table {table} is already reserved on {date} at {time}.',
        'table_number_needed': 'Please specify which table number you\'d like to check (1-20).',
        'datetime_needed_table': 'I need the date and time to check table {table} availability.',
        
        # Error Messages
        'technical_issue': 'I\'m sorry, there was a technical issue. Please call us directly at {phone} and we\'ll be happy to help you.',
        'sheets_error': 'Sorry, I\'m having trouble accessing your reservations. Please call us.',
        'availability_error': 'Sorry, I\'m having trouble checking availability.',
        'update_error': 'Update completed. Please call {phone} to verify changes.',
        'cancel_error': 'Sorry, there was an issue cancelling your reservation. Please call us at {phone}.',
        'general_error': 'Sorry, error processing your request. Please call us at {phone}.'
    },
    
    'si': {
        # Welcome Messages
        'welcome': '🍽️ {restaurant}ට සාදරයෙන් පිළිගන්නවා! {description}. මට ඔබට ලබා ගත හැකි බව පරීක්ෂා කිරීම, වෙන්කර ගැනීම්, අපගේ මෙනුව බැලීම, හෝ තොරතුරු සැපයීම සඳහා උදව් කළ හැකියි. මට ඔබට කෙසේ උදව් කළ හැකිද?',
        
        # Reservation Messages
        'reservation_confirmed': '🎉 {name}ගේ වෙන්කර ගැනීම සනාථ කරන ලදී! {date} දින {time}ට {guests} දෙනෙකු, {table} මේසය. සනාථ කිරීමේ ඊමේල් ඉක්මනින් යවනු ලබයි!',
        'reservation_received': '✅ {name}ගේ වෙන්කර ගැනීම ලැබුණි! {date} දින {time}ට {guests} දෙනෙකු. අපගේ කාර්ය මණ්ඩලය විස්තර සනාථ කිරීම සඳහා ඔබව සම්බන්ධ කරගනු ඇත.',
        'no_availability': '😔 සමාවන්න, {date} දින {time}ට {guests} දෙනෙකුට ඉඩ නැත. කරුණාකර අපගේ වේලාවන් තුළ (උදේ 9 - රාත්‍රී 9) වෙනත් වේලාවක් උත්සාහ කරන්න.',
        'duplicate_reservation': '⚠️ ඔබට දැනටමත් {date} දින {time}ට වෙන්කර ගැනීමක් ඇත.',
        'invalid_time': 'සමාවන්න, අපි {time}ට විවෘත නැත. අපගේ ආපනශාලාව උදේ 9.00සිට රාත්‍රී 9.00 දක්වා විවෘත වේ. කරුණාකර උදේ 9සිට රාත්‍රී 9 දක්වා වේලාවක් තෝරන්න.',
        
        # Input Validation
        'name_needed': 'වෙන්කර ගැනීම සම්පූර්ණ කිරීමට මට ඔබගේ සම්පූර්ණ නම අවශ්‍යයි.',
        'phone_needed': 'වෙන්කර ගැනීම සම්පූර්ණ කිරීමට මට ඔබගේ දුරකථන අංකය අවශ්‍යයි.',
        'email_needed': 'වෙන්කර ගැනීම සම්පූර්ණ කිරීමට මට වලංගු ඊමේල් ලිපිනයක් අවශ්‍යයි.',
        'datetime_needed': 'ඔබේ වෙන්කර ගැනීම සඳහා මට දිනය සහ වේලාව දෙකම අවශ්‍යයි.',
        'phone_for_check': 'ඔබේ වෙන්කර ගැනීම සොයා ගැනීමට කරුණාකර ඔබේ දුරකථන අංකය ලබා දෙන්න.',
        'valid_table_number': 'කරුණාකර 1 සිට 20 දක්වා මේස අංකයක් සඳහන් කරන්න.',
        'valid_guest_count': 'මට 1 සිට 20 දක්වා අමුත්තන්ට ඉඩ සලසා දිය හැකිය. කරුණාකර වලංගු සංඛ්‍යාවක් සඳහන් කරන්න.',
        
        # Reservation Management
        'reservation_updated_date': '✅ දිනය {date}ට සාර්ථකව යාවත්කාලීන කරන ලදී! ඔබේ මේසය දැන් {table}.',
        'reservation_updated_time': '✅ වේලාව {time}ට සාර්ථකව යාවත්කාලීන කරන ලදී! ඔබේ මේසය දැන් {table}.',
        'reservation_updated_guests': '✅ අමුත්තන්ගේ සංඛ්‍යාව {guests} දෙනෙකුට සාර්ථකව යාවත්කාලීන කරන ලදී ({old_guests} දෙනෙකුගෙන්)! ඔබේ මේසය දැන් {table}.',
        'reservation_cancelled': '✅ වෙන්කර ගැනීම සාර්ථකව අවලංගු කරන ලදී! {date} දින {time}ට {guests} දෙනෙකු සඳහා (මේසය {table}) {name}ගේ වෙන්කර ගැනීම ඉවත් කරන ලදී. ඔබ අවලංගු කිරීම ගැන අපට කණගාටුයි. අපි ඔබව නැවත හමුවීමට බලාපොරොත්තු වෙමු!',
        'reservation_not_found': '{phone} දුරකථන අංකය සඳහා සක්‍රීය වෙන්කර ගැනීමක් මට සොයා ගත නොහැකි විය.',
        'multiple_reservations': 'ඔබට වෙන්කර ගැනීම් {count}ක් ඇත. කුමන එක වෙනස් කිරීමට ද යන්න සඳහන් කිරීමට {phone}ට අමතන්න.',
        'current_reservation': '📋 ඔබේ වත්මන් වෙන්කර ගැනීම: {date} දින {time}ට {guests} දෙනෙකු සඳහා {name} (මේසය {table}). ඔබට කුමක් වෙනස් කිරීමට අවශ්‍යද?',
        'reservation_details': '📋 ඔබේ වෙන්කර ගැනීම: {name} ({phone}) - {date} දින {time}ට {guests} දෙනෙකු - මේසය {table} - තත්ත්වය: සනාථයි.',
        
        # Menu
        'menu_header': '🍽️ {restaurant} මෙනුව:',
        'breakfast': '☀️ උදේ ආහාර:',
        'lunch': '🍛 දිවා ආහාර:',
        'dinner': '🌅 රාත්‍රී ආහාර:',
        'beverages': '🥤 පානීය:',
        
        # Restaurant Info
        'opening_hours_header': '🕐 {restaurant} විවෘත වේලාවන්:',
        'weekday_hours': '📅 සඳුදා - සෙනසුරාදා:\nඋදේ 09:00 - රාත්‍රී 09:00',
        'sunday_hours': '📅 ඉරිදා:\nඋදේ 10:00 - රාත්‍රී 08:00',
        'restaurant_info_header': '🍽️ {restaurant}',
        'address_label': '📍 ලිපිනය:\n{address}',
        'phone_label': '📞 දුරකථනය:\n{phone}',
        'email_label': '📧 ඊමේල්:\n{email}',
        'hours_summary': '🕐 වේලාවන්:\nසඳු-සෙන උදේ 9-රාත්‍රී 9\nඉරිදා උදේ 10-රාත්‍රී 8',
        'contact_staff': '👨‍💼 අපගේ කාර්ය මණ්ඩලය සම්බන්ධ කර ගන්න:',
        'location_header': '📍 {restaurant} ස්ථානය:',
        'location_address': '🏠 ලිපිනය:\n{address}',
        
        # Table Availability
        'table_available': '✅ හොඳ ප්‍රවෘත්ති! {date} දින {time}ට {table} මේසය ලබා ගත හැකිය!',
        'table_unavailable': '😔 සමාවන්න, {date} දින {time}ට {table} මේසය දැනටමත් වෙන්කර ගෙන ඇත.',
        'table_number_needed': 'කරුණාකර ඔබට පරීක්ෂා කිරීමට අවශ්‍ය මේස අංකය සඳහන් කරන්න (1-20).',
        'datetime_needed_table': '{table} මේසයේ ලබා ගත හැකි බව පරීක්ෂා කිරීමට මට දිනය සහ වේලාව අවශ්‍යයි.',
        
        # Error Messages
        'technical_issue': 'මට කණගාටුයි, තාක්ෂණික ගැටළුවක් ඇති විය. කරුණාකර {phone}ට කෙලින්ම අමතන්න, අපි ඔබට උදව් කිරීමට සතුටු වෙමු.',
        'sheets_error': 'සමාවන්න, ඔබේ වෙන්කර ගැනීම් වෙත ප්‍රවේශ වීමේදී මට ගැටළුවක් ඇත. කරුණාකර අපට අමතන්න.',
        'availability_error': 'සමාවන්න, ලබා ගත හැකි බව පරීක්ෂා කිරීමේදී මට ගැටළුවක් ඇත.',
        'update_error': 'යාවත්කාලීන කිරීම සම්පූර්ණයි. වෙනස්කම් සනාථ කිරීමට {phone}ට අමතන්න.',
        'cancel_error': 'සමාවන්න, ඔබේ වෙන්කර ගැනීම අවලංගු කිරීමේදී ගැටළුවක් ඇති විය. කරුණාකර {phone}ට අමතන්න.',
        'general_error': 'සමාවන්න, ඔබේ ඉල්ලීම සැකසීමේදී දෝෂයක්. කරුණාකර {phone}ට අමතන්න.'
    },
    
    'ta': {
        # Welcome Messages
        'welcome': '🍽️ {restaurant}க்கு வரவேற்கிறோம்! {description}. நான் உங்களுக்கு கிடைக்கும் தன்மையை சரிபார்க்க, முன்பதிவு செய்ய, எங்கள் மெனுவைப் பார்க்க அல்லது தகவல் வழங்க உதவ முடியும். நான் உங்களுக்கு எப்படி உதவ முடியும்?',
        
        # Reservation Messages
        'reservation_confirmed': '🎉 {name}க்கான முன்பதிவு உறுதி! {date} அன்று {time}க்கு {guests} நபர்கள், மேஜை {table}. உறுதிப்படுத்தும் மின்னஞ்சல் விரைவில் அனுப்பப்படும்!',
        'reservation_received': '✅ {name}க்கான முன்பதிவு பெறப்பட்டது! {date} அன்று {time}க்கு {guests} நபர்கள். எங்கள் பணியாளர்கள் விவரங்களை உறுதிப்படுத்த உங்களைத் தொடர்புகொள்வார்கள்.',
        'no_availability': '😔 மன்னிக்கவும், {date} அன்று {time}க்கு {guests} நபர்களுக்கு இடம் இல்லை. எங்கள் நேரங்களுக்குள் (காலை 9 - இரவு 9) வேறு நேரத்தை முயற்சிக்கவும்.',
        'duplicate_reservation': '⚠️ உங்களுக்கு ஏற்கனவே {date} அன்று {time}க்கு முன்பதிவு உள்ளது.',
        'invalid_time': 'மன்னிக்கவும், எங்கள் உணவகம் {time}க்கு திறக்கப்பட்டில்லை. எங்கள் உணவகம் காலை 9:00 முதல் இரவு 9:00 வரை திறந்திருக்கும். தயவுசெய்து காலை 9 முதல் இரவு 9 வரையிலான நேரத்தைத் தேர்ந்தெடுக்கவும்.',
        
        # Input Validation
        'name_needed': 'முன்பதிவை முடிக்க எனக்கு உங்கள் முழு பெயர் தேவை.',
        'phone_needed': 'முன்பதிவை முடிக்க எனக்கு உங்கள் தொலைபேசி எண் தேவை.',
        'email_needed': 'முன்பதிவை முடிக்க எனக்கு சரியான மின்னஞ்சல் முகவரி தேவை.',
        'datetime_needed': 'உங்கள் முன்பதிவுக்கு எனக்கு தேதி மற்றும் நேரம் இரண்டும் தேவை.',
        'phone_for_check': 'உங்கள் முன்பதிவைக் கண்டறிய தயவுசெய்து உங்கள் தொலைபேசி எண்ணை வழங்கவும்.',
        'valid_table_number': 'தயவுசெய்து 1 முதல் 20 வரையிலான மேஜை எண்ணைக் குறிப்பிடவும்.',
        'valid_guest_count': 'நான் 1 முதல் 20 விருந்தினர்கள் வரை இடமளிக்க முடியும். தயவுசெய்து சரியான எண்ணைக் குறிப்பிடவும்.',
        
        # Reservation Management
        'reservation_updated_date': '✅ தேதி வெற்றிகரமாக {date}க்கு மாற்றப்பட்டது! உங்கள் மேஜை இப்போது {table}.',
        'reservation_updated_time': '✅ நேரம் வெற்றிகரமாக {time}க்கு மாற்றப்பட்டது! உங்கள் மேஜை இப்போது {table}.',
        'reservation_updated_guests': '✅ விருந்தினர்களின் எண்ணிக்கை வெற்றிகரமாக {guests} நபர்களாக மாற்றப்பட்டது ({old_guests} நபர்களிலிருந்து)! உங்கள் மேஜை இப்போது {table}.',
        'reservation_cancelled': '✅ முன்பதிவு வெற்றிகரமாக ரத்து செய்யப்பட்டது! {date} அன்று {time}க்கு {guests} நபர்களுக்கான (மேஜை {table}) {name}க்கான உங்கள் முன்பதிவு அகற்றப்பட்டது. நீங்கள் ரத்து செய்வதைக் கண்டு எங்களுக்கு வருத்தம். விரைவில் உங்களை மீண்டும் பார்க்க நாங்கள் எதிர்பார்க்கிறோம்!',
        'reservation_not_found': '{phone} தொலைபேசி எண்ணுக்கு செயலில் உள்ள முன்பதிவுகளை என்னால் கண்டறிய முடியவில்லை.',
        'multiple_reservations': 'உங்களிடம் {count} முன்பதிவுகள் உள்ளன. எதை மாற்ற வேண்டும் என்பதைக் குறிப்பிட தயவுசெய்து {phone}க்கு அழைக்கவும்.',
        'current_reservation': '📋 உங்கள் தற்போதைய முன்பதிவு: {date} அன்று {time}க்கு {guests} நபர்களுக்கான {name} (மேஜை {table}). நீங்கள் எதை மாற்ற விரும்புகிறீர்கள்?',
        'reservation_details': '📋 உங்கள் முன்பதிவு: {name} ({phone}) - {date} அன்று {time}க்கு {guests} நபர்கள் - மேஜை {table} - நிலை: உறுதி.',
        
        # Menu
        'menu_header': '🍽️ {restaurant} மெனு:',
        'breakfast': '☀️ காலை உணவு:',
        'lunch': '🍛 மதிய உணவு:',
        'dinner': '🌅 இரவு உணவு:',
        'beverages': '🥤 பானங்கள்:',
        
        # Restaurant Info
        'opening_hours_header': '🕐 {restaurant} திறக்கும் நேரங்கள்:',
        'weekday_hours': '📅 திங்கள் - சனிக்கிழமை:\nகாலை 09:00 - இரவு 09:00',
        'sunday_hours': '📅 ஞாயிற்றுக்கிழமை:\nகாலை 10:00 - இரவு 08:00',
        'restaurant_info_header': '🍽️ {restaurant}',
        'address_label': '📍 முகவரி:\n{address}',
        'phone_label': '📞 தொலைபேசி:\n{phone}',
        'email_label': '📧 மின்னஞ்சல்:\n{email}',
        'hours_summary': '🕐 நேரங்கள்:\nதிங்-சனி காலை 9-இரவு 9\nஞாயிறு காலை 10-இரவு 8',
        'contact_staff': '👨‍💼 எங்கள் பணியாளர்களைத் தொடர்பு கொள்ளுங்கள்:',
        'location_header': '📍 {restaurant} இருப்பிடம்:',
        'location_address': '🏠 முகவரி:\n{address}',
        
        # Table Availability
        'table_available': '✅ நல்ல செய்தி! {date} அன்று {time}க்கு மேஜை {table} கிடைக்கிறது!',
        'table_unavailable': '😔 மன்னிக்கவும், {date} அன்று {time}க்கு மேஜை {table} ஏற்கனவே முன்பதிவு செய்யப்பட்டுள்ளது.',
        'table_number_needed': 'தயவுசெய்து நீங்கள் சரிபார்க்க விரும்பும் மேஜை எண்ணைக் குறிப்பிடவும் (1-20).',
        'datetime_needed_table': 'மேஜை {table}ன் கிடைக்கும் தன்மையை சரிபார்க்க எனக்கு தேதி மற்றும் நேரம் தேவை.',
        
        # Error Messages
        'technical_issue': 'மன்னிக்கவும், தொழில்நுட்ப சிக்கல் ஏற்பட்டது. தயவுசெய்து {phone} என்ற எண்ணில் நேரடியாக அழைக்கவும், நாங்கள் உங்களுக்கு உதவ மகிழ்ச்சியாக இருப்போம்.',
        'sheets_error': 'மன்னிக்கவும், உங்கள் முன்பதிவுகளை அணுகுவதில் எனக்கு சிக்கல் உள்ளது. தயவுசெய்து எங்களை அழைக்கவும்.',
        'availability_error': 'மன்னிக்கவும், கிடைக்கும் தன்மையை சரிபார்ப்பதில் எனக்கு சிக்கல் உள்ளது.',
        'update_error': 'புதுப்பித்தல் முடிந்தது. மாற்றங்களைச் சரிபார்க்க {phone}க்கு அழைக்கவும்.',
        'cancel_error': 'மன்னிக்கவும், உங்கள் முன்பதிவை ரத்து செய்வதில் சிக்கல் ஏற்பட்டது. தயவுசெய்து {phone}க்கு அழைக்கவும்.',
        'general_error': 'மன்னிக்கவும், உங்கள் கோரிக்கையை செயல்படுத்துவதில் பிழை. தயவுசெய்து {phone} என்ற எண்ணில் அழைக்கவும்.'
    }
}


def get_text(key, lang='en', **kwargs):
    """Get translated text with formatting"""
    try:
        # Get the text in the requested language, fallback to English
        text = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS['en'].get(key, key)
        
        # Format with provided arguments
        if kwargs:
            return text.format(**kwargs)
        return text
    except Exception as e:
        print(f"Translation error for key '{key}' in language '{lang}': {e}")
        # Return English version as final fallback
        try:
            return TRANSLATIONS['en'].get(key, key)
        except:
            return key
