'''
This module contains the function message_loop which implements the message server as a
thread loop for the client app. It receives a pointer to the MessageQueue object which manages
the input and output queues for the message serving. These queues represent the consumer and producers
for Sentiet Chat.
'''

import sys, os
import threading
import queue
import requests
import json
import time

from Configurator import CConfigurator

configurator = CConfigurator()

class CClientHandler:

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

    def handle(cls, out_handler, in_handler, messages = None):

            # Put messages in the input queue
            # This should be done for each individual message not the list of message strings

            # To enable asynchronicity we need to pass a tag for the current client instance
            # that is entered into each input message and checked in each output reponse
            # responses that match are returned and those that don't are pushed back onto the 
            # output queue.
            #
            # All messages from the client should contain the client identifier field or tag.
            # If there are no real messages there will be a stub message with only the identifier
            # field. In this case we extract the tag and throw the message away. If there is no
            # message with the tag or no messages at all we don't go any further.
            #
            # Alternatively if the first message does not contain the tag then push it into the
            # input queue and then grab whatever is on the output queue without checking for the tag.
            # We probably want to keep some metadata for the tag like the client name and type.
            #
            # At this point this module doesn't know about client tags and what to do with output.
            # This is kept in the business logic.

            from BusinessLogic import CBusinessLogic
            businesslogic = CBusinessLogic(configurator)

            client_tag, messages = businesslogic.check_for_client_tag(messages)

            print(f"4. CClientHandler::handle: type is inout and messages is {messages}")

            # Handle both messages for processing and messages for storage
            # Do this in blocks of messages. Don't interleave.
            
            for message_str in messages:            
                in_handler.input_queue.put(message_str)

            # Copy each message, redirect to memory and AI and stop there
            for message_str in messages:
                redirected_message_str = businesslogic.redirect_to_storage(message_str)
                in_handler.input_queue.put(redirected_message_str)
            
            responses = []

            print("CClientHandler::handle: ")   

            # Retrieve processed messages from the output queue
            # Do this asynchronously so use get_nowait()

            if out_handler.output_queue.qsize() <= 0:
                 return []
            
            response_str = out_handler.output_queue.get_nowait()

            keep_response, response_str = businesslogic.belongs_to_client(client_tag, response_str)

            print(f"CClientHandler::handle: keep_response = {keep_response}, client tag = {client_tag}, response_str = {response_str}")

            # Check that the response_str matches the current client' tag
            # if it matches and is not empty and is a string then add it to the output.

            if len(response_str) > 0:
                if keep_response:
                    responses.append(response_str)
                else:
                    out_handler.output_queue.put(response_str)

            # otherwise we put the response_str back on the output queue
            
            print("11. CClientHandler::handle: Processed response:", response_str)    

            return responses
















