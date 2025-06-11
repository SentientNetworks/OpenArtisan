'''
This module contains the function inject_message which tests using the Flask exposed API to 
inject a message into the client
'''

import sys, os
import threading
import queue
import requests
import json
import time


CLIENT_SERVER_URL = "http://127.0.0.1:5000/inject"

# API processing function 
def inject_message(message):

    try:

        payload = {"message": message, "user": "Andrew"}

        beforeTime = time.time()
        response = requests.post(CLIENT_SERVER_URL, json=payload)
        afterTime = time.time()
        elapsedTime = afterTime - beforeTime

        print(response.text)

        # Check if the request was successful
        if response.status_code == 200:
    
            print(f"Elapsed time is {elapsedTime} seconds")
            print()

            return json.dumps(response.json()), elapsedTime
        
        else:

            print(f"Error: Received status code {response.status_code}")
            print(f"Response: {response.text}")

            return None, 0
        
    except requests.exceptions.RequestException as e:

        print(f"Request failed: {e}")
        return None, 0
    
if __name__ == '__main__':

    message = ""
    if len(sys.argv) > 1:
        message = sys.argv[1]

    response, responseTime = inject_message(message)

    print(response)

