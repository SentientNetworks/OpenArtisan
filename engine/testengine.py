import sys, os
import threading
import queue
import requests
import json
import time

ENGINE_SERVER_URL = "http://127.0.0.1:5001/process"

# API processing function 
def api_process(payload, server_url):

    try:
        beforeTime = time.time()

        print(f"1. testengine::api_process: server_url is {server_url} and payload is {payload}")

        response = requests.post(server_url, json=payload)
        afterTime = time.time()
        elapsedTime = afterTime - beforeTime

        print(f"13. testengine::api_process: the response is {response.text} with status code {response.status_code}")

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

    if len(sys.argv) > 1:
        content = sys.argv[1]
    else:
        content = "Hi This is a test"

    message_str = json.dumps({"source": "Andrew", "target": "room", "type": "in", "direction": "request", "content": f"{content}"})

    payload = {
        "messages": [message_str]
    }

    print(f"0. testengine::main: before api call with payload = {payload}")

    responses = api_process(payload, ENGINE_SERVER_URL)

    print(f"14. testengine::main: before api call with responses = {responses}")

    for response in responses:
        print(f"The next response is {response}")