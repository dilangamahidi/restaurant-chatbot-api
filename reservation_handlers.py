"""
Handlers per la gestione delle prenotazioni del ristorante
"""
from flask import jsonify
import re
import traceback

# Importa da nostri moduli
from config import RESTAURANT_INFO
from datetime_utils import (
    extract_value, 
    parse_dialogflow_datetime, 
    format_date_readable, 
    format_time_readable
)
from sheets_manager import (
    save_reservation_to_sheets,
    check_existing_reservation,
    get_user_reservations,
    update_reservation_field,
    delete_reservation_from_sheets
)
from ml_utils import (
    find_available_table,
    check_table_availability
)
from email_manager import send_confirmation_email, send_admin_notification


def handle_modify_reservation_date(parameters):
    """Gestisce modifica della data di prenotazione - CON FIX RESPONSE"""
    try:
        print(f"🔧 DEBUG - Modify date parameters: {parameters}")
        
        # Estrai parametri
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        new_date_raw = parameters.get('new_date', parameters.get('date', ''))
        new_date = extract_value(new_date_raw)
        
        print(f"🔧 DEBUG - Extracted: phone={phone}, new_date={new_date}")
        
        if not phone:
            return jsonify({
                'fulfillmentText': "Please provide your phone number to find your reservation."
            })
        
        if not new_date:
            return jsonify({
                'fulfillmentText': "Please specify the new date for your reservation."
            })
        
        # Cerca prenotazione esistente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            return jsonify({
                'fulfillmentText': f"I couldn't find any active reservations for phone number {phone}."
            })
        
        if len(user_reservations) != 1:
            return jsonify({
                'fulfillmentText': f"You have multiple reservations. Please call us at {RESTAURANT_INFO['phone']} to specify which one to modify."
            })
        
        reservation = user_reservations[0]
        old_date = reservation.get('Date', '')
        old_time = reservation.get('Time', '')
        guests = reservation.get('Guests', 2)
        
        # Formatta la nuova data
        try:
            formatted_new_date = format_date_readable(new_date)
        except Exception as e:
            print(f"❌ Error formatting new date: {e}")
            formatted_new_date = str(new_date)
        
        # Controlla disponibilità per la nuova data
        try:
            day_of_week, hour_of_day = parse_dialogflow_datetime(new_date, old_time)
            result = find_available_table(int(guests), day_of_week, hour_of_day)
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            return jsonify({
                'fulfillmentText': f"Sorry, I'm having trouble checking availability for the new date."
            })
        
        if result['available']:
            # Aggiorna la data e potenzialmente il tavolo
            new_table = result['table_number']
            
            # Aggiorna data
            try:
                date_updated = update_reservation_field(phone, old_date, old_time, 'date', formatted_new_date)
                print(f"🔧 DEBUG - date_updated result: {date_updated}")
            except Exception as e:
                print(f"❌ Error updating date: {e}")
                date_updated = False
            
            # Aggiorna tavolo se necessario
            try:
                table_updated = update_reservation_field(phone, formatted_new_date, old_time, 'table', new_table)
                print(f"🔧 DEBUG - table_updated result: {table_updated}")
            except Exception as e:
                print(f"❌ Error updating table: {e}")
                table_updated = False
            
            # SEMPRE restituisci una risposta positiva se almeno uno è aggiornato
            if date_updated or table_updated:
                try:
                    rich_response = {
                        "fulfillmentText": "✅ Date updated successfully!",
                        "fulfillmentMessages": [
                            {
                                "text": {
                                    "text": ["✅ Reservation date updated successfully!"]
                                }
                            },
                            {
                                "text": {
                                    "text": ["📋 Updated reservation details:"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"👤 Name: {reservation.get('Name', '')}"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"📅 New Date: {formatted_new_date}"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"🕐 Time: {old_time}"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"👥 Guests: {guests}"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"🪑 Table: {new_table}"]
                                }
                            }
                        ]
                    }
                    return jsonify(rich_response)
                except Exception as e:
                    print(f"❌ Error building response: {e}")
                    return jsonify({
                        'fulfillmentText': f"✅ Date updated to {formatted_new_date}! New table: {new_table}"
                    })
            else:
                return jsonify({
                    'fulfillmentText': f"Update completed but please call {RESTAURANT_INFO['phone']} to verify changes."
                })
        else:
            return jsonify({
                'fulfillmentText': f"Sorry, we don't have availability for {guests} guests on {formatted_new_date} at {old_time}. Please try a different date or time."
            })
            
    except Exception as e:
        print(f"❌ Error in modify_reservation_date: {e}")
        return jsonify({'fulfillmentText': f'Sorry, error modifying your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'})


