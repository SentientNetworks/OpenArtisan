'''
This is the server entry point for Sentiet Chat. It sets up the listening thread, returns to core page and listens for
socketio messages.
'''
import eventlet
from eventlet import wsgi

# Monkey patch to make socketio work with Eventlet
eventlet.monkey_patch()

import sys, os
import threading
import queue
import requests
import json
import time
import pytz
import uuid
import base64
from collections import deque

from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask import copy_current_request_context

from MessageHandler import handle

from logger import _print

TIME_TO_JOIN = 20

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

socketio = SocketIO(app, compression=True, async_mode='eventlet', ping_interval=10, cors_allowed_origins='*')

queuehandler = None
userlist = ["@Teacher"]
roomtype = "chatui"

CLIENT_ID = uuid.uuid4()

input_queue = queue.Queue()
stack = deque()

default_commands = '{"target": "system", "system": { "chain": ["client", "AI", "client"], "method": ["none", "prompt", "none"], "sourcetargets": {"start": 0, "end": 1} } }'

def getCurrentTime():

    local_tz = pytz.timezone('Pacific/Auckland')

    # Get the current time
    current_time = datetime.now(local_tz)

    # Format the time to include seconds
    time_with_seconds = current_time.strftime("%H:%M:%S %Z%z")

    return str(time_with_seconds)

def getCurrentTimestamp():

    # Get the current time
    current_time = time.time()

    # Format the time to include seconds

    return str(current_time)

@app.route('/')
def index():
    
    return show_page(roomtype)

@app.route('/<page>')
def show_page(page):

    roomtype = page
    
    if roomtype not in ["chatroom", "chatui"]:
        return 404
    
    coding_id = os.getenv('CODING_ID', '')
    return render_template(f'index_{roomtype}.html', coding_id=coding_id, default_commands=default_commands)

@socketio.on('connect')
def handle_connect():
    _print('A new client has connected!')
    # You can send a welcome message or initialize data here
    join_room("room")
    send({'type': 'connect', 'username': '', 'userlist': userlist, 'room': 'room'})

# SocketIO event handler for disconnections
@socketio.on('disconnect')
def handle_disconnect():
    _print('A client has disconnected.')
    leave_room('room')
    send({'type': 'disconnect', 'username': '', 'room': 'room'}, broadcast=True)

# create function def makeMesssage(...): ... return json.dumps()

def save_file(message, folderpath):

    if type(message) is not dict:
        return
    if "filename" not in message:
        return
    
    filename = message["filename"]
    filedata = message["filedata"]

    file_path = os.path.join(UPLOAD_FOLDER, filename)

    try:
        decode_text_to_file(filedata, output_path=file_path)
    except Exception as e:
        _print(f"clientserver::save_file: error {e}")
        return
    
    #with open(file_path, 'wb') as f:
    #    f.write(filedata)
    
    _print(f'clientserver::handle_message: File {filename} saved successfully.')

    return

# Encode file as text
def encode_file_to_text(file_path=None, file_data = None):

    if file_path is not None:
        with open(file_path, 'rb') as file:
            encoded_text = base64.b64encode(file.read()).decode('utf-8')
    elif file_data is not None:
        encoded_text = base64.b64encode(file_data).decode('utf-8')

    return encoded_text

# Decode text to file
def decode_text_to_file(encoded_text, output_path=None):
    decoded_text = base64.b64decode(encoded_text.encode('utf-8'))

    if output_path is not None:
        with open(output_path, 'wb') as file:
            file.write(decoded_text)

def makeMessage(username, sender, receiver, commands, agentprompt, direction, content, client_id):

    dMessage = {}

    dMessage["source"] = sender
    dMessage["target"] = receiver
    dMessage["type"] = "in"
    dMessage["direction"] = direction
    dMessage["agentprompt"] = agentprompt
    broadcast = False

    if type(content) is dict and "filename" in content and "filedata" in content and len(content["filename"]) > 0:
        encoded_data = encode_file_to_text(file_path=None, file_data=content["filedata"])
        content["filedata"] = encoded_data
        broadcast = False

    _print(f"clientserver::makeMessage: content = {content}.")

    dMessage["content"] = content
    dMessage["client_id"] = str(client_id)
    dMessage["broadcast"] = broadcast
    dMessage["timestamp"] = getCurrentTimestamp()

    if len(commands) == 0:
        commands = default_commands

    try:

        dCommands = json.loads(commands)

        if type(dCommands) is dict:

            for key, value in dCommands.items():
                dMessage[key] = value

    except Exception as e:

        _print(f"ClientServer::makeMessage: error reading json string: {e}")   

    return json.dumps(dMessage)

