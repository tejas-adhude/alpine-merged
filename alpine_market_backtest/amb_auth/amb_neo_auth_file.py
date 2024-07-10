import requests
import json

import alpine_market_backtest.amb_auth.amb_cred as amb_cred

# Credentials
neo_client_id = amb_cred.neo_client_id
neo_username = amb_cred.neo_username
neo_password = amb_cred.neo_password
neo_mobile_number = amb_cred.neo_mobile_number
neo_mobile_password = amb_cred.neo_mobile_password
neo_user_id = amb_cred.neo_user_id

# Function to handle the authentication process
def authenticate(client_id, username, password, mobile_number, mobile_password, user_id):
    # Step 1: Obtain Access Token
    access_data = {
        'grant_type': 'password',
        'username': username,
        'password': password
    }
    access_response = requests.post('https://napi.kotaksecurities.com/oauth2/token',
                                    headers={'Authorization': f'Basic {client_id}'},
                                    data=access_data)
    access_response_data = access_response.json()
    accAuth = access_response_data['access_token']
    
    # Step 2: Obtain View Token
    view_data = {
        "mobileNumber": mobile_number,
        "password": mobile_password
    }
    view_response = requests.post('https://gw-napi.kotaksecurities.com/login/1.0/login/v2/validate',
                                  headers={'Authorization': 'Bearer ' + accAuth, 'Content-Type': 'application/json'},
                                  json=view_data)
    view_response_data = view_response.json()
    # print(view_response_data)
    viewAuth = view_response_data['data']['token']
    sid = view_response_data['data']['sid']
    rid = view_response_data['data']['rid']
    hsServerId = view_response_data['data']['hsServerId']
    
    # Step 3: Generate OTP
    otp_data = {
        "userId": user_id,
        "sendEmail": True,
        "isWhitelisted": True
    }
    otp_response = requests.post('https://gw-napi.kotaksecurities.com/login/1.0/login/otp/generate',
                                 headers={'Authorization': 'Bearer ' + accAuth, 'Content-Type': 'application/json'},
                                 json=otp_data)
    print("**OTP Generated**")
    
    # Step 4: Input OTP
    otpnn = input("Enter OTP: ")
    if len(otpnn) != 4:
        raise ValueError("Invalid OTP length")
    
    # Step 5: Validate Session
    sess_data = {
        "userId": user_id,
        "otp": otpnn
    }
    sess_response = requests.post('https://gw-napi.kotaksecurities.com/login/1.0/login/v2/validate',
                                   headers={'Authorization': 'Bearer ' + accAuth, 'sid': sid, 'Auth': viewAuth, 'Content-Type': 'application/json'},
                                   json=sess_data)
    sess_response_data = sess_response.json()
    sessAuth = sess_response_data['data']['token']
    
    # Step 6: Write tokens to JSON file
    token_obj = {
        "userID":user_id,
        "password":mobile_password,
        "mobileNumber":mobile_number,
        "consumerKey":None,
        "consumerSecret":None,
        "accessToken": accAuth,
        "enctoken":None,
        "viewAuth": viewAuth,
        "sessAuth": sessAuth,
        "sid": sid,
        "rid": rid,
        "hsServerId": hsServerId
    }
    with open("./amb_auth/amb_neo_token_obj.json", "w") as outfile:
        json.dump(token_obj, outfile)
    print("Tokens saved to amb_neo_token_obj.json")

# Call the function to start the authentication process
authenticate(neo_client_id, neo_username, neo_password, neo_mobile_number, neo_mobile_password, neo_user_id)
