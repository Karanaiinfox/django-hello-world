from django.shortcuts import render,redirect
import requests

import requests
import urllib.parse
import datetime
import logging
from django.http import JsonResponse
import requests

from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
# from client_id import QuickBooks
import json


import pandas as pd
import requests
import urllib.parse
import logging

# Create your views here.
HUBSPOT_CLIENT_ID = '3fd82bfc-3e0a-4707-bb7c-6e4d5995d989'
HUBSPOT_CLIENT_SECRET = '028b7d9e-6a60-4a8d-8cdd-62c3aad573c9'  
HUBSPOT_REDIRECT_URI = 'http://localhost:8000/callback1'
# Your application credentials
client_ID='ABbp8Tfuraz9vM0TVYhnrKTftZsBg4GeeNFXYKo9ci2syWtHf2'
client_secret='mVHMd8bmRyv5XBj9jZxgfkqJpqiyJln4FG6wjvrS'
CLIENT_ID = 'ABbp8Tfuraz9vM0TVYhnrKTftZsBg4GeeNFXYKo9ci2syWtHf2'
client_secret = 'mVHMd8bmRyv5XBj9jZxgfkqJpqiyJln4FG6wjvrS'
environment = 'sandbox'
REDIRECT_URI = 'http://localhost:8000/callback'  




if environment == 'sandbox':
    auth_base_url = 'https://appcenter.intuit.com/connect/oauth2'
    token_url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
    api_base_url = 'https://sandbox-quickbooks.api.intuit.com/v3/company/'
else:
    auth_base_url = 'https://appcenter.intuit.com/connect/oauth2'
    token_url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
    api_base_url = 'https://quickbooks.api.intuit.com/v3/company/'
company_id='9341453286798270'
# Scopes for the API
scopes = 'com.intuit.quickbooks.accounting'


def login(request):
    hubspot_auth_url = (
        f"https://app.hubspot.com/oauth/authorize?client_id={HUBSPOT_CLIENT_ID}"
        f"&redirect_uri={HUBSPOT_REDIRECT_URI}&scope=crm.objects.contacts.write%20"
        "crm.schemas.contacts.write%20oauth%20crm.schemas.contacts.read%20"
        "crm.objects.contacts.read"
    )

    return redirect(hubspot_auth_url)

def callback1(request):
    code = request.args.get('code')
    if not code:
        return "Authorization failed: No code provided", 400
    
    token_url = 'https://api.hubapi.com/oauth/v1/token'
    
    data = {
        'grant_type': 'authorization_code',
        'client_id': HUBSPOT_CLIENT_ID,
        'client_secret': HUBSPOT_CLIENT_SECRET,
        'redirect_uri': HUBSPOT_REDIRECT_URI,
        'code': code
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        tokens = response.json()
        request.session['hubspot_access_token'] = tokens['access_token']
        return redirect('/')  
    else:
        error_response = response.json() if response.content else {'error': 'Unknown error'}
        return JsonResponse({"error": error_response}), response.status_code
def index(request):
    auth_params = {
        'client_id': CLIENT_ID,
        
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': scopes,
        'state': 'e9d2f3c4b5a6d7e8f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4'  # Replace with a secure random string
    }
    auth_url = f"{auth_base_url}?{urllib.parse.urlencode(auth_params)}"
    print(auth_url,'auth_urlauth_urlauth_urlauth_urlauth_urlauth_urlauth_url')
    return redirect(auth_url)

def callback(request):
    error = request.args.get('error')
    if error:
        return f"Error during authentication: {error}", 400

    auth_code = request.args.get('code')
    realm_id = request.args.get('realmId')
    if not auth_code or not realm_id:
        return "Authorization code or realm ID not found in callback.", 400

    request.session['realm_id'] = realm_id

    # Exchange authorization code for access token
    token_payload = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI
    }
    auth_header = requests.auth.HTTPBasicAuth(CLIENT_ID, client_secret)
    token_response = requests.post(
        token_url,
        data=token_payload,
        auth=auth_header,
        headers={'Accept': 'application/json'}
    )

    if token_response.status_code != 200:
        return f"Failed to obtain access token: {token_response.text}", 400

    token_json = token_response.json()
    request.session['access_token'] = token_json['access_token']
    request.session['refresh_token'] = token_json['refresh_token']
    expires_in = token_json.get('expires_in', 3600)
    request.session['token_expiry'] = (datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)).isoformat()

    return redirect('/invoices')