def handle_modify_reservation_time(parameters):
    """Gestisce modifica dell'orario di prenotazione - CON FIX RESPONSE"""
    try:
        print(f"🔧 DEBUG - Modify time parameters: {parameters}")
        
        # Estrai parametri
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        new_time_raw = parameters.get('new_time', parameters.get('time', ''))
        new_time = extract_value(new_time_raw)
        
        print(f"🔧 DEBUG - Extracted: phone={phone}, new_time={new_time}")
        
        if not phone:
            return jsonify({
                'fulfillmentText': "Please provide your phone number to find your reservation."
            })
        
        if not new_time:
            return jsonify({
                'fulfillmentText': "Please specify the new time for your reservation."
            })
        
        # Cerca prenotazione esistente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            return jsonify({
                'fulfillmentText': f"I couldn't find any active reservations for phone number {phone}."
            })
        
        if len(user_reservations) != 1:
            return jsonify({
                'fulfillmentText': f"You have multiple reservations. Please call us at {RESTAURANT_INFO['phone']} to specify which one to modify."
            })
        
        reservation = user_reservations[0]
        old_date = reservation.get('Date', '')
        old_time = reservation.get('Time', '')
        guests = reservation.get('Guests', 2)
        
        # Formatta il nuovo orario
        try:
            formatted_new_time = format_time_readable(new_time)
        except Exception as e:
            print(f"❌ Error formatting new time: {e}")
            formatted_new_time = str(new_time)
        
        # Controlla disponibilità per il nuovo orario
        try:
            day_of_week, hour_of_day = parse_dialogflow_datetime(old_date, new_time)
            
            # 🔧 DEBUG LOGS - INDENTAZIONE CORRETTA
            print(f"🔧 DEBUG ML INPUT (MODIFY TIME):")
            print(f"  old_date: {old_date}")
            print(f"  new_time: {new_time}")
            print(f"  guests: {guests}")
            print(f"  day_of_week: {day_of_week}")  
            print(f"  hour_of_day: {hour_of_day}")
            print(f"  ML results for first 5 tables:")
            
            for table_num in range(1, 6):
                ml_result = check_table_availability(table_num, int(guests), day_of_week, hour_of_day)
                print(f"    Table {table_num}: {'AVAILABLE' if ml_result else 'OCCUPIED'}")
            
            result = find_available_table(int(guests), day_of_week, hour_of_day)
            print(f"  Final result: {result}")
            
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            return jsonify({
                'fulfillmentText': f"Sorry, I'm having trouble checking availability for the new time."
            })
        
        if result['available']:
            # Aggiorna l'orario e potenzialmente il tavolo
            new_table = result['table_number']
            
            # Aggiorna orario
            try:
                time_updated = update_reservation_field(phone, old_date, old_time, 'time', formatted_new_time)
                print(f"🔧 DEBUG - time_updated result: {time_updated}")
            except Exception as e:
                print(f"❌ Error updating time: {e}")
                time_updated = False
            
            # Aggiorna tavolo se necessario
            try:
                table_updated = update_reservation_field(phone, old_date, formatted_new_time, 'table', new_table)
                print(f"🔧 DEBUG - table_updated result: {table_updated}")
            except Exception as e:
                print(f"❌ Error updating table: {e}")
                table_updated = False
            
            # SEMPRE restituisci una risposta positiva se almeno uno è aggiornato
            if time_updated or table_updated:
                try:
                    rich_response = {
                        "fulfillmentText": "✅ Time updated successfully!",
                        "fulfillmentMessages": [
                            {
                                "text": {
                                    "text": ["✅ Reservation time updated successfully!"]
                                }
                            },
                            {
                                "text": {
                                    "text": ["📋 Updated reservation details:"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"👤 Name: {reservation.get('Name', '')}"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"📅 Date: {old_date}"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"🕐 New Time: {formatted_new_time}"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"👥 Guests: {guests}"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"🪑 Table: {new_table}"]
                                }
                            }
                        ]
                    }
                    return jsonify(rich_response)
                except Exception as e:
                    print(f"❌ Error building response: {e}")
                    return jsonify({
                        'fulfillmentText': f"✅ Time updated to {formatted_new_time}! New table: {new_table}"
                    })
            else:
                return jsonify({
                    'fulfillmentText': f"Update completed but please call {RESTAURANT_INFO['phone']} to verify changes."
                })
        else:
            return jsonify({
                'fulfillmentText': f"Sorry, we don't have availability for {guests} guests on {old_date} at {formatted_new_time}. Please try a different time."
            })
            
    except Exception as e:
        print(f"❌ Error in modify_reservation_time: {e}")
        return jsonify({'fulfillmentText': f'Sorry, error modifying your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'})


