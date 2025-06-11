'''
This module contains the function handle which handles the connection to the Message Server used to
connect a Client server (client or timer) to the server systems such as the Engine, the Agent Server and the Function server
for the Sentiet system.
'''

import sys, os
import threading
import queue
import requests
import json
import time
import certifi

from logger import _print

MESSAGE_SERVER_URL = "http://127.0.0.1:5002/process_messages"
#MESSAGE_SERVER_URL = "https://sentiet.ai/process_messages"

# API processing function 
def api_process(payload):

    try:
        beforeTime = time.time()
        
        # TODO: we need to set the client up with authorization 
        # to properly use https
        #response = requests.post(MESSAGE_SERVER_URL, json=payload, verify=certifi.where())
        
        response = requests.post(MESSAGE_SERVER_URL, json=payload, verify=False)

        afterTime = time.time()
        elapsedTime = afterTime - beforeTime

        # Check if the request was successful
        if response.status_code == 200:
    
            _print(f"Elapsed time is {elapsedTime} seconds")
            _print("")

            return json.dumps(response.json()), elapsedTime
        
        else:

            _print(f"Error: Received status code {response.status_code}")
            _print(f"Response: {response.text}")

            return None, 0
        
    except requests.exceptions.RequestException as e:

        _print(f"Request failed: {e}")
        return None, 0
    
# The entry point method for accessing the messageserver
def handle(messages, handler_name="client"):
    '''
    This method wraps an array of messages into a payload
    then calls an API for the MESSAGE_SERVER with an endpoint
    with the name process_messages
    '''

    try:

        _print("MessageHandler::process_messages: at beginning")
    
        # Prepare the payload
        in_payload = {
            "messages": messages,
            "handler_name": handler_name
        }

        _print(f"MessageHandler::process_messages: payload is {in_payload}")
    
        # Process the message with the API
        # we need to send a special key-value pair through to the MS
        # This should be in all the messages including the first one.
        # If there are no messages send a special one with just the key-value pair.
        # This pair identifies the client instance.
        
        response_message_str, streamTime = api_process(in_payload)

        # We need the system to cope with an api_process failure 
        # In this case an error message should be printed and
        # an empty list returned.
    
        _print(f"MessageHandler::process_messages: response string is {response_message_str}")

        # Put the response message into the output queue
        if response_message_str is not None:

            d = json.loads(response_message_str)

            augmented_responses = []

            responses = d["processed_messages"]
            for response in responses:
                
                dr = json.loads(response)
                dr['stream_time'] = streamTime
                augmented_response = json.dumps(dr)
                augmented_responses.append(augmented_response)
                _print(f"MessageHandler::process_messages: augmented_response is {augmented_response}")
                
            return augmented_responses
        else:
            return ""

    except Exception as e:
        _print(f"MessageHandler::process_messages: error: {e}")
            