@socketio.on('message')
def handle_message(data):

    try:
         
        _print(f"handle_message: data = {data}")

        if data["type"] == "join":

            room = data['room']
            username = data['username']
            _print(f'{username} is joining the room {room}.')

            join_room(room)
            if username not in userlist:
                userlist.append(username)

            _print(f"Userlist is now {userlist}")

            send({'type': 'join', 'username': username, 'userlist': userlist, 'room': room}, broadcast=True)

        elif data["type"] == "leave":

            room = data['room']
            username = data['username']
            _print(f'{username} is leaving the room {room}.')

            leave_room(room)
            if username in userlist:
                userlist.remove(username)

            _print(f"Userlist is now {userlist}")

            send({'type': 'leave', 'username': username, 'userlist': userlist, 'room': room}, broadcast=True)            

        elif data["type"] == "message":

            username = data['username']
            content = data['message']
            sender = data['sender'].replace("@", "")
            receiver = data['receiver'].replace("@", "")
            commands = data["commands"]
            agentprompt = data["agentprompt"]

            #save_file(content, UPLOAD_FOLDER)

            in_direction = "request"
            if sender != "AI" and sender != "room":
                if receiver != "AI" and receiver != "room":
                    in_direction = "request_noresponse"

            messages = []
            # change to messages.append(makeMessage(...))
            messages.append(makeMessage(username, sender, receiver, commands, agentprompt, in_direction, content, CLIENT_ID))

            for message_str in messages:

                d = json.loads(message_str)

                header = f"<div id={os.getenv('CODING_ID', '')}></div>"

                if type(d["content"]) is dict and "filename" in d["content"] and len(d["content"]["filename"]) > 0:
                    save_file(d["content"], UPLOAD_FOLDER)
                    prompt = ""

                    filename = d["content"]["filename"]                    

                    if "prompt" in d["content"] and len(d["content"]["prompt"]) > 0:
                        prompt = d["content"]["prompt"]
                        prompt = prompt.replace("{{last_image}}", f"<img src=\"/file_image/{filename}\">")
                        prompt = prompt.replace("{{header}}", header)
                    else:
                        prompt = f"{header}<br><br><img src=\"/file_image/{filename}\"><br><br>"
                    d["content"] = prompt 
                else:
                    prompt = d["content"]
                    prompt = prompt.replace("{{header}}", header)
                    d["content"] = prompt

                #sender = d["source"]
                #receiver = d["target"]
                username = d["source"]
                direction = d["direction"]
                message = d

                datetimeStr = getCurrentTime()

                _print("Message: " + str(d))
            
                if direction == "request":
                    emit('message', {'type': 'message', 'username': sender, 'sender': sender, 'receiver': receiver, 'message': message, 'timestamp': datetimeStr, "undo_hourglass": "true"}, broadcast=True, include_self=True)
                elif direction == "request_noresponse":
                    emit('message', {'type': 'message', 'username': sender, 'sender': sender, 'receiver': receiver, 'message': message, 'timestamp': datetimeStr, "undo_hourglass": "true"}, broadcast=True, include_self=True)            

            if len(messages) == 0:

                d = {}
                d["client_id"] = str(CLIENT_ID)
                #d["timestamp"] = getCurrentTimestamp()

                message_str = json.dumps(d)

                messages.append(message_str)

                _print(f"clientserver::handle_message adding special message: {message_str}")

            for message_str in messages:
                _print(f"clientserver::handle_message putting message on input queue: {message_str}")
                input_queue.put(message_str)

            # This changes - now we directly call and block on an API call to the MessageServer
            # No queues are used in the client itself

        @copy_current_request_context
        def threadloop(stop_event, socketio):

            while not stop_event.is_set():
                    
                    _print("clientserver::threadloop: at beginning")

                    try:

                        time.sleep(1)

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
                            _print("clientserver::threadloop: input queue not empty")
                            
                            message_str = input_queue.get_nowait()
                        else:
                            d = {}
                            d["client_id"] = str(CLIENT_ID)

                            message_str = json.dumps(d)

                        _print(f"clientserver::threadloop: message_str = {message_str}")

                        messages = [message_str]

                        responses = []
                        responses = handle(messages)

                        for response in responses:

                            d = json.loads(response)

                            header = f"<div id={os.getenv('CODING_ID', '')}></div>"

                            if type(d["content"]) is dict and "filename" in d["content"] and len(d["content"]["filename"]) > 0:
                                save_file(d["content"], UPLOAD_FOLDER)
                                prompt = ""

                                filename = d["content"]["filename"]

                                if "prompt" in d["content"] and len(d["content"]["prompt"]) > 0:
                                    prompt = d["content"]["prompt"]
                                    prompt = prompt.replace("{{last_image}}", f"<img src=\"/file_image/{filename}\">")
                                    prompt = prompt.replace("{{header}}", header)
                                else:
                                    prompt = f"{header}<br><br><img src=\"/file_image/{filename}\"><br><br>"
                                d["content"] = prompt 
                            else:
                                prompt = d["content"]
                                prompt = prompt.replace("{{header}}", header)
                                d["content"] = prompt

                            sender = d["source"]
                            receiver = d["target"]
                            username = sender
                            if "direction" not in d.keys():
                                d["direction"] = "response"
                            direction = d["direction"]
                            content = d["content"]
                            message = d

                            datetimeStr = getCurrentTime()

                            _print("Response: " + str(d))
                        
                            if (direction != "request" and direction != "request_noresponse") and len(content) > 0:
                                                    
                                _print(f"chatserver::handle_server: roomtype is {roomtype} and content is {content}")

                                if roomtype == "chatroom" and "<img " in content:
                                    socketio.emit('image_message', {'type': 'image', 'username': username, 'sender': sender, 'receiver': receiver, 'message': message, 'timestamp': datetimeStr, "undo_hourglass": "true"})
                                else:
                                    emit('message', {'type': 'message', 'username': username, 'sender': sender, 'receiver': receiver, 'message': message, 'timestamp': datetimeStr, "undo_hourglass": "true"}, broadcast=True, include_self=True)
                            

                    except Exception as e:

                        _print(f"clientserver::threadloop: Serious error: {str(e)}")
                        break

            return None     

            # Start the queue handler thread
        stop_event = threading.Event()
        clientthread = threading.Thread(target=threadloop, args=(stop_event,socketio))
        clientthread.daemon = True  # Daemonize thread to ensure it exits when main program exits
        clientthread.start()    
              


    except Exception as e:
        _print(f"Error: {e}")
        emit('error', {'msg': str(e)}) 