def handle_modify_reservation_guests(parameters):
    """Gestisce modifica del numero di ospiti - VERSIONE CON DEBUG ESTESO E FIX RESPONSE"""
    try:
        print(f"🔧 DEBUG - Modify guests parameters: {parameters}")
        
        # Estrai parametri
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        new_guests_raw = parameters.get('new_guests', parameters.get('guests', parameters.get('number', '')))
        new_guests = extract_value(new_guests_raw)
        
        print(f"🔧 DEBUG - Extracted: phone={phone}, new_guests={new_guests}")
        
        if not phone:
            return jsonify({
                'fulfillmentText': "Please provide your phone number to find your reservation."
            })
        
        if not new_guests:
            return jsonify({
                'fulfillmentText': "Please specify the new number of guests for your reservation."
            })
        
        # Converti numero ospiti
        try:
            print(f"🔧 DEBUG - Converting new_guests: '{new_guests}' (type: {type(new_guests)})")
            
            if new_guests is None or new_guests == '':
                print(f"🔧 DEBUG - new_guests is None or empty")
                return jsonify({
                    'fulfillmentText': "Please specify the new number of guests for your reservation."
                })
            
            # Pulisci il valore - rimuovi spazi e caratteri speciali
            clean_guests = str(new_guests).strip()
            print(f"🔧 DEBUG - Clean guests string: '{clean_guests}'")
            
            # Rimuovi parole comuni se presenti
            clean_guests = clean_guests.replace('guests', '').replace('people', '').replace('persons', '').strip()
            print(f"🔧 DEBUG - After removing words: '{clean_guests}'")
            
            # Converti parole in numeri se necessario
            word_to_num = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
                'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
            }
            
            if clean_guests.lower() in word_to_num:
                guest_count = word_to_num[clean_guests.lower()]
                print(f"🔧 DEBUG - Converted word to number: {guest_count}")
            else:
                # Prova conversione numerica diretta
                guest_count = int(float(clean_guests))  # float() per gestire eventuali decimali
                print(f"🔧 DEBUG - Converted string to number: {guest_count}")
            
            # Valida range
            if guest_count < 1 or guest_count > 20:
                print(f"🔧 DEBUG - Guest count {guest_count} out of range")
                return jsonify({
                    'fulfillmentText': "I can accommodate between 1 and 20 guests. Please specify a valid number."
                })
                
            print(f"🔧 DEBUG - Final guest_count: {guest_count}")
            
        except (ValueError, TypeError) as e:
            print(f"❌ Error converting guests '{new_guests}': {e}")
            print(f"❌ Type: {type(new_guests)}, Raw value: {repr(new_guests)}")
            return jsonify({
                'fulfillmentText': f"Please provide a valid number of guests (you entered: '{new_guests}')."
            })
        
        # Cerca prenotazione esistente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            return jsonify({
                'fulfillmentText': f"I couldn't find any active reservations for phone number {phone}."
            })
        
        if len(user_reservations) != 1:
            return jsonify({
                'fulfillmentText': f"You have multiple reservations. Please call us at {RESTAURANT_INFO['phone']} to specify which one to modify."
            })
        
        reservation = user_reservations[0]
        old_date = reservation.get('Date', '')
        old_time = reservation.get('Time', '')
        old_guests = reservation.get('Guests', 2)
        
        print(f"🔧 DEBUG - Found reservation:")
        print(f"    old_date: '{old_date}' (type: {type(old_date)})")
        print(f"    old_time: '{old_time}' (type: {type(old_time)})")
        print(f"    old_guests: '{old_guests}' (type: {type(old_guests)})")
        print(f"    new_guests: {guest_count}")
        
        # Controlla disponibilità per il nuovo numero di ospiti
        try:
            print(f"🔧 DEBUG - About to parse datetime with:")
            print(f"    date_param: '{old_date}'")
            print(f"    time_param: '{old_time}'")
            
            day_of_week, hour_of_day = parse_dialogflow_datetime(old_date, old_time)
            
            print(f"🔧 DEBUG - Parsed datetime result:")
            print(f"    day_of_week: {day_of_week}")
            print(f"    hour_of_day: {hour_of_day}")
            
            print(f"🔧 DEBUG - About to check table availability with:")
            print(f"    guest_count: {guest_count}")
            print(f"    day_of_week: {day_of_week}")
            print(f"    hour_of_day: {hour_of_day}")
            
            result = find_available_table(guest_count, day_of_week, hour_of_day)
            
            print(f"🔧 DEBUG - Availability check result:")
            print(f"    available: {result['available']}")
            print(f"    table_number: {result.get('table_number')}")
            print(f"    total_available: {result.get('total_available')}")
            
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            import traceback
            print(f"❌ TRACEBACK: {traceback.format_exc()}")
            return jsonify({
                'fulfillmentText': f"Sorry, I'm having trouble checking availability for {guest_count} guests."
            })
        
        if result['available']:
            # Aggiorna il numero di ospiti e potenzialmente il tavolo
            new_table = result['table_number']
            
            print(f"🔧 DEBUG - Updating reservation:")
            print(f"    phone: {phone}")
            print(f"    old_date: {old_date}")
            print(f"    old_time: {old_time}")
            print(f"    new_guests: {guest_count}")
            print(f"    new_table: {new_table}")
            
            # Aggiorna numero ospiti
            try:
                guests_updated = update_reservation_field(phone, old_date, old_time, 'guests', guest_count)
                print(f"🔧 DEBUG - guests_updated result: {guests_updated}")
            except Exception as e:
                print(f"❌ Error updating guests: {e}")
                guests_updated = False
            
            # Aggiorna tavolo se necessario
            try:
                table_updated = update_reservation_field(phone, old_date, old_time, 'table', new_table)
                print(f"🔧 DEBUG - table_updated result: {table_updated}")
            except Exception as e:
                print(f"❌ Error updating table: {e}")
                table_updated = False
            
            print(f"🔧 DEBUG - Update results:")
            print(f"    guests_updated: {guests_updated}")
            print(f"    table_updated: {table_updated}")
            
            # SEMPRE restituisci una risposta positiva se almeno uno è aggiornato
            if guests_updated or table_updated:
                try:
                    rich_response = {
                        "fulfillmentText": "✅ Guest count updated successfully!",
                        "fulfillmentMessages": [
                            {
                                "text": {
                                    "text": ["✅ Number of guests updated successfully!"]
                                }
                            },
                            {
                                "text": {
                                    "text": ["📋 Updated reservation details:"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"👤 Name: {reservation.get('Name', '')}"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"📅 Date: {old_date}"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"🕐 Time: {old_time}"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"👥 New Guest Count: {guest_count} (was {old_guests})"]
                                }
                            },
                            {
                                "text": {
                                    "text": [f"🪑 Table: {new_table}"]
                                }
                            }
                        ]
                    }
                    print(f"🔧 DEBUG - About to return success response")
                    return jsonify(rich_response)
                except Exception as e:
                    print(f"❌ Error building response: {e}")
                    return jsonify({
                        'fulfillmentText': f"✅ Guest count updated to {guest_count}! New table: {new_table}"
                    })
            else:
                print(f"🔧 DEBUG - Both updates failed, returning error")
                return jsonify({
                    'fulfillmentText': f"Update completed but please call {RESTAURANT_INFO['phone']} to verify changes."
                })
        else:
            print(f"🔧 DEBUG - NO AVAILABILITY FOUND!")
            print(f"    Requested: {guest_count} guests")
            print(f"    Date: {old_date} (parsed as day_of_week: {day_of_week})")
            print(f"    Time: {old_time} (parsed as hour_of_day: {hour_of_day})")
            
            return jsonify({
                'fulfillmentText': f"Sorry, we don't have availability for {guest_count} guests on {old_date} at {old_time}. Please try a different time or date."
            })
            
    except Exception as e:
        print(f"❌ Error in modify_reservation_guests: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return jsonify({'fulfillmentText': f'Sorry, error modifying your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'})


def handle_modify_reservation(parameters):
    """Gestisce richiesta di modifica prenotazione - VERSIONE MENU"""
    try:
        print(f"🔧 DEBUG - Modify reservation parameters: {parameters}")
        
        # Estrai numero di telefono
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        
        print(f"🔧 DEBUG - Extracted phone: {phone}")
        
        if not phone:
            return jsonify({
                'fulfillmentText': "Please provide your phone number to find your reservation."
            })
        
        # Cerca prenotazioni dell'utente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            return jsonify({
                'fulfillmentText': f"I couldn't find any active reservations for phone number {phone}. Please check the number or call us at {RESTAURANT_INFO['phone']}."
            })
        
        if len(user_reservations) == 1:
            # Una sola prenotazione - mostra opzioni di modifica
            reservation = user_reservations[0]
            
            rich_response = {
                "fulfillmentText": "What would you like to modify?",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": ["📋 Your current reservation:"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👤 Name: {reservation.get('Name', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📅 Date: {reservation.get('Date', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🕐 Time: {reservation.get('Time', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👥 Guests: {reservation.get('Guests', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🪑 Table: {reservation.get('Table', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": ["🔄 What would you like to modify?"]
                        }
                    },
                    {
                        "text": {
                            "text": ["You can say: 'Change the date to tomorrow', 'Change the time to 8pm' or 'Change to 4 guests'."]
                        }
                    }
                ]
            }
            return jsonify(rich_response)
            
        else:
            # Multiple prenotazioni - mostra lista
            rich_response = {
                "fulfillmentText": f"You have {len(user_reservations)} reservations:",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [f"📋 You have {len(user_reservations)} active reservations:"]
                        }
                    }
                ]
            }
            
            for i, reservation in enumerate(user_reservations, 1):
                rich_response["fulfillmentMessages"].append({
                    "text": {
                        "text": [f"{i}. {reservation.get('Date', '')} at {reservation.get('Time', '')} - {reservation.get('Guests', '')} guests (Table {reservation.get('Table', '')})"]
                    }
                })
            
            rich_response["fulfillmentMessages"].append({
                "text": {
                    "text": [f"📞 Please call us at {RESTAURANT_INFO['phone']} to specify which reservation you'd like to modify."]
                }
            })
            
            return jsonify(rich_response)
            
    except Exception as e:
        print(f"❌ Error in modify_reservation: {e}")
        return jsonify({'fulfillmentText': f'Sorry, error finding your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'})


