"""
ML Utilities and table availability management
"""
import joblib
import numpy as np
import os
from datetime import datetime

# Global variable for the ML model
model = None
model_loaded = False

def load_model():
    """Load ML model with improved checks and fallback handling"""
    global model, model_loaded
    
    try:
        # Try different paths for the model file
        possible_paths = [
            'restaurant_model_client.pkl',           # Current directory
            './restaurant_model_client.pkl',         # Explicit current directory
            os.path.join(os.path.dirname(__file__), 'restaurant_model_client.pkl'),  # Same directory as this file
            'models/restaurant_model_client.pkl'     # Models subdirectory
        ]
        
        model_found = False
        for path in possible_paths:
            if os.path.exists(path):
                print(f"🔧 DEBUG - Found model at: {path}")
                model = joblib.load(path)
                model_loaded = True
                model_found = True
                print("✅ ML Model loaded successfully!")
                break
        
        if not model_found:
            print("❌ Model file not found in any expected location!")
            print(f"🔧 DEBUG - Tried paths: {possible_paths}")
            print(f"🔧 DEBUG - Current working directory: {os.getcwd()}")
            print(f"🔧 DEBUG - Files in current directory: {os.listdir('.')}")
            model_loaded = False
            
    except Exception as e:
        print(f"❌ Error loading ML model: {e}")
        print(f"🔧 DEBUG - Error type: {type(e)}")
        model = None
        model_loaded = False

# Load the model on import
load_model()

def check_table_availability(table_number, guest_count, day_of_week, hour_of_day, language_code='en'):
    """Use ML model to check table availability with intelligent fallback and multilingual support"""
    global model, model_loaded
    
    print(f"🔧 DEBUG - check_table_availability called with: table={table_number}, guests={guest_count}, day={day_of_week}, hour={hour_of_day}")
    print(f"🔧 DEBUG - Model loaded: {model_loaded}, Model object: {model is not None}")
    
    # Check if ML model is available, otherwise use fallback logic
    if not model_loaded or model is None:
        print("⚠️ ML Model not available, using fallback logic")
        # Intelligent fallback based on simple rules
        return fallback_availability_check(table_number, guest_count, day_of_week, hour_of_day)
    
    try:
        # Validate input parameters
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
        
        # Prepare input for ML model (must match training data format)
        input_data = np.array([[table_number, guest_count, day_of_week, hour_of_day]])
        print(f"🔧 DEBUG - ML input array: {input_data}")
        
        # Make prediction using trained model
        prediction = model.predict(input_data)[0]
        print(f"🔧 DEBUG - ML prediction: {prediction}")
        
        # Convert prediction to boolean (0 = available, 1 = occupied)
        is_available = prediction == 0
        print(f"🔧 DEBUG - Is available: {is_available}")
        
        return is_available
        
    except Exception as e:
        print(f"❌ Error in ML prediction: {e}")
        print(f"🔧 DEBUG - Falling back to rule-based system")
        # Fallback in case of ML error
        return fallback_availability_check(table_number, guest_count, day_of_week, hour_of_day, language_code)


def fallback_availability_check(table_number, guest_count, day_of_week, hour_of_day, language_code='en'):
    """Rule-based fallback system when ML is not working with multilingual support"""
    print(f"🔧 DEBUG - Using fallback availability check")
    
    # Simple rules to simulate availability
    # In a real environment, this should check a database
    
    # Check restaurant opening hours
    if hour_of_day < 9 or hour_of_day > 21:
        print(f"🔧 DEBUG - Outside opening hours")
        return False
    
    # Weekend is busier than weekdays
    if day_of_week in [5, 6]:  # Saturday, Sunday
        if hour_of_day in [19, 20]:  # Peak hours
            # Simulate 70% occupancy
            availability = (table_number + hour_of_day + day_of_week) % 10 < 7
        else:
            # Simulate 50% occupancy
            availability = (table_number + hour_of_day + day_of_week) % 10 < 5
    else:
        # Weekdays - less busy
        if hour_of_day in [12, 13, 19, 20]:  # Peak hours (lunch and dinner)
            # Simulate 50% occupancy
            availability = (table_number + hour_of_day + day_of_week) % 10 < 5
        else:
            # Simulate 30% occupancy
            availability = (table_number + hour_of_day + day_of_week) % 10 < 3
    
    print(f"🔧 DEBUG - Fallback result: {availability}")
    return availability