def is_token_expired(request):
    expiry = request.session.get('token_expiry')
    if not expiry:
        return True
    return datetime.datetime.utcnow() >= datetime.datetime.fromisoformat(expiry)

def refresh_access_token(request):
    refresh_payload = {
        'grant_type': 'refresh_token',
        'refresh_token': request.session.get('refresh_token')
    }
    auth_header = requests.auth.HTTPBasicAuth(CLIENT_ID, client_secret)
    refresh_response = requests.post(
        token_url,
        data=refresh_payload,
        auth=auth_header,
        headers={'Accept': 'application/json'}
    )

    if refresh_response.status_code != 200:
        print(f"Failed to refresh access token: {refresh_response.text}")
        return False

    token_json = refresh_response.json()
    request.session['access_token'] = token_json['access_token']
    request.session['refresh_token'] = token_json['refresh_token']
    expires_in = token_json.get('x_refresh_token_expires_in', 3600)
    request.session['token_expiry'] = (datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)).isoformat()
    return True
def save_invoices_to_json(data):
    # Extract the invoices from the response
    invoices = data.get('QueryResponse', {}).get('Invoice', [])

    # Save invoices to a JSON file
    with open('invoices.json', 'w') as json_file:
        json.dump(invoices, json_file, indent=4)  # 'indent=4' makes the JSON file readable

    # Return the invoices as a JSON response (Flask function)
    return JsonResponse({'invoices': invoices})

