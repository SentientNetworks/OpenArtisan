import json
from Handlers import QUEUE_HANDLER_NAMES
from Handlers import ENGINE_HANDLER_INDEX, CLIENT_HANDLER_INDEX

from logger import _print

class CBusinessLogic:

	def __init__(self, config):
		self.configurator = config

	def check_and_process(self, current_handler_index, message_str, instructions=None):

		try:
			dmessage = json.loads(message_str)
			next_index = None


			if "system" in dmessage and type(dmessage["system"]) is dict:

				chain = dmessage["system"]["chain"]
				chainLength = len(chain)
				chainSourceIndex = dmessage["system"]["sourcetargets"]["start"]
				chainTargetIndex = dmessage["system"]["sourcetargets"]["end"]

				# find correct index based on system values
				chainsource = chain[chainSourceIndex]
				if chainsource == "AI":
					chainsource = "engine"
				chaintarget = chain[chainTargetIndex]
				if chaintarget == "AI":
					chaintarget = "engine"

				if chainSourceIndex >= chainLength - 1:

					return None, message_str

				next_index = QUEUE_HANDLER_NAMES.index(chaintarget)

				_print(f"Messaging: BusinessLogic:: check and process: chainsource={chainsource} chaintarget={chaintarget} next_index={next_index}")

			elif dmessage["source"] == "AI":

				next_index = CLIENT_HANDLER_INDEX

			else:

				next_index = ENGINE_HANDLER_INDEX

		except Exception as e:

			_print(f"CBusinessLogic::check_and_process error reading json string: {e}")

		if next_index is not None:
			return next_index, message_str
		
		return None, "{}"
	
	def check_for_client_tag(self, messages):

		client_tag = ""

		if len(messages) > 0:

			message = json.loads(messages[0])

			if "client_id" in message:

				client_tag = message["client_id"]

				# the stub first message now has two keys - client_id and timestamp
				if len(message.keys()) == 1:

					messages = messages[1:] 

		return client_tag, messages
	
	def belongs_to_client(self, client_tag, projector_tag, response_str):

		keep_response = True

		projectable = False
		if projector_tag is not None and type(projector_tag) is str and len(projector_tag) > 0:
			projectable = True

		if len(response_str) > 0:

			response = json.loads(response_str)

			# We need a more complicated logic now that we have multiple clients (timer and main client)
			if "type" in response and "direction" in response and "target" in response:

				if response["type"] != "in" or response["direction"] != "request":

					broadcast = response["broadcast"]
					client_id = response["client_id"]

					_print(f"messaging::CBusinessLogic::belongs_to_client: for response broadcast is {broadcast} and client_id is {client_id}")

					if "broadcast" in response and broadcast is True:

						keep_response = True
					
					elif "client_id" in response and client_id == client_tag:

						keep_response = True

					else:

						keep_response = False
					
					if "projector_redirected" in response:

						redirected = response["projector_redirected"]

						_print(f"messaging::CBusinessLogic::belongs_to_client: for response redirected is {redirected}")

						#if redirected and keep_response and "@" in response["target"] and not projectable:
						if redirected:
							
							keep_response = projectable

							_print(f"messaging::CBusinessLogic::belongs_to_client: ready for projection: keep_response = {keep_response}")
			
				else:

					keep_response = False				

			else:

				keep_response = False
				response_str = ""

		return keep_response, response_str
	
	def redirect_to_storage(cls, message_str):

		redirected_message_str = message_str

		dmessage = json.loads(redirected_message_str)

		# if there is not system block then we can't redirect this message
		if "system" not in dmessage:

			return ""
		
		dmessage["system"]["chain"] = ["client", "memory", "AI"]
		dmessage["system"]["method"] = ["none", "put", "prompt"]
		dmessage["system"]["sourcetargets"]["start"] = 0
		dmessage["system"]["sourcetargets"]["end"] = 1

		dmessage["type"] = "storage"

		redirected_message_str = json.dumps(dmessage)

		return redirected_message_str   

	def redirect_to_client(self, response_str):

		if len(response_str) == 0:
			return response_str
		
		try:

			d = json.loads(response_str) 
			d["type"] = "out"
			d["direction"] = "response"
			response_str = json.dumps(d)

		except Exception as e:

			_print(f"messaging::businesslogic::redirect_to_client: error {e}")

		return response_str

	def process_and_address_messages(self, messages, passthrough=False):
		'''
		readdresses a list of messages
		'''
		if len(messages) == 0:
			return messages
		
		outMessages = []
		for message in messages:

			_print(f"messaging::BusinessLogic::process_and_address_messages: before addressing message = {message}")

			outMessage = self.process_and_address(message, passthrough=passthrough)

			_print(f"messaging::BusinessLogic::process_and_address_messages: after addressing message = {outMessage}")
			
			if len(outMessage) > 0:

				outMessages.append(outMessage)

		return outMessages

	def process_and_address(self, message, passthrough=False):
		'''
		readdresses a message to send it on to the next module in the chain
		'''
		if len(message) == 0:
			return message

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
					_print(f"Changing currentSource to maxTarget = {maxSource}")

				chainSource = dMessage["system"]["chain"][currentSource]
				chainTarget = dMessage["system"]["chain"][currentTarget]

				if passthrough:

					if chainSource == "functions" and chainTarget == "AI":

						dMessage["system"]["chain"][currentTarget] = "client"

			outMessage = json.dumps(dMessage)

		except Exception as e:

			_print(f"messaging::CBusinessLogic: process_and_address: json error: {e} for string {outMessage}")

			outMessage = ""

		return outMessage

	def redirect_projection(self, message_str):

		try:

			d = json.loads(message_str)

			d["projector_redirected"] = True

			message_str = json.dumps(d)

			return message_str
		
		except Exception as e:

			_print(f"messaging::CBusinessLogic::redirect_projection: error {e}")

	def add_projector_id(self, messages, projector_id):

		if len(messages) == 0:

			message_str = '{"projector_id": ' + projector_id + '}'
			messages.append(message_str)

		outMessages = []
		for message_str in messages:

			try:
				d = json.loads(message_str)

				if "projector_id" not in d:
					d["projector_id"] = projector_id

				message_str = json.dumps(d)

				outMessages.append(message_str)

			except Exception as e:

				_print(f"messaging::CBusinessLogic::add_projector_id: error {e}")
				outMessages = None
				break

		return outMessages
	
	def check_for_projector_tag(self, messages):

		if type(messages) is not list or len(messages) == 0:
			return None, []
		
		message_str = messages[0]

		_print(f"messaging::CBusinessLogic::check_for_projector_tag: message_str is {message_str}")

		projector_tag = None

		try:
			d = json.loads(message_str)

			if "projector_id" in d:
				
				projector_tag = d["projector_id"]

				if "type" not in d and "direction" not in d and len(messages) == 1:
					## this is a dummy message for the projector id
					return projector_tag, []
				
				return projector_tag, messages

		except Exception as e:
			_print(f"messaging::CBusinessLogic::check_for_projector_tag: error {e}")
			return None, messages
		
		return None, messages