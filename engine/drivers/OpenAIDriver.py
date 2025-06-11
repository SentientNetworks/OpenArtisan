import os
import time
import json
import copy
import base64
import openai
from openai import OpenAI

DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def pretty_print_assistant_response(messages, f=None):

	if f is not None:
		#print("{", file=f)
		for m in messages:
			if m.role == "assistant":
				print(f"{m.content[0].text.value}", file=f)
				break
			#print(",", file=f)
		#print("}", file=f)
	else:
		print("# Messages")
		for m in messages:
			print(f"{m.role}: {m.content[0].text.value}")
		print()

# Decode text to file
def decode_text_to_file(encoded_text, output_path=None):
    decoded_text = base64.b64decode(encoded_text.encode('utf-8'))

    if output_path is not None:
        with open(output_path, 'wb') as file:
            file.write(decoded_text)

def create_driver(configurator):
	return COpenAIDriver(configurator)

class COpenAIDriver:

	def __init__(self, config):
		self.configurator = config
		self.ready = True

		openai.organization = self.configurator.getProperty("organization")
		os.environ["OPENAI_API_KEY"] = self.configurator.getProperty("OPENAI_API_KEY")

		self.api_client = OpenAI()

	def extractResponse(self, messages):

		response = ""
		for m in messages:
			if m.role == "assistant":
				response = f"{m.content[0].text.value}"
				break

		return response
	
	def isFilePrompt(self, prompt):

		try:

			dPrompt = json.loads(prompt)

			if type(dPrompt) is dict and "filename" in dPrompt and len(dPrompt["filename"]) > 0 and "file_ids" in dPrompt:

				if "prompt" in dPrompt and len(dPrompt["prompt"]) > 0:

					return dPrompt["file_ids"], dPrompt["prompt"]

				return dPrompt["file_ids"], None
			
		except Exception as e:

			print(f"engine::CAIDriver::isFilePrompt: error {e}")

		return [], None
	
	def fileUpload(self, stream):

		try:
			d = json.loads(stream)

			if len(d["packets"]) > 0:

				for packet in d["packets"]:

					if type(packet["message"]) is not dict or "filename" not in packet["message"] or len(packet["message"]["filename"]) <= 0:

						break

					filename = packet["message"]["filename"]
					filedata = packet["message"]["filedata"]
					filepath = os.path.join(DOWNLOAD_FOLDER, filename)

					decode_text_to_file(filedata, output_path=filepath)

					# we cannot upload raw encoding for files greater that 5kb into the AI
					# so we replace the filedata with the string "Ready to Process"

					with open(filepath, 'rb') as file:
						# Upload the file
						response = self.api_client.files.create(
							file=file,
							purpose='assistants'  # Specify the purpose of the file
						)

					# Extract the file ID from the response
					file_id = response.id					

					packet["message"]["file_ids"] = [file_id]
					packet["message"]["filedata"] = "<Ready to Process> Tell me about the file just uploaded."

				stream = json.dumps(d)

		except Exception as e:

			print(f"engine::CAIDriver:fileUpload error {e}")

		return stream

	def processPrompt(self, user_prompt, system_prompt):

		print(f"inside processPrompt: before prompt = {user_prompt}")

		beforeAllTime = time.time()

		print(self.configurator.getProperty("thread_id"))
		print()

		if self.configurator.getProperty("thread_id") is None:

			#print("About to create a thread")
			print(f"Before client beta threads create")

			thread = self.api_client.beta.threads.create(
				messages=[
    				{
      					"role": "user",
      					"content": user_prompt,
    				}
  				]
			)

			print(f"After client beta threads create thread - {thread.id}")

			self.configurator.setProperty("thread_id", thread.id)
		else:

			thread = self.api_client.beta.threads.retrieve(self.configurator.getProperty("thread_id")) 

		print(f"Before client beta threads messages create")
		print(thread.id)
		print("")

		file_ids, real_prompt = self.isFilePrompt(user_prompt)
		if real_prompt is not None:
			user_prompt = real_prompt
			
		if len(file_ids) > 0:		
			message = self.api_client.beta.threads.messages.create(
				thread_id=thread.id,
				role='user',
				content=f"{user_prompt}. Please analyze the attached document in detail.",
				attachments=[
					{
						# For now we assume each message has only one file attached
						'file_id': file_ids[0],
						'tools': [{'type': 'file_search'}]
					}
				]
			)	
		else:	
			message = self.api_client.beta.threads.messages.create(thread.id, role = "user", content = user_prompt)
		print(f"After client beta threads messages create message = {message.id}")

		beforeTime = time.time()

		run = self.api_client.beta.threads.runs.create(
	  		thread_id=thread.id,
	  		assistant_id=self.configurator.getProperty("assistant_id"),
	  		instructions=system_prompt
		)
 
		while run.status in ["queued", "in_progress", "cancelling"]:
			time.sleep(1) # Wait for 1 second
			run = self.api_client.beta.threads.runs.retrieve(
				thread_id=thread.id,
	    		run_id=run.id
	  		)

		out_stream = "{}"
		if run.status == "completed": 
			messages = self.api_client.beta.threads.messages.list(
				thread_id=thread.id
			)

			response = self.extractResponse(messages)

			with open('response.txt', 'a', encoding='utf-8') as f:
				#pretty_print_assistant_response(messages, f=f)
				print(str(user_prompt), file=f)
				print(file=f)
				print(str(response), file=f)

		else:
			print(run.status)

		afterTime = time.time()

		self.ready = True

		elapsedTime = afterTime - beforeTime
		elapsedAllTime = afterTime - beforeAllTime

		print()
		print(f"inside processPrompt: in {elapsedAllTime} and {elapsedTime} seconds after response = {response}")
		print()
		
		return response
	
	def processImagePrompt(self, prompt):

		response_obj = self.api_client.images.generate(model="dall-e-3", prompt=prompt, n=1, size="1024x1024")

		#print(f"response_obj = {response_obj}")
		
		for image_info in response_obj.data:

			url = image_info.url
			break

		response = f'<div id="{self.configurator.getProperty("coding_id")}"></div><img src="{url}">'

		return response


	def processStream(self, stream):

		print(f"inside processStream: before stream = {stream}")

		self.ready = False

		system_prompt = self.configurator.getProperty("stream_system_prompt")

		# we include the agent prompt for the first packet in the stream if non-empty

		try:
			
			if len(stream) > 0:
				dStream = json.loads(stream)
				if type(dStream) is dict and len(dStream) > 0 and len(dStream["packets"]) > 0:
					first_packet = dStream["packets"][0]
					if "agentprompt" in first_packet:
						agentprompt = first_packet["agentprompt"]
						system_prompt = f"{system_prompt} {agentprompt}"

		except Exception as e:

			print(f"AIDriver::processSteam error = {e}")

			out_packet = {}
			out_packet["target"] = "room"
			out_packet["source"] = "Error"
			out_packet["type"] = self.configurator.getProperty("MESSAGE_TYPE_OUT")
			out_packet["message"] = f"{str(e)}: {stream}"
			out_packet["system"] = {"target": "system", "system": { "chain": ["client", "AI", "client"], "method": ["none", "prompt", "none"], "sourcetargets": {"start": 0, "end": 1} } }

			out_stream = {}
			out_stream["packets"] = [out_packet]

			response = json.dumps(out_stream)

		try:

			response = self.processPrompt(stream, system_prompt)

		except Exception as e:

			print(f"AIDriver::processSteam error = {e}")

			out_packet = {}
			out_packet["target"] = "room"
			out_packet["source"] = "Error"
			out_packet["type"] = self.configurator.getProperty("MESSAGE_TYPE_OUT")
			out_packet["message"] = f"{str(e)}: {stream}"
			out_packet["system"] = {"target": "system", "system": { "chain": ["client", "AI", "client"], "method": ["none", "prompt", "none"], "sourcetargets": {"start": 0, "end": 1} } }

			out_stream = {}
			out_stream["packets"] = [out_packet]

			response = json.dumps(out_stream)

		self.ready = True
	
		print(f"inside processStream: after response = {response}")

		return response
	
	def stripImageRequest(self, packet):
		'''
		tests if the message field contains the strings #picture or #image
		If so it strips these strings out and returns True plus
		the revised packet
		'''
		if "#picture" in packet["message"] or "#image" in packet["message"]:

			packet["message"] = packet["message"].replace("#picture", "")
			packet["message"] = packet["message"].replace("#image", "")

		return packet

	def processImageStream(self, in_stream):
		'''
		Generate a set of images from the packets in a stream
		and return as a stream
		'''

		print(f"inside processImageStream: before stream = {in_stream}")

		self.ready = False

		d = json.loads(in_stream)

		out_packets = []

		for i in range(0, len(d["packets"])):

			in_packet = d["packets"][i]
			message = in_packet["message"]

			out_packet = copy.deepcopy(in_packet)

			try:
				system_prompt = self.configurator.getProperty("image_system_prompt")
				image_prompt = self.processPrompt(message, system_prompt)

				out_message = self.processImagePrompt(image_prompt)

				out_packet["target"] = in_packet["source"]
				out_packet["source"] = "AI"

			except Exception as e:

				print(f"images creation failed: {e}")

				out_message = str(e)

				out_packet["target"] = in_packet["source"]
				out_packet["source"] = "Error"

			out_packet["message"] = out_message
			out_packet["type"] = self.configurator.getProperty("MESSAGE_TYPE_OUT")
			out_packet["direction"] = self.configurator.getProperty("MESSAGE_DIRECTION_RESPONSE")

			original_packet = d["packets"][i]
			original_packet = self.stripImageRequest(original_packet)
			original_packet["type"] = self.configurator.getProperty("MESSAGE_TYPE_OUT")
			out_packets.append(original_packet)

			out_packets.append(out_packet)

		d_out_stream = {}
		d_out_stream["packets"] = out_packets

		out_stream = json.dumps(d_out_stream)

		self.ready = True

		print(f"inside processImageStream: after stream = {out_stream}")

		return out_stream

	def isReady(self):
		return self.ready