'''
This is the server entry point for Sentiet Artisan function handling
'''

import sys, os
import threading
import queue
import requests
import json
import time
from flask import Flask, render_template, request, jsonify
from Configurator import CConfigurator
from BusinessLogic import CBusinessLogic

configurator = CConfigurator()
businesslogic = CBusinessLogic(configurator)

TIME_TO_JOIN = 20

app = Flask(__name__)

@app.route('/process_messages', methods=['POST'])
def process_messages():

    data = request.json

    print(f"2. functionserver::process_messages: data is {data}")

    messages = data["messages"]

    print(f"functionserver::process_messages: messages are {messages}")

    if 'messages' not in data:
        return jsonify({"error": "No messages provided"}), 400

    if not isinstance(messages, list):
        return jsonify({"error": "Messages should be a list"}), 400
    
    print(f"functionserver::process_messages: messages are {messages}")

    responses = []

    for message in messages:

        # do something with each message

        passthrough = True

        result, errormessage = businesslogic.isJSON(message) 
        if result:

            print(f"functionserver::process_messages: type of message {message} is {type(message)}")
            result, errormessage = businesslogic.isCorrectStructure(message)
            if result:                
                # process this as a valid message for functions

                functiondetails = businesslogic.findFunctions(message)
                # findFunctions does all the work to locate and setup the functions

                if functiondetails is not None:
                    # do a run
                    message = businesslogic.runFunctions(message, functiondetails)

                    passthrough = False

            else:
                # if the message is not in the correct structure then let the message pass through the 
                # functions module
                message = errormessage
                passthrough = True
        else:
            # if the message is not in JSON then let the message pass through the 
            # functions module
            message = errormessage
            passthrough = True

        response = businesslogic.process_and_address(message, passthrough=passthrough)
        responses.append(response)

    print(f"12. functionserver::process_messages: the responses are {responses}")

    # return jsonify({"processed_response": responses}), 200

    return {"processed_messages": responses}, 200

    return

if __name__ == '__main__':

    app.run(debug=True, port=5004)



    
