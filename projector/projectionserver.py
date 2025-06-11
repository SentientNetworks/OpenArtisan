'''
This is the server entry point for Sentiet Artisan projection handling
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

    print(f"2. projectionserver::process_messages: data is {data}")

    messages = data["messages"]

    print(f"projectionserver::process_messages: messages are {messages}")

    if 'messages' not in data:
        return jsonify({"error": "No messages provided"}), 400

    if not isinstance(messages, list):
        return jsonify({"error": "Messages should be a list"}), 400
    
    print(f"projectionserver::process_messages: messages are {messages}")

    responses = []

    for message in messages:

        # do something with each message

        result, errormessage = businesslogic.isJSON(message) 
        if result:

            print(f"projectionserver::process_messages: type of message {message} is {type(message)}")
            result, errormessage = businesslogic.isCorrectStructure(message)
            if result:                
                print(f"projectionserver::process_messages: correct structure")

            else:
                # if the message is not in the correct structure then let the message pass through the 
                # projections module
                message = errormessage

                print(f"projectionserver::process_messages: invalid structure")

        else:
            # if the message is not in JSON then let the message pass through the 
            # projections module
            message = errormessage

            print(f"projectionserver::process_messages: invalid json")

        response = businesslogic.process_and_address(message)
        responses.append(response)

    print(f"12. projectionserver::process_messages: the responses are {responses}")

    # return jsonify({"processed_response": responses}), 200

    return {"processed_messages": responses}, 200

    return

if __name__ == '__main__':

    app.run(debug=True, port=5004)



    
