from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
import requests
import logging
import hubspot_app
# from hubspot.crm.products import SimplePublicObjectInputForCreate, ApiException
# HUBSPOT_CLIENT_ID = '3fd82bfc-3e0a-4707-bb7c-6e4d5995d989'
# HUBSPOT_CLIENT_SECRET = '028b7d9e-6a60-4a8d-8cdd-62c3aad573c9'  
# HUBSPOT_REDIRECT_URI = 'http://localhost:8000/callback1'
 
# STORE_NAME = "fashion-store-aiinfox-com.myshopify.com"  
ACCESS_TOKEN = "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"  
 
logger = logging.getLogger(__name__)
 
 
def store(request):
    if request.method=='POST':
        try:
            request.session['store_name'] = request.POST['store_name']
            logger.info('store_name saved successfully')
            return redirect('dashboard')
        except Exception as e:
            logger.error('Error saving store name: ' + str(e))
    return render(request, 'shopify_store.html')
 
 
def dashboard(request):
    store_name = request.session.get('store_name')
    if not store_name:
        return redirect('store')  
    return render(request, 'shopify_dashboard.html', {'store_name': store_name})
 
 
 
def import_products_to_hubspot(hubspot_access_token,items):
    import hubspot_app
    # from hubspot.crm.products import SimplePublicObjectInputForCreate, ApiException
       
    client = hubspot_app.Client.create(access_token=hubspot_access_token)
 
    for item in items:
        print("Item data:", item)
        price_str = item['variants'][0]['price']
       
        try:
            price = float(price_str.replace(',', '').strip())
            price_in_cents = int(price * 100)  
           
        except ValueError:
            print(f"Invalid price value for product {item['title']}: {price_str}")
            continue
        # Map Shopify product data to HubSpot fields
        properties = {
            "name": item['title'],  
            "price": price_in_cents,  
            "sku": item['variants'][0].get('sku', '112'),  
        }
       
        # Create HubSpot product input
        simple_public_object_input_for_create = SimplePublicObjectInputForCreate(properties=properties)
 
        try:
            # Create product in HubSpot
            api_response = client.crm.products.basic_api.create(simple_public_object_input_for_create=simple_public_object_input_for_create)
            print("Product created in HubSpot:", api_response)
        except ApiException as e:
            print(f"Exception when creating product in HubSpot: {e}")
 
def get_products(request):
    if request.method == 'POST':
        store_name = request.session.get('store_name')
        hubspot_access_token = request.session.get('hubspot_access_token')
 
        if not store_name:
            return JsonResponse({"error": "Store name not found in session"}, status=400)
       
        url = f"https://{store_name}.myshopify.com/admin/api/2021-07/products.json"
        headers = {'X-Shopify-Access-Token': ACCESS_TOKEN}
 
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            products = response.json().get('products', [])
            import_products_to_hubspot(hubspot_access_token,products)
            return JsonResponse({"message": f"Synced {len(products)} products successfully!"})
        except requests.exceptions.RequestException as e:
            logger.error(f"Error syncing products: {e}")
            return JsonResponse({"error": "Failed to sync products"}, status=500)
    return redirect('dashboard')
 
def import_order_to_hubspot(hubspot_access_token,orders):
   
       
    # Initialize HubSpot Client
    client = hubspot_app.Client.create(access_token=hubspot_access_token)
    for order in orders:
        order_data = {
            "inputs": [
                {
                    "properties": {
                        "hs_external_order_id": order['id'],
                        "hs_order_name":order['id'],
                        "hs_billing_address_email": order['email'],
                        "hs_total_price": order['total_price'],
                        "hs_external_created_date": order['created_at'],
                        "hs_currency_code": order['currency'],  # Add the currency code
                        "hs_shipping_address_name": order['shipping_address']['address1'] if order['shipping_address'] else None,
                    }
                }
            ]
        }
 
        # HubSpot API endpoint to create or import orders
        url = "https://api.hubapi.com/crm/v3/objects/orders/batch/create"  # For importing, use this endpoint
        headers = {
            'accept': "application/json",
            'content-type': "application/json",
            'authorization': f"Bearer {hubspot_access_token}"
        }
 
        # Make POST request to HubSpot API to import orders
        response = requests.post(url, json=order_data, headers=headers)
 
        if response.status_code == 201:
            print(f"Successfully imported order {order['id']} to HubSpot.")
        else:
            print(f"Failed to import order {order['id']}: {response.status_code}, {response.text}")
 
 
def get_orders(request):
    if request.method == 'POST':
        hubspot_access_token = request.session.get('hubspot_access_token')
 
        store_name = request.session.get('store_name')
        if not store_name:
            return JsonResponse({"error": "Store name not found in session"}, status=400)
       
        url = f"https://{store_name}.myshopify.com/admin/api/2021-07/orders.json"
        headers = {'X-Shopify-Access-Token': ACCESS_TOKEN}
 
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            orders = response.json().get('orders', [])
            if orders:
                import_order_to_hubspot(hubspot_access_token,orders)
            return JsonResponse({"message": f"Synced {len(orders)} orders successfully!"})
        except requests.exceptions.RequestException as e:
            logger.error(f"Error syncing orders: {e}")
            return JsonResponse({"error": "Failed to sync orders"}, status=500)
    return redirect('dashboard')
 
 