def find_or_create_customer(email,name,address,phone ,City ,Country ,PostalCode,request):
    
    headers = {
        'Authorization': f'Bearer {request.session["access_token"]}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    query = f"SELECT * FROM Customer WHERE PrimaryEmailAddr = '{email}'"
    url = f"{api_base_url}{request.session['realm_id']}/query?query={urllib.parse.quote(query)}&minorversion=65"
    response = requests.get(url, headers=headers)

    if response.status_code == 200 and response.json().get('QueryResponse', {}).get('Customer', []):
        return response.json()['QueryResponse']['Customer'][0]['Id']
    # else:
    #     return response.json()
    # Create customer if not found
    customer_data = {
                    "BillAddr": {
                        "Line1": f"{address}",
                        "City": f"{City}",
                        "Country": f"{Country}",
                        "CountrySubDivisionCode": " ",
                        "PostalCode": f"{PostalCode}"
                    },
                    "Notes": "Here are other details.",
                    "DisplayName": f"{name}",
                    "PrimaryPhone": {
                        "FreeFormNumber": f"{phone}"
                    },
                    "PrimaryEmailAddr": {
                        "Address": f"{email}"
                    }
                }
    url = f"{api_base_url}{request.session['realm_id']}/customer"
    response = requests.post(url, headers=headers, json=customer_data)

    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to create customer: {response.text}")
        return None

def create_invoice(customer_id, line_items, session,inv):
    headers = {
        'Authorization': f'Bearer {session["access_token"]}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    invoice_data = {
        "Line": line_items,
        "CustomerRef": {"value": 295},
         "CustomField": [
                        {
                        "DefinitionId": "1",
                        "Name": "orig_inv",
                        "Type": "StringType",
                        "StringValue": f"{inv}"
                        }
                        ]
            }
    
    url = f"{api_base_url}{session['realm_id']}/invoice"
    invoice_data={
                "Line": line_items,
                "CustomerRef": {
                    "value": f"{customer_id}"
                },
                
                }
    
    print(invoice_data)
    response = requests.post(url, headers=headers, json=invoice_data)

    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to create invoice: {response.text}")
        return None
    
def process_csv(file_path, session,request):
    df = pd.read_csv(file_path)
    results = []
    print(df.info())
    for _, row in df.iterrows():
        
        email=row['Email']
        name=row['Customer / Project']
        address=''
        phone='' 
        City='' 
        Country='' 
        PostalCode=''
        print(email,name,'email,name,email,name,email,name')
        customer_id = find_or_create_customer(email,name,address,phone ,City ,Country ,PostalCode,request)
        print(customer_id,'customer_idcustomer_idcustomer_idcustomer_id')
        
        if customer_id:
            line_items = [{
                "DetailType": "SalesItemLineDetail",
                "Amount": row['Amount'],
                "Description": '',
                "SalesItemLineDetail": {
                    "ItemRef": {"value": '26'},
                    "Qty": 1,
                    "UnitPrice": row['Amount']
                }
            }]
            print(line_items,'line_itemsline_itemsline_itemsline_items')
            inv=row['No.']
            invoice_result = create_invoice(customer_id, line_items, session,inv)
            results.append(invoice_result)
        else:
            results.append("Failed to create customer or invoice")
    return results

def upload_csv(request):
    # file = request.files['file']
    sessions = {
    'access_token': request.session['access_token'],
    'realm_id' : request.session['realm_id']
    }
    if not all(request.session.values()):
        return JsonResponse({'error': 'Missing access token or realm ID'}), 400

    file_path = 'c:/Users/MANJEET SINGH/Downloads/sales (6).csv' 
    results = process_csv(file_path, sessions,request)
    return JsonResponse(results)

def line_item(request):
    print('------',request.session["access_token"],'-------')
    headers = {
        'Authorization': f'Bearer {request.session["access_token"]}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    payload = "select * from item startposition 1 maxresults 5"
    url = f"{api_base_url}/{company_id}query?minorversion=65"
    print(url,'urlurlurlurlurlurlurlurl')
    
    response = requests.request("GET", url, headers=headers, data=payload)
    print(response,'responseresponseresponseresponse')
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to create invoice: {response.text}")
        return response.json()

def import_invoices_to_hubspot(invoices,request):
    import hubspot_app
    from pprint import pprint
    from hubspot.crm.deals import BatchInputSimplePublicObjectInputForCreate, ApiException
    from hubspot.crm.deals import SimplePublicObjectInput, ApiException
    hubspot_access_token = request.session.get('hubspot_access_token')
    client = hubspot_app.Client.create(access_token=hubspot_access_token)

    imported_invoices = []
    for invoice in invoices:
        # Define properties for HubSpot based on the invoice data
        properties = {
            "invoice_number": invoice['DocNumber'],
            "customer_name": invoice['CustomerRef']['name'],
            "due_date": invoice['DueDate'],
            "total_amount": invoice['TotalAmt'],
            "status": invoice['Balance'],  # Adjust based on available fields
            # Add more mappings if necessary
        }

        # Create the HubSpot invoice (object API endpoint might differ)
        invoice_input = SimplePublicObjectInput(properties=properties)
        print("________++++++++",invoice_input)
        try:
            api_response = client.crm.objects.basic_api.create(object_type="invoices", simple_public_object_input_for_create=invoice_input)
            print("Invoice created:", api_response)
            imported_invoices.append(invoice['InvoiceNumber'])
        except ApiException as e:
            print(f"Exception when creating invoice in HubSpot: {e}")
        except Exception as e:
            print(f"Error processing invoice {invoice['DocNumber']}: {e}")

    return JsonResponse(imported_invoices) 

def get_invoices(request):
    if 'access_token' not in request.session or is_token_expired(request):
        if not refresh_access_token(request):
            return redirect('/')

    access_token = request.session['access_token']
    realm_id = request.session['realm_id']
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    query = "SELECT * FROM Invoice "
    url = f"{api_base_url}{realm_id}/query?query={urllib.parse.quote(query)}&minorversion=65"

    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        # Unauthorized, try refreshing token
        if refresh_access_token(request):
            access_token = request.session['access_token']
            headers['Authorization'] = f'Bearer {access_token}'
            response = requests.get(url, headers=headers)
            print('got the response ')
        else:
            return redirect('/')

    if response.status_code != 200:
        return f"Error fetching invoices: {response.text}", response.status_code
    print('got the response')
    data = response.json()
    invoices = data.get('QueryResponse', {}).get('Invoice', [])
    with open('invoices.json', 'w') as json_file:
        json.dump(invoices, json_file, indent=4)
    return JsonResponse({'invoices': invoices})

def import_invoices(request):
    invoices = get_invoices(request).get_json()['invoices']
    print("ggggggggggg",invoices)
    result = import_invoices_to_hubspot(invoices,request)
    return result

def import_items_to_hubspot(items):
    import hubspot_app
    from pprint import pprint
    from hubspot.crm.products import SimplePublicObjectInputForCreate, ApiException
    hubspot_access_token = session.get('hubspot_access_token')
    client = hubspot_app.Client.create(access_token=hubspot_access_token)

    item_data = []
    for item in items:
        print("Item data:", item)
        
        # Define properties for HubSpot based on the invoice data
        properties = {
            "name": item['Name'],
            # "description": item.get('Description', ''),
            "price": item['UnitPrice'] * 100,  
            # "type": item.get('Type', ''),  
            # "quantity_on_hand": item.get('TrackQtyOnHand', 0),
            # "domain": item.get('domain', False),
            "sku": "4522222222"      

        }
        simple_public_object_input_for_create = SimplePublicObjectInputForCreate( properties=properties )

        # Create the HubSpot invoice (object API endpoint might differ)
        # item_input = SimplePublicObjectInput(properties=properties)
        # print("________++++++++",item_input)
        try:
            api_response = client.crm.products.basic_api.create(simple_public_object_input_for_create=simple_public_object_input_for_create)

            # api_response = client.crm.products.batch_api.archive(batch_input_simple_public_object_input_for_create=item_input)
            print("ite created:", api_response)
            # item_data.append(api_response)

        except ApiException as e:
            print(f"Exception when creating item in HubSpot: {e}")

def get_item_info(request):
    print(request.session['access_token'])
    if 'access_token' not in request.session or is_token_expired(request):
        if not refresh_access_token(request):
            return redirect('/')

    access_token = request.session['access_token']
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'

    }
    query = "SELECT * FROM Item"
    url = f"{api_base_url}{request.session['realm_id']}/query?query={urllib.parse.quote(query)}&minorversion=65"

    all_items = []
    while url:
        response = requests.get(url, headers=headers)
        print(response.status_code, 'response status')
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('QueryResponse', {}).get('Item', [])
            all_items.extend(items)
            url = data.get('QueryResponse', {}).get('nextPage', None)
            if url:
                url = f"{api_base_url}{request.session['realm_id']}{url}"
            else:
                break
        else:
            logging.error(f"Failed to fetch items: {response.text}")
            return JsonResponse({"error": "Failed to fetch items from QuickBooks"}), response.status_code
    
    return all_items

def import_item(request):
    item_info = get_item_info(request)
    print("ggggggggggg",item_info)
    if isinstance(item_info, dict) and 'error' in item_info:
        return JsonResponse(item_info), 400 
    result = import_items_to_hubspot(item_info)
    return JsonResponse(result)

def get_company_info(request):
    print(request.session['access_token'])
    if 'access_token' not in request.session or is_token_expired(request):
        if not refresh_access_token(request):
            return redirect('/')

    access_token = request.session['access_token']
    realm_id = request.session['realm_id']
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    url = f"{api_base_url}{realm_id}/companyinfo/{realm_id}?minorversion=65"

    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        # Unauthorized, try refreshing token
        if refresh_access_token(request):
            access_token = request.session['access_token']
            headers['Authorization'] = f'Bearer {access_token}'
            response = requests.get(url, headers=headers)
        else:
            return redirect('/')

    if response.status_code != 200:
        return f"Error fetching company info: {response.text}", response.status_code

    data = response.json()
    company_info = data.get('CompanyInfo', {})
    create_company_in_hubspot(company_info,request)
    print("company_info",company_info)
    return JsonResponse(company_info)

def create_company_in_hubspot(company_info,request):
    import hubspot_app
    from pprint import pprint
    from hubspot.crm.companies import SimplePublicObjectInputForCreate, ApiException

    hubspot_access_token = request.session.get('hubspot_access_token')
    client = hubspot_app.Client.create(access_token=hubspot_access_token)

    
    properties = {
        "name": company_info.get("CompanyName"),
        "domain": company_info.get("domain"),
        "country": company_info.get("Country"),
        "city": company_info.get("CompanyAddr", {}).get("City"),
        "address": company_info.get("CompanyAddr", {}).get("Line1"),
        # "postal_code": company_info.get("CompanyAddr", {}).get("PostalCode"),
        "state": company_info.get("CompanyAddr", {}).get("CountrySubDivisionCode"),
        # "email": company_info.get("Email", {}).get("Address"),
        "phone": company_info.get("PrimaryPhone", {}).get("FreeFormNumber"),
        # "website": company_info.get("WebAddr", {}).get("URI"),
        # "fiscal_year_start_month": company_info.get("FiscalYearStartMonth"),
        # "legal_name": company_info.get("LegalName"),
        # "legal_address": company_info.get("LegalAddr", {}).get("Line1"),
        # "customer_email": company_info.get("CustomerCommunicationEmailAddr", {}).get("Address"),
        # Add more mappings as needed
    }

    properties = {k: v for k, v in properties.items() if v is not None}

    simple_public_object_input_for_create = SimplePublicObjectInputForCreate(properties=properties)
    try:
        api_response = client.crm.companies.basic_api.create(simple_public_object_input_for_create=simple_public_object_input_for_create)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling HubSpot API: %s\n" % e)