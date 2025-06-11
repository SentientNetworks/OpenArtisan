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
from datetime import datetime
from Configurator import CConfigurator
from BusinessLogic import CBusinessLogic
from Handlers import ENGINE_HANDLER_INDEX, CLIENT_HANDLER_INDEX, MEMORY_HANDLER_INDEX, FUNCTION_HANDLER_INDEX, PROJECTOR_HANDLER_INDEX, TIMER_HANDLER_INDEX

from logger import _print

config = CConfigurator()
businesslogic = CBusinessLogic(config)

# API processing function 
def direct_and_pass(queue_handlers, queue_handler_names, current_handler_index, message_str, bypass = False):
    '''
    Direct and pass takes in a list of message strings
    It converts each message string to JSON
    It then reads the message and determines where to route the message to namely which handler to route to and which queue
    '''
    
    #if bypass:
    #    return None, "{}"

    new_handler_index, message_str = businesslogic.check_and_process(current_handler_index, message_str)
    
    if new_handler_index is None:
        return None, message_str
    else:
        return queue_handlers[queue_handler_names[new_handler_index]][0], message_str

# The core worker thread function
def route_core(stop_event, queue_handlers, queue_handler_names):
    
    while not stop_event.is_set():
            
            #time.sleep(1)
            
            try:
                beforeTime = time.time()
                beforeDatetime = datetime.now()
                
                _print("MessageRouter::route_core: Inside core router loop at client queues")
                process_queues(queue_handlers, queue_handler_names, CLIENT_HANDLER_INDEX, direct_and_pass, bypass = False)
                
                _print("MessageRouter::router_core: Inside core router loop at engine queues")
                process_queues(queue_handlers, queue_handler_names, ENGINE_HANDLER_INDEX, direct_and_pass, bypass = True)

                #time.sleep(1)

                afterTime = time.time()
                afterDatetime = datetime.now()
                elapsedTime = afterTime - beforeTime

                _print("")
                _print("==============")
                _print(f"messaging::MessageRounter::route_core [timing] the before datetime is {beforeDatetime}")
                _print(f"messaging::MessageRounter::route_core [timing] the after datetime is {afterDatetime}")
                _print(f"messaging::MessageRounter::route_core [timing] the elapsed time in seconds is {elapsedTime}")
                _print("==============")
                _print("")

                continue

            except Exception as e:

                _print(f"MessageRouter::route_core: Serious error in message loop: {str(e)}")
                break


# The subsidiary worker thread function
def route_subsidiary(stop_event, queue_handlers, queue_handler_names):
    
    while not stop_event.is_set():
            
            #time.sleep(1)
            
            try:
                beforeTime = time.time()
                beforeDatetime = datetime.now()
                
                _print("MessageRouter::route_subsidiary: Inside subsidiary router loop at memory queues")
                process_queues(queue_handlers, queue_handler_names, MEMORY_HANDLER_INDEX, direct_and_pass, bypass = True)

                _print("MessageRouter::route_subsidiary: Inside subsidiary router loop at functions queues")
                process_queues(queue_handlers, queue_handler_names, FUNCTION_HANDLER_INDEX, direct_and_pass, bypass = True)

                _print("MessageRouter::route_subsidiary: Inside subsidiary router loop at projector queues")
                process_queues(queue_handlers, queue_handler_names, PROJECTOR_HANDLER_INDEX, direct_and_pass, bypass = True)

                _print("MessageRouter::route_subsidiary: Inside subsidiary router loop at timer queues")
                process_queues(queue_handlers, queue_handler_names, TIMER_HANDLER_INDEX, direct_and_pass, bypass = True)

                time.sleep(1)

                afterTime = time.time()
                afterDatetime = datetime.now()
                elapsedTime = afterTime - beforeTime

                _print("")
                _print("==============")
                _print(f"messaging::MessageRounter::route_subsidiary [timing] the before datetime is {beforeDatetime}")
                _print(f"messaging::MessageRounter::route_subsidiary [timing] the after datetime is {afterDatetime}")
                _print(f"messaging::MessageRounter::route_subsidiary [timing] the elapsed time in seconds is {elapsedTime}")
                _print("==============")
                _print("")

                continue

            except Exception as e:

                _print(f"MessageRouter::route_subsidiary: Serious error in message loop: {str(e)}")
                break

# The worker thread function
def process_queues(handlers, handler_names, current_handler_index, direct_and_pass, bypass = False):
    
    try:

        current_handler = handlers[handler_names[current_handler_index]][0]
        handler_type = handlers[handler_names[current_handler_index]][1]

        # Get a message from the input queue
        message_str = current_handler.input_queue.get_nowait()

        _print(f"5. MessageRouter::process_queues: message_str is {message_str} with type {type(message_str)}")

        # get each message string individually by looping through getting from the input queue while it is not empty
        
        # loop around while the queue is not empty collecting all the message strings into a list
    
        if message_str is None or type(message_str) is not str or len(message_str) == 0:
            _print("No input from queue")
            return None
        
        _print(f"In MessageRouter::process_queues: ({current_handler_index}) message_str is {message_str}")

        next_handler, message_str = direct_and_pass(handlers, handler_names, current_handler_index, message_str, bypass = bypass)

        if next_handler is None:
            _print("MessageRouter::process_queues: throwing the message away!!!!!")
            return None
        else:
            _print("MessageRouter::process_queues: keeping the message!!!!!!!!")

        _print(message_str)
        
        # Put the response message into the output queue
        if message_str is not None:

            currentTime = datetime.now()
            _print("")
            _print(f"messaging::MessageRouter::process_queues: ({handler_names[current_handler_index]}) current time [timing] before inserting messages on output queue is {currentTime}")
            _print("")

            next_handler.output_queue.put(message_str)
        
            # Mark the task as done but only after all processing is complete
            # current_handler.input_queue.task_done()
        
        _print(f"MessageRouter::process_queues: message_str is {message_str}")

    except queue.Empty:
        _print("MessageRouter::process_queues: The queue is empty")
        time.sleep(3.0)

    except Exception as e:
        _print(f"Error in process_queues in MessageRouter is {e}")
        
    return None


