import sys, os
import json

class CConfigurator:

	_instance = None

	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			cls._instance = super().__new__(cls, *args, **kwargs)
		return cls._instance

	def __init__(self):
		self.db = {}

		print("CConfigurator.__init__ has been called")
		print()

		self.db["organization_variable_name"] = "organization"
		self.db["apikey_variable_name"] = "OPENAI_API_KEY"
		self.db["assistantid_variable_name"] = "ASSISTANT_ID"
		self.db["organization"] = os.getenv(self.getProperty("organization_variable_name"))
		self.db["OPENAI_API_KEY"] = os.getenv(self.getProperty("apikey_variable_name"))
		self.db["assistant_id"] = os.getenv(self.getProperty("assistantid_variable_name"))
		self.db["coding_id"] = os.getenv("CODING_ID")
		self.db["stream_system_prompt"] = f'''
		
		First: You will receive an array of communication packets in JSON format. Each packet will contain fields for sender, target and message content, type and direction and system which will be a dictionary.  Generate an array of packets like the source array wrapped like the original in JSON. Do NOT return the original input packet the AI receives where the type field is "in" and direction is "request" along with the response. Retain the sourcetargets start and end values exactly as in the original packet when creating the response packets. Do not change the start and end numbers. 
		
		Second: For each original packet Remember the original source from the packet call this SOURCE and the original target from the packet call this TARGET. If the message field starts with an @ symbol in front of a name make this name TARGET.

		Third(a): For each packet there will be a field called client_id. Copy this field client_id and its value into the response packet.

		Third(b): For each packet there will be a field called broadcast. Copy this field broadcast and its value into the response packet. 

		Third(c): For each packet there will be a field called agentprompt. Copy this field agentprompt and its value into the response packet exactly as is. 		

		Third(d): For each packet make sure there is a field called direction. This is either "request" if the packet is of type "in" or "response" if the packet is of type "out". Remember to include the field direction in any out packet. Also include the field system with the same values as in the in packet in the out packet.	

		Fourth: If the target TARGET is AI or system, first send back the original packet in the new list of packets. Then create a new packet with AI as the source and SOURCE as the target with all the same attributes as the original packet. Generate a response and make this the message in the message field with the @ symbol followed by SOURCe and a space in front for the new packet. For this response packet add a "direction" field and make the "direction" field in the packet the string "response". Retain the sourcetargets start and end values exactly as in the original packet when creating the response packets.
	
		Fifth: If the target TARGET is room, first send back the original packet in the new list of packets. Then create a new packet with AI as the source and room as the target. Generate a response and make this the message in the message field.  For this response packet add a "direction" field and make the "direction" field in the packet the string "response". Never duplicate responses for one input packet. 
					 
		Sixth: Create a new separate packet for each target. Always create a packet for each input packet with a response in the message field which may be blank. Always make the "direction" field "respone".
		
		Seventh: These packets relate to a network of human members and you the AI. 
		
		Eighth: When generating responses consider whether you want to add any packets and do so. Send packets to anyone who might be interested or for whom the message or response of any preceeding packet might be relevant or to anyone you feel needs to receive the packet.

		Ninth: If you are including code in your response first convert any < symbols to &lt; and any > symobols to &gt; Then put a <div id="{self.db["coding_id"]}"></div><br><pre  style="background-color: #cfcbcb;"><code> string just before the code block and a </code></pre><br> string after the code block. 

		Tenth: Always represent JSON documents in compact form without specifying that they are json. Always keep and include the system block regardless of the message. 
		'''

		self.db["image_system_prompt"] = f'''

		First, do not ever generate a response in the JSON format but rather in plain English.

		Second, do not try to draw the image at this point. Instead, clarify the image that the requestor has asked for. Always refer to the most recent request not earlier ones.

		Third, but if the requestor references an earlier image that was requested expand the requestor's words to specify the original request for that image.
		'''

		# which is not HTML code and does not include the <html> and </html> tags

		self.db["MESSAGE_TYPE_NAME"] = "type"
		self.db["MESSAGE_DIRECTION_NAME"] = "direction"
		self.db["MESSAGE_SOURCE_NAME"] = "source"
		self.db["MESSAGE_TARGET_NAME"] = "target"
		self.db["MESSAGE_AGENTPROMPT_NAME"] = "agentprompt"
		self.db["MESSAGE_CONTENT_NAME"] = "content"
		self.db["MESSAGE_RESPONSE_NAME"] = "response"
		self.db["MESSAGE_SYSTEMBLOCK_NAME"] = "system"

		# The SPECIAL type is a special category assigned by BusinessLogic
		self.db["STORE_QUEUE_IN"] = "in"
		self.db["STORE_QUEUE_OUT"] = "out"
		self.db["STORE_QUEUE_CONFIG"] = "config"
		self.db["STORE_QUEUE_SPECIAL"] = "special"
		self.db["STORE_QUEUE_IMAGE"] = "image"

		self.db["MESSAGE_TYPE_IN"] = "in"
		self.db["MESSAGE_TYPE_OUT"] = "out"
		self.db["MESSAGE_TYPE_CONFIG"] = "config"
		self.db["MESSAGE_TYPE_STORAGE"] = "storage" # used for asynchronously updating memory and AI
		self.db["MESSAGE_TYPE_SPECIAL"] = "special"
		self.db["MESSAGE_TYPE_IMAGE"] = "image"
		self.db["MESSAGE_TYPE_RESPONSE"] = "response"

		self.db["MESSAGE_DIRECTION_REQUEST"] = "request"
		self.db["MESSAGE_DIRECTION_RESPONSE"] = "response"

		self.db["MESSAGE_IMAGE_TYPE_KEYWORDS"] = ["draw", "picture", "image"]

		self.db["NETWORK_MEMBERS"] = '["AI"]'
		self.db["thread_id"] = None

		self.db["PACKET_NUMBER"] = 0
		self.db["PACKET_TTL"] = 2 # in days		

	def getProperty(self, key):
		return self.db[key]

	def setProperty(self, key, value):
		print(f"Adding key {key} with value {value}")
		self.db[key] = value

	def update(self, updatePacket):

		message_str = updatePacket["message"]

		try:
			d = json.loads(message_str)

			for key in d.keys():
				self.setProperty(key, d[key]) 
		except:
			print(f"Invalid JSON string for Configurator::update: {message_str}")
			return None
