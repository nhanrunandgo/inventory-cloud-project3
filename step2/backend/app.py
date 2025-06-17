from flask import Flask, jsonify, request
import json
import os
import db_handler as db
from woocommerce_handler import woocommerce_handler
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Root endpoint
@app.route('/')
def home():
    return jsonify(message="Welcome to Inventory Backend Server", status="OK")

@app.route('/inventory', methods=['GET'])
def get_inventory():
    data, status = db.database_provider(db.PRODUCT_GETTER_QUERY)
    return data 

@app.route('/orders', methods=['GET'])
def get_orders():
    orders, status = db.database_provider(db.ORDER_GETTER_QUERY)
    
    # Xử lý định dạng lại
    formatted_orders = []
    for order in orders:
        # Parse JSON từ chuỗi items
        item_list = json.loads(order['items'])
        formatted_items = [
            f"{item['post_title']} x{item['quantity']}" for item in item_list
        ]
        
        formatted_orders.append({
            "id": order["id"],
            "customer": order["customer"],
            "items": formatted_items,
            "totalCost": float(order["totalCost"]),
            "status": order["status"].replace("wc-", ""),  # Loại bỏ tiền tố 'wc-'
            "date": order["date"].strftime("%Y-%m-%d")  # Chỉ lấy ngày yyyy-mm-dd
        })
    return formatted_orders 

@app.route('/inventory/<int:item_id>', methods=['PUT'])
def update_inventory(item_id):
    data = request.get_json()
    
    # Validate incoming data
    if not data or 'id' not in data or data['id'] != item_id:
        return jsonify({"error": "Invalid input"}), 400
    
    # Create a sending message with woocommerce form
    try:
        woocommerce_category = f"products/{item_id}"
        woocommerce_json = {
            "name": data['name'],
            "manage_stock": True,
            "stock_quantity": data['quantity'],
            "regular_price": f"{data['regularPrice']}",
            "sale_price": f"{data['salePrice']}"
        }
        response = woocommerce_handler(woocommerce_category, woocommerce_json)
        print(f"Inventory #{response['id']}: \n{woocommerce_json}\n")
    except Exception as e: 
        return jsonify({"error": {str(e)}}), 400
    
    return jsonify({"message": "Item updated successfully",}), 200

@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    woocommerce_json = request.get_json()
    
    # Validate incoming data
    if not woocommerce_json or "status" not in woocommerce_json:
        return jsonify({"error": "Invalid input"}), 400
    
    try:
        woocommerce_category = f'orders/{order_id}'
        response = woocommerce_handler(woocommerce_category, woocommerce_json)
        print(f"Order #{response['id']}: \n{woocommerce_json}\n")
    except Exception as e:
        return jsonify({"error": {str(e)}}), 400

    return jsonify({"message": "Item updated successfully",}), 200

# Error handling example
@app.errorhandler(404)
def not_found(error):
    return jsonify(error="Resource not found"), 404

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run in production mode for real deployment
    # For development, you might want to use debug=True
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG') == '1')