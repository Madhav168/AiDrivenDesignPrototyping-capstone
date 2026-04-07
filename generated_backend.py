from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# Initialize data.xlsx if it doesn't exist
DATA_FILE = 'data.xlsx'

def init_data_file():
    if not os.path.exists(DATA_FILE):
        # Create initial structure with sample data
        df_orders = pd.DataFrame(columns=[
            'customerId', 'customerName', 'orderId', 'items', 'totalAmount', 
            'paymentMethod', 'status', 'timestamp'
        ])
        with pd.ExcelWriter(DATA_FILE, engine='openpyxl') as writer:
            df_orders.to_excel(writer, sheet_name='Orders', index=False)

init_data_file()

@app.route('/api/order/calculateTotal', methods=['POST'])
def calculate_total():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required_fields = ['customerId', 'customerName', 'orderId', 'items']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    # Simple calculation: $10 per item for demo purposes
    item_count = len(data['items'])
    total_amount = item_count * 10.0

    # Return calculated total
    return jsonify({
        'totalAmount': total_amount,
        'itemCount': item_count,
        'message': f'Total calculated for {item_count} items.'
    })

@app.route('/api/payment/process', methods=['POST'])
def process_payment():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'order' not in data or 'paymentMethod' not in data:
        return jsonify({'error': 'Order and paymentMethod are required'}), 400

    order = data['order']
    payment_method = data['paymentMethod']

    # Validate order structure
    required_order_fields = ['customerId', 'customerName', 'orderId', 'items', 'totalAmount']
    for field in required_order_fields:
        if field not in order:
            return jsonify({'error': f'Order missing required field: {field}'}), 400

    # Simulate payment processing
    # In a real app, this would integrate with a real payment gateway
    success = True  # Simulate always successful for demo
    status = "SUCCESS" if success else "FAILED"
    message = "Payment processed successfully." if success else "Payment failed."

    # Record the transaction
    record_transaction(order, payment_method, status)

    return jsonify({
        'status': status,
        'message': message,
        'transactionId': f'TXN_{order["orderId"]}_{payment_method.upper()}_{pd.Timestamp.now().strftime("%Y%m%d%H%M%S")}'
    })

@app.route('/api/data/save', methods=['POST'])
def save_data():
    try:
        # Read existing data
        df_orders = pd.read_excel(DATA_FILE, sheet_name='Orders')
        
        # If no data exists, create empty DataFrame
        if df_orders.empty:
            df_orders = pd.DataFrame(columns=[
                'customerId', 'customerName', 'orderId', 'items', 'totalAmount', 
                'paymentMethod', 'status', 'timestamp'
            ])
        
        # Save back to Excel (this will overwrite the file)
        with pd.ExcelWriter(DATA_FILE, engine='openpyxl') as writer:
            df_orders.to_excel(writer, sheet_name='Orders', index=False)
        
        return jsonify({
            'message': f'Data saved successfully to {DATA_FILE}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def record_transaction(order, payment_method, status):
    """Record a transaction in the Excel file"""
    try:
        # Read existing data
        df_orders = pd.read_excel(DATA_FILE, sheet_name='Orders')
        
        # Create new row
        new_row = {
            'customerId': order['customerId'],
            'customerName': order['customerName'],
            'orderId': order['orderId'],
            'items': ', '.join(order['items']),
            'totalAmount': order['totalAmount'],
            'paymentMethod': payment_method,
            'status': status,
            'timestamp': pd.Timestamp.now()
        }
        
        # Append new row
        df_orders = pd.concat([df_orders, pd.DataFrame([new_row])], ignore_index=True)
        
        # Save back to Excel
        with pd.ExcelWriter(DATA_FILE, engine='openpyxl') as writer:
            df_orders.to_excel(writer, sheet_name='Orders', index=False)
            
    except Exception as e:
        print(f"Error recording transaction: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)