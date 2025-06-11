'''
This module contains the function handler which implements the agent server as a
thread loop for agents. It receives a pointer to the MessageQueue object which manages
the input and output queues for the message serving. These queues represent the consumer and producers
for Sentiet Message Server.
'''

import sys, os
import threading
import queue
import requests
import json
import time

from logger import _print

MEMORY_SERVER_URL = "http://127.0.0.1:5003/process_messages"

class CMemoryHandler:

    _instance = None
    input_queue = None
    output_queue = None
    thread = None

    def __new__(cls, *args, **kwargs):

        if cls._instance is None:

            cls._instance = super().__new__(cls, *args, **kwargs)
               
            cls.input_queue = queue.Queue()
            cls.output_queue = queue.Queue()

        return cls._instance

    # API processing function 
    def api_process(cls, payload, server_url):

        try:
            beforeTime = time.time()

            _print(f"8. CMemoryHandler::api_process: server_url is {server_url} and payload is {payload}")

            response = requests.post(server_url, json=payload)
            afterTime = time.time()
            elapsedTime = afterTime - beforeTime

            # Check if the request was successful

            _print(f"9. CMemoryHandler::api_process: the response is {response.json()}")
            if response.status_code == 200:
        
                _print(f"Elapsed time is {elapsedTime} seconds")
                _print("")

                return json.dumps(response.json())
            
            else:

                _print(f"Error: Received status code {response.status_code}")
                _print(f"Response: {response.text}")

                return None
            
        except requests.exceptions.RequestException as e:

            _print(f"Request failed: {e}")
            return None
        
    def threadloop(cls, stop_event, out_handler, in_handler):

        while not stop_event.is_set():
                
                try:

                    cls.handle(out_handler, in_handler, messages = None)
                        
                except Exception as e:

                    _print(f"CMemoryHandler::threadloop: Serious error in handler loop: {str(e)}")
                    break

        return None
    
    def handle(cls, out_handler, in_handler, messages = None):

        messages = []

        _print(f"CMemoryHandler::handle: start of handle loop before get")

        # Retrieve processed messages from the output queue
        message = out_handler.output_queue.get()
        messages.append(message)
            
        _print(f"CMemoryHandler::handler: Processed message: {message}")    
        while not out_handler.output_queue.empty():
            message = out_handler.output_queue.get()
            messages.append(message)
                
            _print(f"CMemoryHandler::handler: Processed message: {message}")

        payload = {
                "messages": messages
        }    

        _print(f"7. CMemoryHandler::handle: : after get before api_process: payload is {payload}")

        responses_str = cls.api_process(payload, MEMORY_SERVER_URL)
        _print(f"CMemoryHandler::handle:  outin responses_str is {responses_str}")
        d = json.loads(responses_str)
        responses = d["processed_messages"]
        _print(f"10. CMemoryHandler::handle: outin responses is {responses}")

        for response in responses:
            _print(f"CMemoryHandler::handle: outin Processed response: {response}")
            in_handler.input_queue.put(response)

        _print(f"CMemoryHandler::handle: outin")

        return responses
