import json
import boto3
import os
import hmac
import hashlib
import base64
from datetime import datetime

def validate_request(event):
    """Validate WooCommerce webhook signature"""
    secret = os.environ['WC_SECRET']
    
    # Get signature from headers (case-insensitive)
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    received_sig = headers.get('x-wc-webhook-signature', '')
    
    # Get raw request body as string
    body = event.get('body', '')
    
    # If body is a dict (like in test events), convert to JSON string
    if isinstance(body, dict):
        body = json.dumps(body)
    
    # Compute expected signature
    digest = hmac.new(
        secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    expected_sig = base64.b64encode(digest).decode()
    
    # Securely compare signatures
    return hmac.compare_digest(received_sig, expected_sig)

def lambda_handler(event, context):
    # 1. Validate webhook signature
    if not validate_request(event):
        print("Webhook validation failed - potential security issue")
        return {
            'statusCode': 401,
            'body': 'Invalid signature'
        }
    
    # 2. Parse and process order
    try:
        # Get body content (might be string or already parsed)
        body = event.get('body', '{}')
        
        # Parse JSON if we got a string
        if isinstance(body, str):
            order = json.loads(body)
        else:
            order = body
            
        # Only process specific statuses
        status = order.get('status', '')
        print(f"Processing {status} order #{order.get('id')}")

        if status == 'processing':
            return processing_handler(order)
        elif status == 'completed':
            return completed_handler(order)
        
        print(f"Ignoring non-processable status: {status}")
        return {'statusCode': 200, 'body': f'Ignored status: {status}'}
        
    except Exception as e:
        print(f"Error processing order: {str(e)}")
        return {'statusCode': 500, 'body': 'Processing error'}

def completed_handler(order_data):
    """Send formatted order email to customer"""
    try:
        # Extract order details
        billing = order_data.get('billing', {})
        customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
        order_id = order_data.get('id', 'N/A')

        # Format order date
        order_date_iso = order_data.get('date_created_gmt', '')
        try:
            order_date = datetime.strptime(order_date_iso, "%Y-%m-%dT%H:%M:%S").strftime("%B %d, %Y %H:%M")
        except:
            order_date = order_date_iso

        # Format completion date date
        completion_date_iso = order_data.get('date_completed_gmt', '')
        try:
            completion_date = datetime.strptime(completion_date_iso, "%Y-%m-%dT%H:%M:%S").strftime("%B %d, %Y %H:%M")
        except:
            completion_date = completion_date_iso
        message = f"""
Let's go shopping

Hello {customer_name}, your order #{order_id} has been shipped to you.

Order Summary:
Order number: {order_id}
Order date: {order_date}
Completion date: {completion_date}
Thank you for choosing Let's go shopping. We hope you enjoy your purchase and look forward to serving you again soon!
"""
        return send_email_handler(f"Order Completed #{order_id}", message)
    except Exception as e:
        print(f"Fetching data: {str(e)}")
        return {'statusCode': 500, 'body': 'Data fetching error'}

def processing_handler(order_data):
    """Send formatted order email to customer"""
    try:
        # Extract order details
        billing = order_data.get('billing', {})
        shipping = order_data.get('shipping', {})
        customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
        order_id = order_data.get('id', 'N/A')
        
        # Format order date
        order_date_iso = order_data.get('date_created_gmt', '')
        try:
            order_date = datetime.strptime(order_date_iso, "%Y-%m-%dT%H:%M:%S").strftime("%B %d, %Y %H:%M")
        except:
            order_date = order_date_iso
        
        # Prepare items table
        line_items = order_data.get('line_items', [])
        items_text = ""
        total_quantity = 0
        for item in line_items:
            name = item.get('name', 'Unnamed Product')
            quantity = item.get('quantity', 0)
            price = format_currency(item.get('price', 0), order_data.get('currency_symbol', '₫'))
            total = format_currency(item.get('total', 0), order_data.get('currency_symbol', '₫'))
            total_quantity += quantity
            items_text += f"- {name}: {quantity} x {price} = {total}\n"
        
        # Prepare shipping address
        shipping_address = f"""
{shipping.get('first_name', '')} {shipping.get('last_name', '')}
{shipping.get('address_1', '')}
{shipping.get('city', '')}, {shipping.get('state', '')} {shipping.get('postcode', '')}
{shipping.get('country', '')}
""".strip()

        # Create plain text message
        message = f"""
Let's go shopping

Hello {customer_name}, thank you for ordering at Let's go shopping.

Order Summary:
Order number: {order_id}
Order date: {order_date}
Payment method: {order_data.get('payment_method_title', 'N/A')}

Items:
{items_text}
Total items: {total_quantity}
Subtotal: {format_currency(order_data.get('total', 0), order_data.get('currency_symbol', '₫'))}
Tax: {format_currency(order_data.get('total_tax', 0), order_data.get('currency_symbol', '₫'))}
Grand total: {format_currency(order_data.get('total', 0), order_data.get('currency_symbol', '₫'))}

Shipping address:
{shipping_address}

We'll notify you when your order ships!
"""
        return send_email_handler(f"Order Confirmation #{order_id}", message)
    except Exception as e:
        print(f"Fetching data: {str(e)}")
        return {'statusCode': 500, 'body': 'Data fetching error'}

def send_email_handler(subject, message):
    try:
        # Get the SNS Topic ARN from an environment variable.
        # This is a best practice for managing your resources.
        SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
        
        if not SNS_TOPIC_ARN:
            print("Error: Please set the SNS_TOPIC_ARN environment variable.")
            return {
                'statusCode': 500,
                'body': json.dumps('Server configuration error: SNS Topic ARN not set.')
            }
        
        # Publish to SNS
        sns = boto3.client('sns')
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        
        print("Notification sent via SNS:", response['MessageId'])
        return {'statusCode': 200, 'body': 'Order notification sent successfully'}
        
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return {'statusCode': 500, 'body': 'Email processing error'}

def format_currency(amount, symbol):
    """Format currency amount with symbol"""
    try:
        # Handle both string and number types
        amount_float = float(amount)
        return f"{symbol}{amount_float:,.2f}"
    except:
        return f"{symbol}{amount}"