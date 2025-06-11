import json

class CBusinessLogic:

	def __init__(self, config):
		self.configurator = config

	def process_and_address(self, message):
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

			outMessage = json.dumps(dMessage)

		except Exception as e:

			print(f"projectionserver: change_and_address: json error: {e} for string {outMessage}")

			outMessage = ""

		return outMessage
	
	def isJSON(self, message):
		'''
		Tests is a string is in JSON format or not
		If the message string is not JSON then let the message pass through
		'''
		print(f"projection::BusinessLogic:isJSON arrived")

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
		print(f"projection::BusinessLogic:isCorrectStructure arrived")

		try:
			dMessage = json.loads(message)

			if "content" not in dMessage:
				print(f"projection::BusinessLogic:isCorrectStructure no content field in message")
				return False, message
			
			contentStr = dMessage["content"]
			print(f"projectionserver::BusinessLogic::isCorrectStructure: type of content {contentStr} is {type(contentStr)}")

			if type(contentStr) is str:
				content = json.loads(contentStr)
			else:
				content = contentStr
				
			print(f"projection::BusinessLogic:isCorrectStructure returned true")
			
		except Exception as e:
			print(f"projection::BusinessLogic:isCorrectStructure exception {e} when loading the message dict")
			return False, message
		
		return True, message
	