def find_available_table(guest_count, day_of_week, hour_of_day, language_code='en'):
    """
    Find available table automatically - IMPROVED VERSION with multilingual support
    Does NOT require table_number from customer - automatically selects best table
    """
    print(f"🔧 DEBUG - find_available_table called with: guests={guest_count}, day={day_of_week}, hour={hour_of_day}")
    
    available_tables = []
    
    # Check all tables (1-20) for availability
    for table_number in range(1, 21):
        if check_table_availability(table_number, guest_count, day_of_week, hour_of_day, language_code):
            available_tables.append(table_number)
            print(f"🔧 DEBUG - Table {table_number} is AVAILABLE")
        else:
            print(f"🔧 DEBUG - Table {table_number} is OCCUPIED")
    
    print(f"🔧 DEBUG - Total available tables: {available_tables}")
    
    if available_tables:
        # Choose the best table for the number of guests
        # Table allocation strategy based on party size
        if guest_count <= 2:
            # Prefer small tables (1-8) for couples and small parties
            small_tables = [t for t in available_tables if t <= 8]
            best_table = small_tables[0] if small_tables else available_tables[0]
        elif guest_count <= 4:
            # Prefer medium tables (9-15) for small groups
            medium_tables = [t for t in available_tables if 9 <= t <= 15]
            best_table = medium_tables[0] if medium_tables else available_tables[0]
        else:
            # Prefer large tables (16-20) for big parties
            large_tables = [t for t in available_tables if t >= 16]
            best_table = large_tables[0] if large_tables else available_tables[0]

        # Return success result with assigned table
        result = {
            'available': True,
            'table_number': best_table,
            'total_available': len(available_tables)
        }
        
    else:
        # No tables available
        result = {
            'available': False,
            'table_number': None,
            'total_available': 0
        }
    
    print(f"🔧 DEBUG - find_available_table result: {result}")
    return result


def get_model_status():
    """Return the status of the ML model"""
    global model_loaded, model
    status = model_loaded and model is not None
    print(f"🔧 DEBUG - get_model_status: {status}")
    return status


def force_enable_availability():
    """Force enable availability for all tables (testing purposes)"""
    print("🔧 DEBUG - FORCING AVAILABILITY FOR ALL TABLES")
    
    def always_available(*args, **kwargs):
        """Function that always returns True for availability"""
        return True
    
    # Temporarily replace the function for testing
    global check_table_availability
    check_table_availability = always_available
    
    return True


def test_ml_model():
    """Complete test of the ML model and availability functions"""
    print("\n🔧 DEBUG - TESTING ML MODEL:")
    print(f"  Model loaded: {get_model_status()}")
    print(f"  Model object: {model}")
    
    if model:
        print(f"  Model type: {type(model)}")
        try:
            # Test input shape and prediction functionality
            test_input = np.array([[1, 2, 0, 12]])  # Table 1, 2 guests, Monday, 12pm
            test_prediction = model.predict(test_input)
            print(f"  Test prediction successful: {test_prediction}")
        except Exception as e:
            print(f"  Test prediction failed: {e}")
    
    print("\n🔧 DEBUG - TESTING AVAILABILITY FUNCTIONS:")
    
    # Test different scenarios to validate functionality
    test_scenarios = [
        (1, 2, 0, 12),  # Table 1, 2 guests, Monday, 12pm (weekday lunch)
        (1, 2, 1, 19),  # Table 1, 2 guests, Tuesday, 7pm (weekday dinner)
        (5, 4, 5, 20),  # Table 5, 4 guests, Saturday, 8pm (weekend peak)
        (10, 6, 6, 18), # Table 10, 6 guests, Sunday, 6pm (weekend dinner)
    ]
    
    for table, guests, day, hour in test_scenarios:
        result = check_table_availability(table, guests, day, hour)
        print(f"  Table {table}, {guests} guests, day {day}, hour {hour}: {'AVAILABLE' if result else 'OCCUPIED'}")
    
    print("\n🔧 DEBUG - TESTING find_available_table:")
    
    # Test automatic table finding for different party sizes and times
    find_scenarios = [
        (2, 1, 19),  # 2 guests, Tuesday, 7pm (small party, dinner)
        (4, 5, 20),  # 4 guests, Saturday, 8pm (medium party, weekend peak)
        (6, 0, 12),  # 6 guests, Monday, 12pm (large party, lunch)
    ]
    
    for guests, day, hour in find_scenarios:
        availability = find_available_table(guests, day, hour)
        print(f"  {guests} guests, day {day}, hour {hour}: {availability}")


# Automatic test on import if in debug mode
if __name__ == "__main__":
    test_ml_model()
