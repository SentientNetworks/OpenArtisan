import sys, os
import threading
import queue
import requests
import json
import time

MESSAGE_SERVER_URL = "http://127.0.0.1:5002/process_messages"

# API processing function 
def api_process(payload, server_url):

    try:
        beforeTime = time.time()

        print(f"1. testmessaging::api_process: server_url is {server_url} and payload is {payload}")

        response = requests.post(server_url, json=payload)
        afterTime = time.time()
        elapsedTime = afterTime - beforeTime

        print(f"13. testmessaging::api_process: the response is {response.text} with status code {response.status_code}")

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
        content = "Hi this is a test"

    message_str = json.dumps({"source": "Andrew", "target": "room", "type": "in", "direction": "request", "content": f"{content}"})

    payload = {
        "messages": [message_str],
        "handler_name": "client"
    }

    print(f"0. testmessaging::main: before api call with payload = {payload}")

    responses, elapsedTime = api_process(payload, MESSAGE_SERVER_URL)

    print(f"14. testmessaging::main: after api call with responses = {responses}")

    d = json.loads(responses)

    for response in d["processed_response"]:
        print(f"The next response is {response}")