import os, sys
import json
from flask import Flask, request, jsonify

from sentietengine.PacketManager import CPacketManager


# Create the Flask application
app = Flask(__name__)

# Global PacketManager instance (singleton)
packet_manager = None

# Initialization method
@app.before_request
def initialize_manager():
    global packet_manager
    
    if packet_manager == None:
        packet_manager = CPacketManager()

def process_and_address(message):

    try:

        print(f"engine: process_and_address: message = {message}")

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

        print(f"engine: process_and_address: outMessage = {outMessage}")        

    except Exception as e:

        print(f"engine: process_and_address: json error: {str(e)}")

        outMessage = ""

    return outMessage

# Process request method
@app.route('/process_messages', methods=['POST'])
def process_messages():
    global packet_manager
    if not packet_manager:
        return jsonify({"error": "PacketManager not initialized"}), 500

    data = request.json
    if 'messages' not in data:
        return jsonify({"error": "No messages provided"}), 400

    messages = data['messages']
    if not isinstance(messages, list):
        return jsonify({"error": "Messages should be a list"}), 400

    #group = data['group']

    # process the messages with the AI
    processed_messages = packet_manager.process_messages(messages)
    
    # finally, address the messages to be placed in the queue
    addressed_messages = []
    for message in processed_messages:
        addressed_messages.append(process_and_address(message))

    print(f"engine: after addressing: messages = {addressed_messages}")

    return jsonify({"processed_messages": addressed_messages})

# Main entry point for running the server
if __name__ == '__main__':
    app.run(debug=True, port=5001)
