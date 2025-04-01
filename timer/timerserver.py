'''
This is the server entry point for Sentiet Artisan timer handling
'''

import sys, os
import threading
import queue
import requests
import json
import time
import uuid
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask import copy_current_request_context

from MessageHandler import handle

TIME_TO_JOIN = 20

app = Flask(__name__)

queuehandler = None
CLIENT_ID = uuid.uuid4()
input_queue = queue.Queue()

current_timestamp = time.time()

def getCurrentTime():

    # Get the current time
    current_time = datetime.now()

    # Format the time to include seconds
    time_with_seconds = current_time.strftime("%H:%M:%S")

    return str(time_with_seconds)

def getCurrentTimestamp():

    # Get the current time
    current_time = time.time()

    # Format the time to include seconds

    return str(current_time)

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

        print(f"timerserver: change_and_address: json error: {e} for string {outMessage}")

        outMessage = ""

    return outMessage

def makeMessage(username, sender, receiver, commands, direction, agentprompt, content, client_id):

    dMessage = {}

    dMessage["source"] = sender
    dMessage["target"] = receiver
    dMessage["type"] = "in"
    dMessage["direction"] = direction
    dMessage["agentprompt"] = agentprompt
    dMessage["content"] = content
    dMessage["client_id"] = str(client_id)
    dMessage["broadcast"] = True
    dMessage["timestamp"] = getCurrentTimestamp()

    try:

        dCommands = json.loads(commands)

        if type(dCommands) is dict:

            for key, value in dCommands.items():
                dMessage[key] = value

    except Exception as e:

        print(f"timerServer::makeMessage: error reading json string: {e}")   

    return json.dumps(dMessage)

@app.route('/process_messages', methods=['POST'])
def process_messages():

    data = request.json

    print(f"2. timerserver::process_messages: data is {data}")

    messages = data["messages"]

    print(f"timerserver::process_messages: messages are {messages}")

    if 'messages' not in data:
        return jsonify({"error": "No messages provided"}), 400

    if not isinstance(messages, list):
        return jsonify({"error": "Messages should be a list"}), 400
    
    print(f"timerserver::process_messages: messages are {messages}")

    responses = []

    for message in messages:

        # do something with each message

        response = process_and_address(message)
        responses.append(response)

    print(f"12. timerserver::process_messages: the responses are {responses}")

    # return jsonify({"processed_response": responses}), 200

    return {"processed_messages": responses}, 200

    return


#@copy_current_request_context
def threadloop(stop_event, interval):

    while not stop_event.is_set():
            
            print("timerserver::threadloop: at beginning")

            try:

                time.sleep(interval)

                # To enable asynchronicity we want to create a thread loop that contains the remainder of this segment
                # we will need to push message/s into an input queue
                # First we generate an identifier tag for the client instance
                # We insert this into each message if there are no messages we create a message with just the tag.

                # We will create the thread loop function in this module.
                # We will rename process_messages to handle to be inline with the Message Server handlers
                # We call the thread loop function process_messages. The function shouldf begin with a delay or sleep.

                # We rename the process_messages method to handle. We then wrap everything from what is next until the second emit
                # in a thread loop function thread_loop. This first does a queue get_nowait to obtain messages for output
                # if any exist. These are sent into the handle method. THe responses are then thrown away or emitted.

                message_str = ""
                if input_queue.qsize() > 0:
                    print("timerserver::threadloop: input queue not empty")
                    
                    # something has to push a message into the input queue
                    message_str = input_queue.get_nowait()
                #else:
                #    d = {}
                #    d["client_id"] = str(CLIENT_ID)
                #
                #    message_str = json.dumps(d)

                if len(message_str) == 0:
                    continue

                print(f"timerserver::threadloop: message_str = {message_str}")

                messages = [message_str]

                responses = []
                responses = handle(messages, handler_name="timer")

                for response in responses:

                    d = json.loads(response)
                    username = d["source"]
                    if "direction" not in d.keys():
                        d["direction"] = "response"
                    direction = d["direction"]
                    content = d["content"]
                    message = d

                    print("timerserver::threadloop: Response: " + str(d))
                
                    # push onto the output queue if appropriate                  

            except Exception as e:

                print(f"timerserver::threadloop: Serious error: {str(e)}")
                break

    return None     

def handleTimer(templates, name, client_id):

    messages = []

    username = "system"
    sender = templates[name]["source"]
    receiver = templates[name]["target"]
    sender = templates[name]["source"]
    commands = templates[name]["commands"]
    agentprompt = templates[name]["agentprompt"]
    content = templates[name]["content"]
    
    messages.append(makeMessage(username, sender, receiver, commands, "request", agentprompt, content, client_id))    

    #if len(messages) == 0:

    #    d = {}
    #    d["client_id"] = str(client_id)
    #    
    #    message_str = json.dumps(d)
    #
    #    messages.append(message_str)

    #    print(f"timerserver::handle_message adding special message: {message_str}")    

    for message_str in messages:
        print(f"timerserver::handle_message putting message on input queue: {message_str}")
        input_queue.put(message_str)

    return

message_templates = {}
message_templates["first"] = {}
message_templates["first"]["source"] = "timer"
message_templates["first"]["target"] = "AI"
message_templates["first"]["commands"] = json.dumps({"system": {"chain": ["timer", "AI", "client"], "method": ["start", "prompt", "none"], "sourcetargets": {"start": 0, "end": 1}}})
message_templates["first"]["agentprompt"] = ""
#message_templates["first"]["content"] = "Write a response about anything you want to talk about that has occurred during this whole session with anybody. Only respond if you want to." 
message_templates["first"]["content"] = "Write a response in detail about anything you want to talk about. Do NOT talk if you have nothing to say. Do NOT reference timer by name." 

def main() :
    
    while True:

        time.sleep(300.0)

        try:

            handleTimer(message_templates, "first", CLIENT_ID)

            template = ""

            print(f"timerserver::main: handled messages: {template} for {CLIENT_ID}")

            

        except Exception as e:
            print(f"timerserver::main: encountered error {e}")
            break

    return



if __name__ == '__main__':

    # Start the queue handler thread
    stop_event = threading.Event()
    clientthread = threading.Thread(target=threadloop, args=(stop_event, 12.0, ))
    clientthread.daemon = True  # Daemonize thread to ensure it exits when main program exits
    clientthread.start()  

    # we need to decide how to run main
    # if main runs on the main thread and if main comes before app.run
    # then app.run will never be called
    # and if app.run comes first then main will never be called
    # alternatively main can be call on another thread
    
    main()     

    app.run(debug=True, port=5005)



    