def handle_cancel_reservation(parameters):
    """Gestisce richiesta di cancellazione prenotazione - VERSIONE AGGIORNATA"""
    try:
        print(f"🔧 DEBUG - Cancel reservation parameters: {parameters}")
        
        # Estrai numero di telefono
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        
        print(f"🔧 DEBUG - Extracted phone: {phone}")
        
        if not phone:
            return jsonify({
                'fulfillmentText': "Please provide your phone number to find your reservation to cancel."
            })
        
        # Cerca prenotazioni dell'utente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            return jsonify({
                'fulfillmentText': f"I couldn't find any active reservations for phone number {phone}. Please check the number or call us at {RESTAURANT_INFO['phone']}."
            })
        
        if len(user_reservations) == 1:
            # Una sola prenotazione - elimina completamente
            reservation = user_reservations[0]
            
            # Elimina la prenotazione dal foglio
            success = delete_reservation_from_sheets(
                phone, 
                reservation.get('Date', ''), 
                reservation.get('Time', '')
            )
            
            if success:
                rich_response = {
                    "fulfillmentText": "✅ Reservation cancelled and removed successfully!",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": ["✅ Reservation cancelled and removed successfully!"]
                            }
                        },
                        {
                            "text": {
                                "text": ["📋 Cancelled reservation details:"]
                            }
                        },
                        {
                            "text": {
                                "text": [f"👤 Name: {reservation.get('Name', '')}"]
                            }
                        },
                        {
                            "text": {
                                "text": [f"📅 Date: {reservation.get('Date', '')}"]
                            }
                        },
                        {
                            "text": {
                                "text": [f"🕐 Time: {reservation.get('Time', '')}"]
                            }
                        },
                        {
                            "text": {
                                "text": [f"👥 Guests: {reservation.get('Guests', '')}"]
                            }
                        },
                        {
                            "text": {
                                "text": [f"🪑 Table: {reservation.get('Table', '')} (now available again)"]
                            }
                        },
                        {
                            "text": {
                                "text": ["🗑️ Your reservation has been completely removed from our system."]
                            }
                        },
                        {
                            "text": {
                                "text": ["💔 We're sorry to see you cancel. We hope to see you again soon!"]
                            }
                        }
                    ]
                }
                return jsonify(rich_response)
            else:
                return jsonify({
                    'fulfillmentText': f"Sorry, there was an issue cancelling your reservation. Please call us at {RESTAURANT_INFO['phone']}."
                })
                
        else:
            # Multiple prenotazioni - mostra lista per scelta manuale
            reservation_list = "📋 Your active reservations:\n\n"
            for i, reservation in enumerate(user_reservations, 1):
                reservation_list += f"{i}. {reservation.get('Date', '')} at {reservation.get('Time', '')} - {reservation.get('Guests', '')} guests (Table {reservation.get('Table', '')})\n"
            
            reservation_list += f"\n📞 Please call us at {RESTAURANT_INFO['phone']} to specify which reservation you'd like to cancel."
            
            return jsonify({'fulfillmentText': reservation_list})
            
    except Exception as e:
        print(f"❌ Error in cancel_reservation: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return jsonify({'fulfillmentText': f'Sorry, error cancelling your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'})


def handle_check_my_reservation(parameters):
    """Gestisce richiesta di controllo delle proprie prenotazioni - VERSION CON DEBUG"""
    try:
        print(f"🔧 DEBUG - Check my reservation parameters: {parameters}")
        
        # Estrai numero di telefono
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        print(f"🔧 DEBUG - phone_raw: {phone_raw} (type: {type(phone_raw)})")
        
        phone = extract_value(phone_raw)
        
        print(f"🔧 DEBUG - Extracted phone: '{phone}' (type: {type(phone)})")
        
        if not phone:
            return jsonify({
                'fulfillmentText': "To check your reservations, I need your phone number for security. Please provide the phone number you used when booking."
            })
        
        # Cerca prenotazioni dell'utente
        print(f"🔧 DEBUG - About to search for reservations...")
        user_reservations = get_user_reservations(phone)
        print(f"🔧 DEBUG - Search completed, found {len(user_reservations)} reservations")
        
        if not user_reservations:
            # Aggiungi suggerimenti per formati di telefono diversi
            phone_variants = [
                phone,
                phone.replace(' ', ''),
                phone.replace('-', ''),
                phone.replace('(', '').replace(')', ''),
                phone.replace('+', ''),
                f"+94{phone}" if not phone.startswith('+') else phone[3:],
                f"0{phone}" if not phone.startswith('0') else phone[1:],
            ]
            
            # Rimuovi duplicati mantenendo l'ordine
            phone_variants = list(dict.fromkeys(phone_variants))
            
            print(f"🔧 DEBUG - Trying phone variants: {phone_variants}")
            
            # Prova tutte le varianti
            for variant in phone_variants:
                if variant != phone:  # Evita di ricontrollare lo stesso numero
                    print(f"🔧 DEBUG - Trying variant: '{variant}'")
                    variant_reservations = get_user_reservations(variant)
                    if variant_reservations:
                        user_reservations = variant_reservations
                        print(f"🔧 DEBUG - Found reservations with variant: '{variant}'")
                        break
        
        if not user_reservations:
            return jsonify({
                'fulfillmentText': f"I couldn't find any active reservations for phone number {phone}. Please check the number format (try with/without spaces, +94 prefix, etc.) or call us at {RESTAURANT_INFO['phone']}."
            })
        
        if len(user_reservations) == 1:
            # Una sola prenotazione - mostra dettagli completi
            reservation = user_reservations[0]
            
            rich_response = {
                "fulfillmentText": "📋 Your reservation details:",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": ["📋 Your reservation details:"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👤 Name: {reservation.get('Name', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📞 Phone: {reservation.get('Phone', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📧 Email: {reservation.get('Email', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👥 Guests: {reservation.get('Guests', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📅 Date: {reservation.get('Date', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🕐 Time: {reservation.get('Time', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🪑 Table: {reservation.get('Table', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": ["✅ Status: Confirmed"]
                        }
                    },
                    {
                        "text": {
                            "text": ["Need to modify or cancel? Just let me know!"]
                        }
                    }
                ]
            }
            return jsonify(rich_response)
            
        else:
            # Multiple prenotazioni - mostra lista
            rich_response = {
                "fulfillmentText": f"📋 You have {len(user_reservations)} active reservations:",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [f"📋 You have {len(user_reservations)} active reservations:"]
                        }
                    }
                ]
            }
            
            for i, reservation in enumerate(user_reservations, 1):
                rich_response["fulfillmentMessages"].append({
                    "text": {
                        "text": [f"{i}. {reservation.get('Date', '')} at {reservation.get('Time', '')} - {reservation.get('Guests', '')} guests (Table {reservation.get('Table', '')})"]
                    }
                })
            
            rich_response["fulfillmentMessages"].append({
                "text": {
                    "text": ["Need to modify or cancel any reservation? Just let me know!"]
                }
            })
            
            return jsonify(rich_response)
            
    except Exception as e:
        print(f"❌ Error in check_my_reservation: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return jsonify({'fulfillmentText': f'Sorry, error checking your reservations. Please call us at {RESTAURANT_INFO["phone"]}.'})

def handle_check_table_specific(parameters):
    """Gestisce controllo tavolo specifico"""
    try:
        print(f"🔧 DEBUG - Raw parameters: {parameters}")
        
        # 🔧 MIGLIORA ESTRAZIONE NUMERO TAVOLO
        # Prova tutte le possibili chiavi per il numero del tavolo
        table_raw = None
        possible_table_keys = ['table_number', 'number', 'table', 'table_num', 'num']
        
        for key in possible_table_keys:
            if key in parameters and parameters[key]:
                table_raw = parameters[key]
                print(f"🔧 DEBUG - Found table in key '{key}': {table_raw}")
                break
        
        if not table_raw:
            print(f"🔧 DEBUG - No table found, trying extract_value on all keys")
            for key in possible_table_keys:
                extracted = extract_value(parameters.get(key, ''))
                if extracted:
                    table_raw = extracted
                    print(f"🔧 DEBUG - Extracted table from '{key}': {table_raw}")
                    break
        
        # Estrai anche date e time
        date_raw = parameters.get('date', parameters.get('day_of_week', ''))
        time_raw = parameters.get('time', parameters.get('hour_of_day', ''))
        
        print(f"🔧 DEBUG - Extracted raw: table={table_raw}, date={date_raw}, time={time_raw}")
        
        # Estrai valori con extract_value
        table_number = extract_value(table_raw)
        date = extract_value(date_raw)
        time = extract_value(time_raw)
        
        print(f"🔧 DEBUG - Final values: table={table_number}, date={date}, time={time}")
        
        # 🔧 MIGLIORA CONVERSIONE NUMERO TAVOLO
        try:
            if table_number is None or table_number == '':
                return jsonify({'fulfillmentText': "Please specify which table number you'd like to check (1-20)."})
            
            # Converti, gestendo vari formati
            table_str = str(table_number).strip().lower()
            
            # Rimuovi parole comuni
            table_str = table_str.replace('table', '').replace('number', '').replace('#', '').strip()
            
            # Converti parole in numeri se necessario
            word_to_num = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
                'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
            }
            
            if table_str in word_to_num:
                table_num = word_to_num[table_str]
            else:
                table_num = int(float(table_str))  # Gestisce anche numeri decimali
            
            print(f"🔧 DEBUG - Converted table number: {table_num}")
            
            # Valida range tavolo
            if table_num < 1 or table_num > 20:
                return jsonify({'fulfillmentText': "Please specify a table number between 1 and 20."})
                
        except (ValueError, TypeError) as e:
            print(f"🔧 DEBUG - Error converting table '{table_number}': {e}")
            return jsonify({'fulfillmentText': "Please provide a valid table number (1-20)."})
        
        # Controlla parametri mancanti
        missing = []
        if not date:
            missing.append("the date")
        if not time:
            missing.append("the time")
            
        if missing:
            missing_text = " and ".join(missing)
            return jsonify({'fulfillmentText': f"I need {missing_text} to check table {table_num} availability."})
        
        # Converti date/time per ML
        day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
        
        print(f"🔧 DEBUG - ML input: table={table_num}, guests=4, day={day_of_week}, hour={hour_of_day}")
        
        # Controlla tavolo specifico (usando guest_count=4 come default per il check)
        is_available = check_table_availability(table_num, 4, day_of_week, hour_of_day)
        
        print(f"🔧 DEBUG - Table {table_num} availability: {is_available}")
        
        # Formatta data e ora per la risposta
        try:
            formatted_date = format_date_readable(date)
            formatted_time = format_time_readable(time)
        except Exception as e:
            print(f"❌ Error formatting date/time: {e}")
            formatted_date = str(date)
            formatted_time = str(time)
        
        if is_available:
            response_text = f"✅ Good news! Table {table_num} is available on {formatted_date} at {formatted_time}!"
        else:
            response_text = f"😔 Sorry, table {table_num} is already reserved on {formatted_date} at {formatted_time}."
            
        return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        print(f"❌ Error in check_table_specific: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return jsonify({'fulfillmentText': 'Sorry, error checking table availability. Please call us.'})


def handle_make_reservation(parameters):
    """Gestisce prenotazione completa con controlli robusti - MULTIPLE MESSAGES + EMAIL"""
    try:
        print(f"🔧 DEBUG - RAW PARAMETERS: {parameters}")
        
        # Estrai parametri con controlli robusti
        name = extract_value(parameters.get('name', parameters.get('person', '')))
        phone = extract_value(parameters.get('phone_number', parameters.get('phone', '')))
        email = extract_value(parameters.get('email', ''))
        
        # 🔧 MIGLIORA ESTRAZIONE NUMERO OSPITI
        # Prova tutte le possibili chiavi per il numero di ospiti
        guests_raw = None
        possible_guest_keys = ['guest_count', 'guests', 'number', 'people', 'party_size', 'num_guests']
        
        for key in possible_guest_keys:
            if key in parameters and parameters[key]:
                guests_raw = parameters[key]
                print(f"🔧 DEBUG - Found guests in key '{key}': {guests_raw}")
                break
        
        if not guests_raw:
            print(f"🔧 DEBUG - No guests found, trying extract_value on all keys")
            for key in possible_guest_keys:
                extracted = extract_value(parameters.get(key, ''))
                if extracted:
                    guests_raw = extracted
                    print(f"🔧 DEBUG - Extracted guests from '{key}': {guests_raw}")
                    break
        
        # Se ancora non trovato, usa default
        if not guests_raw:
            guests_raw = 2
            print(f"🔧 DEBUG - Using default guests: {guests_raw}")
        
        guests = extract_value(guests_raw)
        
        date = extract_value(parameters.get('day_of_week', parameters.get('date', '')))
        time = extract_value(parameters.get('hour_of_day', parameters.get('time', '')))
        
        print(f"🔧 DEBUG - Extracted: name={name}, phone={phone}, email={email}, guests={guests}, date={date}, time={time}")
        
        # 🔧 MIGLIORA CONVERSIONE NUMERO OSPITI
        try:
            if guests is None or guests == '':
                guest_count = 2  # Default
                print(f"🔧 DEBUG - Using default guest count: {guest_count}")
            else:
                # Prova a convertire, gestendo vari formati
                guest_str = str(guests).strip().lower()
                
                # Rimuovi parole comuni
                guest_str = guest_str.replace('guests', '').replace('people', '').replace('persons', '').strip()
                
                # Converti parole in numeri
                word_to_num = {
                    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
                }
                
                if guest_str in word_to_num:
                    guest_count = word_to_num[guest_str]
                else:
                    guest_count = int(float(guest_str))  # Gestisce anche numeri decimali
                
                print(f"🔧 DEBUG - Converted guest count: {guest_count}")
                
        except (ValueError, TypeError) as e:
            print(f"🔧 DEBUG - Error converting guests '{guests}': {e}")
            guest_count = 2  # Fallback
        
        # Valida range ospiti
        if guest_count < 1 or guest_count > 20:
            return jsonify({
                'fulfillmentText': f"I can accommodate between 1 and 20 guests. You requested {guest_count} guests. Please specify a number between 1 and 20."
            })
        
        # Valida gli altri parametri (escludi guests dalla validazione dato che l'abbiamo già gestito)
        validation_errors = []
        
        # Nome
        if not name or len(str(name).strip()) < 2:
            validation_errors.append("a valid full name (at least 2 characters)")
        
        # Telefono
        if not phone:
            validation_errors.append("your phone number")
        elif not re.match(r'^[\d\s\-\+\(\)]+$', str(phone)):
            validation_errors.append("a valid phone number")
        
        # Email
        if not email:
            validation_errors.append("your email address")
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(email)):
            validation_errors.append("a valid email address")
        
        # Data
        if not date:
            validation_errors.append("the reservation date")
        
        # Ora
        if not time:
            validation_errors.append("the reservation time")
        
        if validation_errors:
            if len(validation_errors) == 1:
                error_text = validation_errors[0]
            elif len(validation_errors) == 2:
                error_text = f"{validation_errors[0]} and {validation_errors[1]}"
            else:
                error_text = f"{', '.join(validation_errors[:-1])}, and {validation_errors[-1]}"
            
            return jsonify({
                'fulfillmentText': f"I need {error_text} to complete your reservation. Please provide the missing information."
            })
        
        # Formatta data e ora
        try:
            formatted_date = format_date_readable(date)
            formatted_time = format_time_readable(time)
        except Exception as e:
            print(f"❌ Error formatting date/time: {e}")
            formatted_date = str(date)
            formatted_time = str(time)
        
        # Controllo duplicati
        try:
            if check_existing_reservation(name, phone, formatted_date, formatted_time):
                return jsonify({
                    'fulfillmentText': f"⚠️ You already have a reservation for {formatted_date} at {formatted_time}. Contact us to modify it."
                })
        except Exception as e:
            print(f"❌ Error checking duplicates: {e}")
            # Continua comunque
        
        # Controlla disponibilità
        try:
            day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
            
            # 🔧 DEBUG LOGS - INDENTAZIONE CORRETTA
            print(f"🔧 DEBUG ML INPUT (CREATE RESERVATION):")
            print(f"  date: {date}")
            print(f"  time: {time}")
            print(f"  guest_count: {guest_count}")
            print(f"  day_of_week: {day_of_week}")  
            print(f"  hour_of_day: {hour_of_day}")
            print(f"  ML results for first 5 tables:")
            
            for table_num in range(1, 6):
                ml_result = check_table_availability(table_num, guest_count, day_of_week, hour_of_day)
                print(f"    Table {table_num}: {'AVAILABLE' if ml_result else 'OCCUPIED'}")
            
            result = find_available_table(guest_count, day_of_week, hour_of_day)
            print(f"  Final result: {result}")
            
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            return jsonify({
                'fulfillmentText': f"Sorry, I'm having trouble checking availability. Please call us at {RESTAURANT_INFO['phone']}."
            })
        
        if result['available']:
            table_num = result['table_number']
            
            # Prepara dati per salvataggio
            reservation_data = {
                'name': str(name).strip(),
                'phone': str(phone).strip(),
                'email': str(email).strip(),
                'guests': guest_count,
                'date': formatted_date,
                'time': formatted_time,
                'table': table_num
            }
            
            # Salva su Google Sheets
            try:
                sheets_saved = save_reservation_to_sheets(reservation_data)
            except Exception as e:
                print(f"❌ Error saving to sheets: {e}")
                sheets_saved = False
            
            # 🆕 INVIA EMAIL DI CONFERMA
            email_sent = False
            admin_notified = False
            
            try:
                from email_manager import send_confirmation_email, send_admin_notification
                email_sent = send_confirmation_email(reservation_data)
                admin_notified = send_admin_notification(reservation_data)
            except Exception as e:
                print(f"❌ Error sending emails: {e}")
            
            # Risposta di successo con multiple messages
            rich_response = {
                "fulfillmentText": "🎉 Reservation Confirmed!",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": ["🎉 Reservation Confirmed!"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👤 Name: {name}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📞 Phone: {phone}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📧 Email: {email}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👥 Number of guests: {guest_count}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📅 Date: {formatted_date}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🕐 Time: {formatted_time}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🪑 Table assigned: {table_num}"]
                        }
                    },
                    {
                        "text": {
                            "text": ["✅ Your reservation is confirmed!"]
                        }
                    }
                ]
            }
            
            # Aggiungi messaggio email se inviata con successo
            if email_sent:
                rich_response["fulfillmentMessages"].append({
                    "text": {
                        "text": ["📧 Confirmation email sent to your address!"]
                    }
                })
            
            # Aggiungi messaggio se sheets non funziona
            if not sheets_saved:
                rich_response["fulfillmentMessages"].append({
                    "text": {
                        "text": ["📝 Note: Our staff will contact you to confirm details."]
                    }
                })
            
            return jsonify(rich_response)
            
        else:
            # Nessuna disponibilità - MULTIPLE MESSAGES
            rich_response = {
                "fulfillmentText": f"😔 Sorry {name}, no tables available",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [f"😔 Sorry {name}, no tables are available for {guest_count} guests at that time."]
                        }
                    }
                ]
            }
            return jsonify(rich_response)
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR in make_reservation: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        
        # Messaggio di errore più specifico
        error_message = f"I'm sorry, there was a technical issue processing your reservation. "
        error_message += f"Please call us directly at {RESTAURANT_INFO['phone']} and we'll be happy to help you immediately."
        
        return jsonify({'fulfillmentText': error_message})
