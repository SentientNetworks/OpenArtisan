import json
from FunctionRunner import CFunctionRunner 

class CBusinessLogic:

	def __init__(self, config):
		self.configurator = config
		self.runner = CFunctionRunner(self.configurator)

	def process_and_address(self, message, passthrough=False):
		'''
		readdresses a message to send it on to the next module in the chain
		'''

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
					print(f"Changing currentSource to maxTarget = {maxSource}")

				chainSource = dMessage["system"]["chain"][currentSource]
				chainTarget = dMessage["system"]["chain"][currentTarget]

				if passthrough:

					if chainSource == "functions" and chainTarget == "AI":

						dMessage["system"]["chain"][currentTarget] = "client"

			outMessage = json.dumps(dMessage)

		except Exception as e:

			print(f"functionserver: change_and_address: json error: {e} for string {outMessage}")

			outMessage = ""

		return outMessage
	
	def isJSON(self, message):
		'''
		Tests is a string is in JSON format or not
		If the message string is not JSON then let the message pass through
		'''
		print(f"functions::BusinessLogic:isJSON arrived")

		try:
			dMessage = json.loads(message)
			return True, message
		except:
			return False, message
	
	def isCorrectStructure(self, message):
		'''
		Tests that a message in the content field has the correct structure
		If the structure is not correct let the message pass through
		'''
		print(f"functions::BusinessLogic:isCorrectStructure arrived")

		try:
			dMessage = json.loads(message)

			if "content" not in dMessage:
				print(f"functions::BusinessLogic:isCorrectStructure no content field in message")
				return False, message
			
			contentStr = dMessage["content"]
			print(f"functionserver::BusinessLogic::isCorrectStructure: type of content {contentStr} is {type(contentStr)}")

			if type(contentStr) is str:
				content = json.loads(contentStr)
			else:
				content = contentStr

			if type(content) is not dict:
				print(f"functions::BusinessLogic:isCorrectStructure content not dict: {content}")
				return False, message
			
			if "type" not in content or "functions" not in content:
				print(f"functions::BusinessLogic:isCorrectStructure no type or content")
				return False, message
			
			if type(content["functions"]) is not list:
				print(f"functions::BusinessLogic:isCorrectStructure functions is not a list")
				return False, message
			
			# the list of functions must contain dicts with a key field "name"
			if len(content["functions"]) > 0:
				for function in content["functions"]:
					if type(function) is not dict:
						print(f"functions::BusinessLogic:isCorrectStructure function is not a dict")
						return False, message
					if "name" not in function:
						print(f"functions::BusinessLogic:isCorrectStructure function does not contain name")
						return False, message
			
			print(f"functions::BusinessLogic:isCorrectStructure returned true")
			
		except Exception as e:
			print(f"functions::BusinessLogic:isCorrectStructure exception {e} when loading the message dict")
			return False, message
		
		return True, message
	
	def findFunctions(self, message):
		'''
		Locates the correct function packages (script.py and maybe requirements.txt)
		returns this in a dict
		'''
		details = []

		print(f"functions::BusinessLogic:findFunctions arrived")

		# prepare is where we check all the files are in order
		# including the function structures
		# if required we create necessary directories or files
		# if prepare is successful we then extract the list of function structures
		details, result = self.runner.prepare(message)
		if not result:
			print(f"CBusinessLogic::runFunctions preparation failed for {details}")
			return None

		return details
	
	def runFunctions(self, message, details):
		'''
		Runs the functions and returns the output in a revised message
		'''
		print(f"functions::BusinessLogic:runFunctions arrived")

		if message is None or not self.isJSON(message):

			return message
		
		if details is None or type(details) is not list:

			return message
		
		print(f"functions::BusinessLogic:runFunctions ready to process functions")

		output = self.runner.run(details)
		if output is None:
			print(f"CBusinessLogic::runFunctions running failed for details = {details}")
			return message
		
		print(f"CBusinessLogic::runFunctions running succeeded for details = {details} with output = {output}")

		response = self.runner.respond(message, output, details)

		if response is None:
			return message
		else:
			return response



