'''
This module contains the function handler which implements the function server as a
thread loop for functions. It receives a pointer to the MessageQueue object which manages
the input and output queues for the message serving. These queues represent the consumer and producers
for Sentiet Message Server.
'''

import sys, os
import threading
import queue
import requests
import json
import time
import uuid

from logger import _print

REMOTE_SERVER_URI = "/process_messages"

PROJECTOR_ID = uuid.uuid4()

from Configurator import CConfigurator

configurator = CConfigurator()

class CProjectorHandler:

    _instance = None
    input_queue = None
    output_queue = None
    thread = None
    isActive = False
    activeStartTime = 0.0
    activeEndTime = 0.0
    loopInterval = 300

    def __new__(cls, *args, **kwargs):

        if cls._instance is None:

            cls._instance = super().__new__(cls, *args, **kwargs)
               
            cls.input_queue = queue.Queue()
            cls.output_queue = queue.Queue()

            cls.isActive = False

            cls.activeStartTime = 0.0
            cls.activeEndTime = 0.0

            cls.loopInterval = 300

        return cls._instance
    
    def activate(cls):
        cls.isActive = True

    def deactivate(cls):
        cls.isActive = False
    
    def extract_address(cls, messages):

        if type(messages) is not list or len(messages) <= 0:
            return "", ""
        
        message = messages[0]

        host, port = cls.extract_address_single(message)

        return host, port

    def extract_address_single(cls, message):

        if type(message) is not dict:

            try:
                message = json.loads(message)
            except Exception as e:
                return "", ""

        host = ""
        port = ""
        
        if "target" in message:

            target = message["target"]

            if "@" not in target:
                return "", ""
            
            user, host = target.split("@")

            port = ""
            if ":" in host:
                host, port = host.split(":")

        return host, port
    
    def isConfig(cls, message):

        try:
            d = json.loads(message)
            if "content" in d and "#config" in d["content"]:
                config = True
        except Exception as e:
            _print(f"CProjectorHandler::isConfig: error handling json: {e}")
            config = False        
        
    # API processing function 
    def api_process(cls, payload, server_uri, server_address, server_port="443", protocol="https"):

        server_url = f"{protocol}://{server_address}:{server_port}{server_uri}"

        try:
            beforeTime = time.time()

            _print(f"CProjectorHandler::api_process: server_url is {server_url} and payload is {payload}")

            # TODO: we need to set the client up with authorization 
            # to properly use https
            #response = requests.post(MESSAGE_SERVER_URL, json=payload, verify=certifi.where())

            response = requests.post(server_url, json=payload, verify=False)
            afterTime = time.time()
            elapsedTime = afterTime - beforeTime

            # Check if the request was successful

            _print(f"CProjectorHandler::api_process: the response is {response.json()}")
            if response.status_code == 200:
        
                _print(f"CProjectorHandler::api_process: Elapsed time is {elapsedTime} seconds")
                _print("")

                return json.dumps(response.json())
            
            else:

                _print(f"CProjectorHandler::api_process: Error: Received status code {response.status_code}")
                _print(f"CProjectorHandler::api_process: Response: {response.text}")

                return None
            
        except requests.exceptions.RequestException as e:

            _print(f"CProjectorHandler::api_process: Request failed: {e}")
            return None
        
    def threadloop(cls, stop_event, out_handler, in_handler):

        while not stop_event.is_set():
                
                try:

                    loopInterval = 300
                    if cls.isActive:
                        loopInterval = 3
                    else:
                        loopInterval = 300

                    cls.handle(out_handler, in_handler, messages = None)

                    time.sleep(loopInterval)

                except Exception as e:

                    _print(f"CProjectorHandler::threadloop: Serious error in handler loop: {str(e)}")
                    break

        return None
    
    def handle(cls, out_handler, in_handler, messages = None, handler_name = "client"):

        from BusinessLogic import CBusinessLogic
        businesslogic = CBusinessLogic(configurator)

        outMessages = []

        _print(f"CProjectorHandler::handle: start of handle loop before get")

        # Retrieve processed messages from the output queue
        # TODO: we should not want the output queue to be blocked 
        # TODO: so use get_nowait()

        outMessage = ""
        
        if not cls.isActive:
            outMessage = out_handler.output_queue.get()
        else:
            if not out_handler.output_queue.empty():
                outMessage = out_handler.output_queue.get_nowait()

        address = ""
        port = ""
        protocol = "https"
        config = False

        if outMessage is not None and type(outMessage) is str and len(outMessage) > 0:

            config = cls.isConfig(outMessage)

            if config:
                address, port = cls.extract_address_single(outMessage)

                out_handler.output_queue.put(outMessage)

                outMessage = ""

        _print(f"CProjectorHandler::handle: start of handle loop after get: message = {outMessage}")
        
        if outMessage is not None and type(outMessage) is str and len(outMessage) > 0:

            outMessages.append(outMessage)
                
            _print(f"CProjectorHandler::handler: Processed message: {outMessage}")    
            while not out_handler.output_queue.empty():
                outMessage = out_handler.output_queue.get()
                outMessages.append(outMessage)
                    
                _print(f"CProjectorHandler::handle: Processed message: {outMessage}")

        else:

            if cls.isActive:
                cls.activeEndTime = time.time()
                elapsedTime = cls.activeEndTime - cls.activeStartTime
                if elapsedTime > 10.0:
                    cls.deactivate()

            return []

        outMessages = businesslogic.process_and_address_messages(outMessages)
        outMessages = businesslogic.add_projector_id(outMessages, str(PROJECTOR_ID))

        if len(address) <= 0:
            address, port = cls.extract_address(outMessages)

        payload = {
                "messages": outMessages,
                "handler_name": handler_name
        }    

        _print(f"7. CProjectorHandler::handle: : after get before api_process: payload is {payload}")

        responses_str = ""
        
        if len(address) > 0:
            
            if not cls.isActive and len(outMessages) > 0:
                cls.activate()
                cls.activeStartTime = time.time()
                cls.activeEndTime = 0.0

            if len(port) <= 0:

                responses_str = cls.api_process(payload, REMOTE_SERVER_URI, address)

            else:

                if int(port) == 80 or int(port) > 5000:
                    protocol = "http"

                responses_str = cls.api_process(payload, REMOTE_SERVER_URI, address, server_port=port, protocol=protocol)
            
        _print(f"CProjectorHandler::handle:  outin responses_str is {responses_str}")

        responses = []

        if responses_str is None:

            for message_str in payload["messages"]:
                message_str = businesslogic.redirect_projection(message_str)
                _print(f"CProjectorHandler::handle: out Redirected message {message_str}")
                in_handler.input_queue.put(message_str)

            if cls.isActive:
                cls.activeEndTime = time.time()
                elapsedTime = cls.activeEndTime - cls.activeStartTime
                if elapsedTime > 10.0:
                    cls.deactivate()

            _print(f"CProjectorHandler::handle: out")
            return []

        elif responses_str is not None and len(responses_str) > 0:
            d = json.loads(responses_str)
            responses = d["processed_messages"]
            _print(f"CProjectorHandler::handle: outin responses is {responses}")

            outResponses = []
            if responses is not None and len(responses) > 0:

                cls.deactivate()
                cls.activeStartTime = 0.0
                cls.activeEndTime = 0.0

                for response_str in responses:
                    response = json.loads(response_str)                    
                    if "projector_redirected" in response:
                        del response["projector_redirected"]
                    response_str = json.dumps(response)
                    

                    _print(f"CProjectorHandler::handle: outin Processed response: {response_str}")
                    in_handler.input_queue.put(response_str)

                    outResponses.append(response_str)

            _print(f"CProjectorHandler::handle: outin")
            return outResponses                    

        _print(f"CProjectorHandler::handle: outin: final")

        return responses
