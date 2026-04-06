from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Data file path
DATA_FILE = 'data.xlsx'

# Initialize data file if it doesn't exist
def init_data_file():
    if not os.path.exists(DATA_FILE):
        # Create empty DataFrames for products
        df_products = pd.DataFrame(columns=['id', 'name', 'type', 'factory', 'description', 'created_at'])
        df_products.to_excel(DATA_FILE, sheet_name='Products', index=False)

# Load products from Excel
def load_products():
    if not os.path.exists(DATA_FILE):
        init_data_file()
    try:
        df = pd.read_excel(DATA_FILE, sheet_name='Products')
        return df.to_dict('records')
    except Exception as e:
        print(f"Error loading products: {e}")
        return []

# Save products to Excel
def save_products(products):
    try:
        df = pd.DataFrame(products)
        df.to_excel(DATA_FILE, sheet_name='Products', index=False)
    except Exception as e:
        print(f"Error saving products: {e}")

# Generate unique ID
def generate_id():
    return str(uuid.uuid4())[:8]

# Get current timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# API Routes
@app.route('/api/factory/<factory_type>', methods=['POST'])
def create_products(factory_type):
    """Create products using the specified factory"""
    if factory_type not in ['X', 'Y']:
        return jsonify({'error': 'Invalid factory type. Use X or Y'}), 400
    
    # Load existing products
    products = load_products()
    
    # Create new products based on factory type
    new_products = []
    
    # Product A
    product_a_name = f"Product{factory_type}A_{get_timestamp().replace(':', '').replace('-', '')}"
    product_a = {
        'id': generate_id(),
        'name': product_a_name,
        'type': 'A',
        'factory': f'ConcreteFactory{factory_type}',
        'description': f'This is a Product A created by ConcreteFactory{factory_type}. It implements the ProductA interface.',
        'created_at': get_timestamp()
    }
    new_products.append(product_a)
    
    # Product B
    product_b_name = f"Product{factory_type}B_{get_timestamp().replace(':', '').replace('-', '')}"
    product_b = {
        'id': generate_id(),
        'name': product_b_name,
        'type': 'B',
        'factory': f'ConcreteFactory{factory_type}',
        'description': f'This is a Product B created by ConcreteFactory{factory_type}. It implements the ProductB interface.',
        'created_at': get_timestamp()
    }
    new_products.append(product_b)
    
    # Add new products to existing ones
    products.extend(new_products)
    
    # Save to file
    save_products(products)
    
    return jsonify({
        'success': True,
        'message': f'Successfully created products using ConcreteFactory{factory_type}',
        'products': new_products
    })

@app.route('/api/products', methods=['GET'])
def get_all_products():
    """Get all products"""
    products = load_products()
    return jsonify({
        'success': True,
        'count': len(products),
        'products': products
    })

@app.route('/api/factories', methods=['GET'])
def get_factories():
    """Get available factories"""
    factories = [
        {
            'name': 'ConcreteFactoryX',
            'description': 'Creates ProductAX and ProductBX',
            'methods': ['createProductA()', 'createProductB()'],
            'products': ['ProductAX', 'ProductBX']
        },
        {
            'name': 'ConcreteFactoryY',
            'description': 'Creates ProductAY and ProductBY',
            'methods': ['createProductA()', 'createProductB()'],
            'products': ['ProductAY', 'ProductBY']
        }
    ]
    return jsonify({
        'success': True,
        'factories': factories
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Factory Pattern API is running',
        'timestamp': get_timestamp()
    })

if __name__ == '__main__':
    # Initialize data file
    init_data_file()
    app.run(host='0.0.0.0', port=5000, debug=True)