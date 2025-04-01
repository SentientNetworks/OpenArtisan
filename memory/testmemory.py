import sys, os
import threading
import queue
import requests
import json
import time
import uuid

MEMORY_SERVER_URL = "http://127.0.0.1:5003/process_messages"
CLIENT_ID = str(uuid.uuid4())

# API processing function 
def api_process(payload, server_url):

    try:
        beforeTime = time.time()

        print(f"1. testmemory::api_process: server_url is {server_url} and payload is {payload}")

        response = requests.post(server_url, json=payload)
        afterTime = time.time()
        elapsedTime = afterTime - beforeTime

        print(f"13. testmemory::api_process: the response is {response.text} with status code {response.status_code}")

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
    
def makeMessage(username, sender, receiver, commands, direction, content, client_id):

    dMessage = {}

    dMessage["source"] = sender
    dMessage["target"] = receiver
    dMessage["type"] = "in"
    dMessage["direction"] = direction
    dMessage["content"] = content
    dMessage["client_id"] = str(client_id)
    dMessage["broadcast"] = False

    try:

        dCommands = json.loads(commands)

        if type(dCommands) is dict:

            for key, value in dCommands.items():
                dMessage[key] = value

    except Exception as e:

        print(f"ClientServer::makeMessage: error reading json string: {e}")   

    return json.dumps(dMessage)

def makeConfigMessage(username, sender, receiver, commands, direction, content, client_id):

    message_str = makeMessage(username, sender, receiver, commands, direction, content, client_id)
    dMessage = json.loads(message_str)

    dMessage["type"] = "config"
    dMessage["client_id"] = str(client_id)

    try:

        dCommands = json.loads(commands)

        if type(dCommands) is dict:

            for key, value in dCommands.items():
                dMessage[key] = value

    except Exception as e:

        print(f"ClientServer::makeMessage: error reading json string: {e}")   

    return json.dumps(dMessage)

def assembleContent(objectType, objectName, operation):

    contentTemplate = '''
    {      
        "databases" : {
            "name" : "artisan".
            "operation": {
                "drop" : {},
                "alter" : {}.
            }            
        }, 
        "collections" : {
            "name" : "". 
            "operation": {
                "insert" : {},
                "delete" : {}.
            }            
        } 
                    
    }
    '''

    try :
        dContent = json.loads(contentTemplate)

        if objectType == "databases":
            del dContent["collections"]
            dContent["databases"]["name"] = objectName
            dContent["databases"]["operation"] = operation
        elif objectType == "collections":
            del dContent["databases"]
            dContent["collections"]["name"] = objectName
            dContent["collections"]["operation"] = operation

        content = json.dumps(dContent)

    except Exception as e:

        print(f"testmemory: exception while performing json commands: {e}")
        content = "{}"
    
    return content

if __name__ == '__main__':

    if len(sys.argv) > 1:
        content = sys.argv[1]
    else:
        content = assembleContent()

    message_str = makeConfigMessage("tester", "client", "memory", "{}", "request", content, CLIENT_ID)

    payload = {
        "messages": [message_str],
        "handler_name": "client"
    }

    print(f"0. testmemory::main: before api call with payload = {payload}")

    responses, elapsedTime = api_process(payload, MEMORY_SERVER_URL)

    print(f"14. testmemory::main: after api call with responses = {responses}")

    d = json.loads(responses)

    for response in d["processed_response"]:
        print(f"The next response is {response}")