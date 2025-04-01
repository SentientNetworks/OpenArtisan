import json
from Handlers import QUEUE_HANDLER_NAMES
from Handlers import ENGINE_HANDLER_INDEX, CLIENT_HANDLER_INDEX

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

				print(f"Messaging: BusinessLogic:: check and process: chainsource={chainsource} chaintarget={chaintarget} next_index={next_index}")

			elif dmessage["source"] == "AI":

				next_index = CLIENT_HANDLER_INDEX

			else:

				next_index = ENGINE_HANDLER_INDEX

		except Exception as e:

			print(f"CBusinessLogic::check_and_process error reading json string: {e}")

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
	
	def belongs_to_client(self, client_tag, response_str):

		keep_response = True

		if len(response_str) > 0:

			response = json.loads(response_str)

			# We need a more complicated logic now that we have multiple clients (timer and main client)
			if "type" in response and "direction" in response:

				if response["type"] != "in" or response["direction"] != "request":

					if "broadcast" in response and response["broadcast"] is True:

						keep_response = True
					
					elif "client_id" in response and response["client_id"] == client_tag:

						keep_response = True

					else:

						keep_response = False
				
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
	


