"""
Utility ML e gestione disponibilità tavoli - VERSIONE CORRETTA CON FALLBACK
"""
import joblib
import numpy as np
import os
from datetime import datetime

# Variabile globale per il modello
model = None
model_loaded = False

def load_model():
    """Carica il modello ML con controlli migliorati"""
    global model, model_loaded
    
    try:
        # Prova diversi percorsi per il modello
        possible_paths = [
            'restaurant_model_client.pkl',
            './restaurant_model_client.pkl',
            os.path.join(os.path.dirname(__file__), 'restaurant_model_client.pkl'),
            'models/restaurant_model_client.pkl'
        ]
        
        model_found = False
        for path in possible_paths:
            if os.path.exists(path):
                print(f"🔧 DEBUG - Trovato modello in: {path}")
                model = joblib.load(path)
                model_loaded = True
                model_found = True
                print("✅ ML Model loaded successfully!")
                break
        
        if not model_found:
            print("❌ Model file not found in any expected location!")
            print(f"🔧 DEBUG - Percorsi provati: {possible_paths}")
            print(f"🔧 DEBUG - Current working directory: {os.getcwd()}")
            print(f"🔧 DEBUG - Files in current directory: {os.listdir('.')}")
            model_loaded = False
            
    except Exception as e:
        print(f"❌ Error loading ML model: {e}")
        print(f"🔧 DEBUG - Error type: {type(e)}")
        model = None
        model_loaded = False

# Carica il modello all'import
load_model()

def check_table_availability(table_number, guest_count, day_of_week, hour_of_day):
    """Usa ML model per controllare disponibilità tavolo con fallback intelligente"""
    global model, model_loaded
    
    print(f"🔧 DEBUG - check_table_availability called with: table={table_number}, guests={guest_count}, day={day_of_week}, hour={hour_of_day}")
    print(f"🔧 DEBUG - Model loaded: {model_loaded}, Model object: {model is not None}")
    
    if not model_loaded or model is None:
        print("⚠️ ML Model not available, using fallback logic")
        # Fallback intelligente basato su regole semplici
        return fallback_availability_check(table_number, guest_count, day_of_week, hour_of_day)
    
    try:
        # Valida input
        if not (1 <= table_number <= 20):
            print(f"❌ Invalid table number: {table_number}")
            return False
            
        if not (1 <= guest_count <= 20):
            print(f"❌ Invalid guest count: {guest_count}")
            return False
            
        if not (0 <= day_of_week <= 6):
            print(f"❌ Invalid day of week: {day_of_week}")
            return False
            
        if not (0 <= hour_of_day <= 23):
            print(f"❌ Invalid hour: {hour_of_day}")
            return False
        
        # Prepara input per ML
        input_data = np.array([[table_number, guest_count, day_of_week, hour_of_day]])
        print(f"🔧 DEBUG - ML input array: {input_data}")
        
        # Fai predizione
        prediction = model.predict(input_data)[0]
        print(f"🔧 DEBUG - ML prediction: {prediction}")
        
        # 0 = available, 1 = occupied
        is_available = prediction == 0
        print(f"🔧 DEBUG - Is available: {is_available}")
        
        return is_available
        
    except Exception as e:
        print(f"❌ Error in ML prediction: {e}")
        print(f"🔧 DEBUG - Falling back to rule-based system")
        # Fallback in caso di errore ML
        return fallback_availability_check(table_number, guest_count, day_of_week, hour_of_day)


def fallback_availability_check(table_number, guest_count, day_of_week, hour_of_day):
    """Sistema di fallback basato su regole quando ML non funziona"""
    print(f"🔧 DEBUG - Using fallback availability check")
    
    # Regole semplici per simulare disponibilità
    # In un ambiente reale, questo dovrebbe controllare un database
    
    # Orari di chiusura
    if hour_of_day < 9 or hour_of_day > 21:
        print(f"🔧 DEBUG - Outside opening hours")
        return False
    
    # Weekend più occupato
    if day_of_week in [5, 6]:  # Sabato, Domenica
        if hour_of_day in [19, 20]:  # Ore di punta
            # Simula 70% occupazione
            availability = (table_number + hour_of_day + day_of_week) % 10 < 7
        else:
            # Simula 50% occupazione
            availability = (table_number + hour_of_day + day_of_week) % 10 < 5
    else:
        # Giorni feriali - meno occupati
        if hour_of_day in [12, 13, 19, 20]:  # Ore di punta
            # Simula 50% occupazione
            availability = (table_number + hour_of_day + day_of_week) % 10 < 5
        else:
            # Simula 30% occupazione
            availability = (table_number + hour_of_day + day_of_week) % 10 < 3
    
    print(f"🔧 DEBUG - Fallback result: {availability}")
    return availability


