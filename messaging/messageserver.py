'''
This is the server entry point for Sentiet Artisan message routing
'''

import sys, os
import threading
import queue
import requests
import json
import time
from flask import Flask, render_template, request, jsonify
from MessageRouter import route_core, route_subsidiary
import Handlers
from Handlers import queue_handlers, ENGINE_HANDLER, CLIENT_HANDLER, MEMORY_HANDLER, FUNCTION_HANDLER, PROJECTOR_HANDLER, TIMER_HANDLER, QUEUE_HANDLER_NAMES

from logger import _print

TIME_TO_JOIN = 20

app = Flask(__name__)

userlist = ["@Teacher"]

@app.route('/process_messages', methods=['POST'])
def process_messages():

    data = request.json

    _print(f"2. messageserver::process_messages: data is {data}")

    messages = data["messages"]

    _print(f"messageserver::process_messages: messages are {messages}")

    if 'messages' not in data or 'handler_name' not in data:
        return jsonify({"error": "No messages provided"}), 400

    if not isinstance(messages, list):
        return jsonify({"error": "Messages should be a list"}), 400

    handler_name = data["handler_name"]
    if not isinstance(handler_name, str) or len(handler_name) == 0:
        return jsonify({"error": "handler_name should be a non-empty string"}), 400
    
    handler = queue_handlers[handler_name][0]
    handler_type = queue_handlers[handler_name][1]

    _print(f"3. messageserver::process_messages: before placing on in queue for handler name {handler_name} and handler_type {handler_type}")

    responses = handler.handle(queue_handlers[CLIENT_HANDLER][0], queue_handlers[CLIENT_HANDLER][0], messages = messages)

    _print(f"12. messageserver::process_messages: the responses are {responses}")

    # return jsonify({"processed_response": responses}), 200

    return {"processed_messages": responses}, 200

    return

if __name__ == '__main__':

    stop_event = threading.Event()

    # Start the core router thread
    corerouterthread = threading.Thread(target=route_core, args=(stop_event,queue_handlers,QUEUE_HANDLER_NAMES,))
    corerouterthread.daemon = True  # Daemonize thread to ensure it exits when main program exits
    corerouterthread.start()

    # Start the subsidiary router thread
    subsidiaryrouterthread = threading.Thread(target=route_subsidiary, args=(stop_event,queue_handlers,QUEUE_HANDLER_NAMES,))
    subsidiaryrouterthread.daemon = True  # Daemonize thread to ensure it exits when main program exits
    subsidiaryrouterthread.start()

    # Start the queue handler threads
    enginehandlerthread = threading.Thread(target=queue_handlers[ENGINE_HANDLER][0].threadloop, args=(stop_event,queue_handlers[ENGINE_HANDLER][0], queue_handlers[ENGINE_HANDLER][0],))
    enginehandlerthread.daemon = True  # Daemonize thread to ensure it exits when main program exits
    enginehandlerthread.start()

    # Start the queue handler threads
    memoryhandlerthread = threading.Thread(target=queue_handlers[MEMORY_HANDLER][0].threadloop, args=(stop_event,queue_handlers[MEMORY_HANDLER][0], queue_handlers[MEMORY_HANDLER][0],))
    memoryhandlerthread.daemon = True  # Daemonize thread to ensure it exits when main program exits
    memoryhandlerthread.start()

    # Start the queue handler threads
    functionshandlerthread = threading.Thread(target=queue_handlers[FUNCTION_HANDLER][0].threadloop, args=(stop_event,queue_handlers[FUNCTION_HANDLER][0], queue_handlers[FUNCTION_HANDLER][0],))
    functionshandlerthread.daemon = True  # Daemonize thread to ensure it exits when main program exits
    functionshandlerthread.start()

    # Start the queue handler threads
    projectorhandlerthread = threading.Thread(target=queue_handlers[PROJECTOR_HANDLER][0].threadloop, args=(stop_event,queue_handlers[PROJECTOR_HANDLER][0], queue_handlers[PROJECTOR_HANDLER][0],))
    projectorhandlerthread.daemon = True  # Daemonize thread to ensure it exits when main program exits
    projectorhandlerthread.start()

    # Start the queue handler threads
    # Not needed for timers right now but keep this code snippet
    #
    #timerhandlerthread = threading.Thread(target=queue_handlers[TIMER_HANDLER][0].threadloop, args=(stop_event,queue_handlers[TIMER_HANDLER][0], queue_handlers[TIMER_HANDLER][0],))
    #timerhandlerthread.daemon = True  # Daemonize thread to ensure it exits when main program exits
    #timerhandlerthread.start()

    app.run(debug=True, port=5002)

    stop_event.set()


    