@socketio.on('join')
def handle_join(data):
    
    try:
        room = data['room']
        username = data['username']

        _print(f'{username} is joining the room {room}.')

        join_room(room)
        if username not in userlist:
             userlist.append(username)
        
        _print(f"Userlist is now {userlist}")

        emit('join', {'type': 'join', 'username': username, 'userlist': userlist, 'room': room}, broadcast=True)

    except Exception as e:
        _print(f"Error: {e}")
        emit('error', {'msg': 'Failed to join the room'})        
        
@socketio.on('leave')
def handle_leave(data):
        
        room = data['room']
        username = data['username']

        leave_room(room)

        _print(f'{username} is leaving the room {room}.')

        if username in userlist:
             userlist.remove(username)
        
        _print(f"Userlist is now {userlist}")
        
        send({'type': 'leave', 'username': username, 'userlist': userlist, 'room': room}, broadcast=True)

@app.route('/file_image/<filename>', methods=['GET'])
def serve_image(filename):

    _print(f"clientserver::serve_image: entered filename = {filename}")

    path = os.path.join(UPLOAD_FOLDER, filename)

    _print(f"clientserver::serve_image: path = {path}")

    if os.path.exists(path):
        return send_file(path, mimetype='image/jpeg')  # adjust MIME type if needed
    else:
        _print(f"clientserver::serve_image: path {path} does not exist.")
        abort(404)


if __name__ == '__main__':
    
    listener = eventlet.listen(('127.0.0.1', 5000))  # You can change the host and port as needed


    _print("Starting WSGI server with Eventlet on http://127.0.0.1:5000")

    wsgi.server(listener, app)  # Start the WSGI server    