def find_available_table(guest_count, day_of_week, hour_of_day):
    """
    Trova tavolo disponibile automaticamente - VERSIONE MIGLIORATA
    NON richiede table_number dal cliente
    """
    print(f"🔧 DEBUG - find_available_table called with: guests={guest_count}, day={day_of_week}, hour={hour_of_day}")
    
    available_tables = []
    
    # Controlla tutti i tavoli (1-20)
    for table_number in range(1, 21):
        if check_table_availability(table_number, guest_count, day_of_week, hour_of_day):
            available_tables.append(table_number)
            print(f"🔧 DEBUG - Table {table_number} is AVAILABLE")
        else:
            print(f"🔧 DEBUG - Table {table_number} is OCCUPIED")
    
    print(f"🔧 DEBUG - Total available tables: {available_tables}")
    
    if available_tables:
        # Scegli il miglior tavolo per il numero di ospiti
        if guest_count <= 2:
            # Preferisci tavoli piccoli (1-8)
            small_tables = [t for t in available_tables if t <= 8]
            best_table = small_tables[0] if small_tables else available_tables[0]
        elif guest_count <= 4:
            # Preferisci tavoli medi (9-15)
            medium_tables = [t for t in available_tables if 9 <= t <= 15]
            best_table = medium_tables[0] if medium_tables else available_tables[0]
        else:
            # Preferisci tavoli grandi (16-20)
            large_tables = [t for t in available_tables if t >= 16]
            best_table = large_tables[0] if large_tables else available_tables[0]

        result = {
            'available': True,
            'table_number': best_table,
            'total_available': len(available_tables)
        }
        
    else:
        result = {
            'available': False,
            'table_number': None,
            'total_available': 0
        }
    
    print(f"🔧 DEBUG - find_available_table result: {result}")
    return result


def get_model_status():
    """Restituisce lo stato del modello ML"""
    global model_loaded, model
    status = model_loaded and model is not None
    print(f"🔧 DEBUG - get_model_status: {status}")
    return status


def force_enable_availability():
    """Forza l'abilitazione delle disponibilità per testing"""
    print("🔧 DEBUG - FORCING AVAILABILITY FOR ALL TABLES")
    
    def always_available(*args, **kwargs):
        return True
    
    # Sostituisce temporaneamente la funzione
    global check_table_availability
    check_table_availability = always_available
    
    return True


def test_ml_model():
    """Test completo del modello ML"""
    print("\n🔧 DEBUG - TESTING ML MODEL:")
    print(f"  Model loaded: {get_model_status()}")
    print(f"  Model object: {model}")
    
    if model:
        print(f"  Model type: {type(model)}")
        try:
            # Test input shape
            test_input = np.array([[1, 2, 0, 12]])
            test_prediction = model.predict(test_input)
            print(f"  Test prediction successful: {test_prediction}")
        except Exception as e:
            print(f"  Test prediction failed: {e}")
    
    print("\n🔧 DEBUG - TESTING AVAILABILITY FUNCTIONS:")
    
    # Test scenari diversi
    test_scenarios = [
        (1, 2, 0, 12),  # Table 1, 2 guests, Monday, 12pm
        (1, 2, 1, 19),  # Table 1, 2 guests, Tuesday, 7pm
        (5, 4, 5, 20),  # Table 5, 4 guests, Saturday, 8pm
        (10, 6, 6, 18), # Table 10, 6 guests, Sunday, 6pm
    ]
    
    for table, guests, day, hour in test_scenarios:
        result = check_table_availability(table, guests, day, hour)
        print(f"  Table {table}, {guests} guests, day {day}, hour {hour}: {'AVAILABLE' if result else 'OCCUPIED'}")
    
    print("\n🔧 DEBUG - TESTING find_available_table:")
    
    find_scenarios = [
        (2, 1, 19),  # 2 guests, Tuesday, 7pm
        (4, 5, 20),  # 4 guests, Saturday, 8pm
        (6, 0, 12),  # 6 guests, Monday, 12pm
    ]
    
    for guests, day, hour in find_scenarios:
        availability = find_available_table(guests, day, hour)
        print(f"  {guests} guests, day {day}, hour {hour}: {availability}")


# Test automatico all'import se in debug mode
if __name__ == "__main__":
    test_ml_model()
