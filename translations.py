"""
Modulo di traduzione per il chatbot multilingue del ristorante
Supporta: Inglese, Singalese, Tamil
"""

TRANSLATIONS = {
    'en': {
        # Reservation Messages
        'reservation_confirmed': '🎉 Reservation confirmed for {name}! {guests} guests on {date} at {time}, Table {table}. Confirmation email will be sent shortly!',
        'reservation_received': '✅ Reservation received for {name}! {guests} guests on {date} at {time}. Our staff will contact you to confirm details.',
        'no_availability': '😔 Sorry, we don\'t have availability for {guests} guests on {date} at {time}. Please try a different time within our hours (9 AM - 9 PM).',
        'duplicate_reservation': '⚠️ You already have a reservation for {date} at {time}.',
        'invalid_time': 'Sorry, we\'re not open at {time}. Our restaurant is open from 9:00 AM to 9:00 PM. Please choose a time between 9 AM and 9 PM.',
        'invalid_time_early': 'Sorry, we\'re not open at {time}. Our restaurant is open from 9:00 AM to 9:00 PM. Please choose a time between 9 AM and 9 PM.',
        'invalid_time_late': 'Sorry, we\'re not open at {time}. Our restaurant closes at 9:00 PM. Please choose a time between 9:00 AM and 9:00 PM.',
        
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
        'general_error': 'Sorry, error processing your request. Please call us at {phone}.',
        
        # Welcome Messages
        'welcome': '🍽️ Welcome to {restaurant}! {description}. I can help you check availability, make reservations, view our menu, or provide information. How can I assist you?'
    },
    
    'si': {
        # Reservation Messages
        'reservation_confirmed': '🎉 {name}ගේ වෙන්කර ගැනීම සනාථ කරන ලදී! {date} දින {time}ට {guests} දෙනෙකු, {table} මේසය. සනාථ කිරීමේ ඊමේල් ඉක්මනින් යවනු ලබයි!',
        'reservation_received': '✅ {name}ගේ වෙන්කර ගැනීම ලැබුණි! {date} දින {time}ට {guests} දෙනෙකු. අපගේ කාර්ය මණ්ඩලය විස්තර සනාථ කිරීම සඳහා ඔබව සම්බන්ධ කරගනු ඇත.',
        'no_availability': '😔 සමාවන්න, {date} දින {time}ට {guests} දෙනෙකුට ඉඩ නැත. කරුණාකර අපගේ වේලාවන් තුළ (උදේ 9 - රාත්‍රී 9) වෙනත් වේලාවක් උත්සාහ කරන්න.',
        'duplicate_reservation': '⚠️ ඔබට දැනටමත් {date} දින {time}ට වෙන්කර ගැනීමක් ඇත.',
        'invalid_time': 'සමාවන්න, අපි {time}ට විවෘත නැත. අපගේ ආපනශාලාව උදේ 9.00සිට රාත්‍රී 9.00 දක්වා විවෘත වේ. කරුණාකර උදේ 9සිට රාත්‍රී 9 දක්වා වේලාවක් තෝරන්න.',
        'invalid_time_early': 'සමාවන්න, අපි {time}ට විවෘත නැත. අපගේ ආපනශාලාව උදේ 9.00සිට රාත්‍රී 9.00 දක්වා විවෘත වේ. කරුණාකර උදේ 9සිට රාත්‍රී 9 දක්වා වේලාවක් තෝරන්න.',
        'invalid_time_late': 'සමාවන්න, අපි {time}ට විවෘත නැත. අපගේ ආපනශාලාව රාත්‍රී 9.00ට වැසේ. කරුණාකර උදේ 9සිට රාත්‍රී 9 දක්වා වේලාවක් තෝරන්න.',
        
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
        'reservation_cancelled': '✅ වෙන්කර ගැනීම සාර්ථකව අවලංගු කරන ලදී! {date} දින {time}ට {guests} දෙනෙකු සඳහා (මේසය {table}) {name}ගේ වෙන්කර ගැනීම ඉවත් කරන ලදී.',
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
        'update_error': 'යාවත්කා
