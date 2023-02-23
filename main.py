# File for all APIs

# import libraries
from waitress import serve
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from driver import *
from configparser_crypt import ConfigParserCrypt
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required, JWTManager, set_access_cookies 
import json
#import sys

logging.basicConfig(filename='app.log', level=logging.DEBUG)
app = Flask(__name__)
CORS(app,supports_credentials=True)

headers = {'Content-Type': 'application/json; charset=utf-8', 'Strict-Transport-Security':'max-age=31536000; includeSubDomains'}
requestHeaders = ['Content-Type','Authorization','Token']

# decrypt config file
file = './db_config.ini'
conf_file = ConfigParserCrypt()
# Set AES key
with open('./filekey.key', 'rb') as filekey:
    aes_key = filekey.read()
conf_file.aes_key = aes_key
# Read encrypted config file
conf_file.read_encrypted(file)

# app configurations
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_SECRET_KEY"] = conf_file['db_access']["JWT_SECRET_KEY"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["SESSION_COOKIE_HTTPONLY"] = False
app.config["JWT_COOKIE_SECURE"] = False

jwt = JWTManager(app)

@app.after_request
def middleware_for_response(response):
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    # response.headers.add('Access-Control-Expose-Headers', 'true')
    return response

# login API
@app.route('/userlogin', methods=["POST"])
@cross_origin(origin='localhost',headers=requestHeaders)
def jwt_gen():

    # check if the request method is POST
    if request.method == "POST":

        # read the request body
        request_body = request.json

        # call function to check if user present in DB  
        result, msg = UserLogin(request_body)
        response = jsonify({"message": "User Logged-in Successfully.", "role": msg})
        
        # if true, generate JWT using user ID and set it in cookie
        if result == True:
            jwt_token = create_access_token(identity=request_body['User'])
            set_access_cookies(response, jwt_token)
            return response
        else:
            return jsonify({"message": msg})


# 'after_request' will run after each request to protected API to check if token is expiring within 30 min
# then it generates refresh token, if required
@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        target_timestamp = datetime.timestamp(datetime.now() + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    # if there is no valid JWT, return the original response
    except (RuntimeError, KeyError):
        return response


# API to add new words from temp dictionary to main table (accept button)
@app.route('/addwords', methods=["POST"])
@cross_origin(origin='localhost',headers=requestHeaders)
# jwt_required() will authorize for given JWT
@jwt_required()
def addwords():

    # check if the request method is POST
    if request.method == "POST":
        
        # read the request body
        request_body = request.json
        
        # call function to update dictionary 
        newdict = add_word(request_body)
        
        if newdict:
            return {"status": True, "message": "Word(s) added to the dictionary."}
        else:
            return {"status": False, "message": "Word(s) can not be added to the dictionary."}


# API to remove words from temp dictionary (reject button)
@app.route('/rejectwords', methods=["POST"])
@cross_origin(origin='localhost',headers=requestHeaders)
# jwt_required() will authorize for given JWT
@jwt_required()
def rejectwords():

    # check if the request method is POST
    if request.method == "POST":
        
        # read the request body
        request_body = request.json
        
        # call function to remove words dictionary 
        updateddict = reject_word(request_body)
        
        if updateddict:
            return {"status": True, "message": "Word(s) removed from the dictionary."}
        else:
            return {"status": False, "message": "Word(s) can not be removed from the dictionary."}


# API to add words in temporary dictionary 
@app.route('/updatedict', methods=["POST"])
@cross_origin(origin='localhost',headers=requestHeaders)
# jwt_required() will authorize for given JWT
@jwt_required()
def updatedict():

    # check if the request method is POST
    if request.method == "POST":
        
        # read the request body
        request_body = request.json
        
        # call function to update dictionary 
        dict_update = update_dictionary(request_body)
        
        if dict_update:
            return {"status": True, "message": "Request sent to update dictionary."}
        else:
            return {"status": False, "message": "Request can not be sent."}
 

# API to display temporary table
@app.route('/temptable', methods=["GET"])
@cross_origin(origin='localhost',headers=requestHeaders)
# jwt_required() will authorize for given JWT
@jwt_required()
def modifytable():

    # check if the request method is GET
    if request.method == "GET":

        # call function to display temporary table 
        table_display = get_temp()
    return {"status": True, "data": table_display}

 
# API to get all dictioanries
@app.route('/viewdict', methods=["GET"])
@cross_origin(origin='localhost',headers=requestHeaders)
# jwt_required() will authorize for given JWT
@jwt_required()
def viewdict():

    # check if the request method is GET
    if request.method == "GET":

        # call function to display dictionary 
        dict_display = get_dictionary()
        
    return {"status": True, "data": dict_display}


# API function to get summary table
@app.route('/summary', methods=["POST"], strict_slashes=False)
@cross_origin(origin='localhost',headers=requestHeaders)
# jwt_required() will authorize for given JWT
@jwt_required()
def summary(): 
       
    if request.method == "POST":
        # read the request body
        request_body = request.json
        
        try:
            if request_body != {}:
                data = request_body['data']
                return jsonify({"output": prepareData(data)})
            
            else:
                return jsonify({"message": "Data is not provided or not in required format (string)"})
            
        except Exception as e:
            #exc_type, exc_obj, exc_tb = sys.exc_info()
            return jsonify({"message": f"Internal error: {str(e)}"})
    
if __name__ == "__main__":
    # app.run(host="127.0.0.1", port=2000,debug=True)
    serve(app, host="127.0.0.1", port=2000)