'''
This is the server entry point for the Sentiet Artisan memory server
The process_messages function needs to be refactored!
'''

import sys, os
import threading
import queue
import requests
import json
import time
from flask import Flask, render_template, request, jsonify
from Configurator import CConfigurator
from MemoryStore import CMemoryStore
import copy

TIME_TO_JOIN = 20

app = Flask(__name__)


config = CConfigurator()
store = CMemoryStore(config)


def process_and_address(message):

    try:

        dMessage = json.loads(message)

        if dMessage["type"] != "storage":
            dMessage["type"] = "out"
            dMessage["direction"] = "response"

        if "system" in dMessage and type(dMessage["system"]) is dict:

            currentSource = int(dMessage["system"]["sourcetargets"]["start"])
            currentTarget = int(dMessage["system"]["sourcetargets"]["end"])
            maxTarget = len(dMessage["system"]["chain"]) - 1

            if currentTarget < maxTarget:

                dMessage["system"]["sourcetargets"]["start"] = currentSource + 1
                dMessage["system"]["sourcetargets"]["end"] = currentTarget + 1

            else:
                
                dMessage["system"]["sourcetargets"]["start"] = currentTarget
                maxSource = dMessage["system"]["sourcetargets"]["start"]
                print(f"Changing currentSource to maxTarget = {maxSource}")

        outMessage = json.dumps(dMessage)

    except Exception as e:

        print(f"memory: change_and_address: json error: {e} for string {outMessage}")

        outMessage = ""

    return outMessage

def isConfig(message):

    try:

        dMessage = json.loads(message)

        if "type" in dMessage:
            if dMessage["type"] == "config":
                return True
    
    except Exception as e:

        print(f"memoryserver::isConfig: problem with json {e}")
        
    return False

def isStorage(message):

    try:

        dMessage = json.loads(message)

        if "type" in dMessage:
            if dMessage["type"] == "storage":
                return True
    
    except Exception as e:

        print(f"memoryserver::isStorage: problem with json {e}")
        
    return False

@app.route('/process_messages', methods=['POST'])
def process_messages():

    data = request.json

    print(f"2. memoryserver::process_messages: data is {data}")

    if 'messages' not in data:
        return jsonify({"error": "No messages provided"}), 400

    messages = data["messages"]

    if not isinstance(messages, list):
        return jsonify({"error": "Messages should be a list"}), 400

    print(f"memoryserver::process_messages: messages are {messages}")
    
    responses = []

    for message in messages:

        # do something with each message
        dMessage = json.loads(message)
        systemblock = dMessage["system"]

        currentModuleIndex = int(systemblock["sourcetargets"]["end"])
        moduleName = systemblock["chain"][currentModuleIndex]
        moduleMethod = systemblock["method"][currentModuleIndex]

        if moduleName != "memory":
            print(f"memoryserver::process_messages: the module name is not memory so the responses are empty.")
            return {"processed_messages": []}, 200

        if isConfig(message):

            # do config stuff

            fullconfig = config.update(dMessage, moduleMethod)
            if fullconfig is None:
                print(f"memoryserver::process_messages: failed to config the configurator!")
                break

            print(f"memoryserver::process_messages: configurator is now {fullconfig}")

            # what do we want to do when database storage fails?

            if moduleMethod == "put" or moduleMethod == "none":
                
                if not store.store("messages", message):
                    break

            elif moduleMethod == "get":

                content = dMessage["content"]
                dContent = json.loads(content)
                
                print(f"memoryserver::process_messages: get method content = {dContent}")

                if len(dContent) > 0 and type(dContent) is not dict:
                    break

                print(f"memoryserver::process_messages: before store.get content = {dContent}")
                results = store.get("artisan", "messages", matching=dContent)
                if results is None:
                    print(f"memoryserver::process_messages: no valid results from store.get content = {dContent}")
                    break

                result_strs = []
                for result in results:
                    result_strs.append(str(result))

                print(f"memoryserver::process_messages: results = {result_strs}")
                dStagingMessage = copy.deepcopy(dMessage)
                dStagingMessage["content"] = {"results": result_strs}

                message = json.dumps(dStagingMessage)

        elif isStorage(message):

            # do other storage stuff

            if moduleMethod == "put" or moduleMethod == "none":
                print(f"memoryserver::process_messages: put method")
                if not store.store("messages", message):
                    
                    # what do we want to do when database storage fails?
                    #continue
                    print(f"memoryserver::process_messages: store.store failed for message = {message}")
                    break
            
        elif moduleMethod == "get":

            content = dMessage["content"]
            dContent = json.loads(content)

            print(f"memoryserver::process_messages: get method content = {dContent}")
            
            if len(dContent) > 0 and type(dContent) is not dict:
                break

            print(f"memoryserver::process_messages: before store.get content = {dContent}")
            results = store.get("artisan", "messages", matching=dContent)
            if results is None:
                print(f"memoryserver::process_messages: no valid results from store.get content = {dContent}")
                break
            
            result_strs = []
            for result in results:
                result_strs.append(str(result))

            print(f"memoryserver::process_messages: results = {result_strs}")
            dStagingMessage = copy.deepcopy(dMessage)
            dStagingMessage["content"] = {"results": result_strs}

            message = json.dumps(dStagingMessage)

        response = process_and_address(message)
        responses.append(response)
        print(f"memoryserver::process_messages: about to set up responses {responses}")

    print(f"12. memoryserver::process_messages: the responses are {responses}")

    # return jsonify({"processed_response": responses}), 200

    return {"processed_messages": responses}, 200

    return

if __name__ == '__main__':

    app.run(debug=True, port=5003)



    
