import os, sys
import json

from sentietengine.Configurator import CConfigurator 
from sentietengine.BusinessLogic import CBusinessLogic 
from sentietengine.PacketStore import CPacketStore 
from sentietengine.AIDriver import CAIDriver 

TEST_STREAM = '{"packets": [{ "sender" : "Andrew", "target" : "AI", "message" : "Who are the members of my network?" }, { "sender" : "Bob", "target" : "AI", "message" : "Who are the members of my network?" }, { "sender" : "Andrew2", "target" : "AI", "message" : "Who are the members of my network?" }, { "sender" : "Bob2", "target" : "AI", "message" : "Who are the members of my network?" }, { "sender" : "Andrew", "target" : "AI", "message" : "Who are the members of my network?" }, { "sender" : "Bob", "target" : "AI", "message" : "Who are the members of my network?" }, { "sender" : "Andrew2", "target" : "AI", "message" : "Who are the members of my network?" }, { "sender" : "Bob2", "target" : "AI", "message" : "Who are the members of my network?" }, { "sender" : "Andrew", "target" : "AI", "message" : "Who are the members of my network?" }, { "sender" : "Bob", "target" : "AI", "message" : "Who are the members of my network?" }]}'

class CPacketManager:

	configurator = None
	_instance = None

	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			cls._instance = super().__new__(cls, *args, **kwargs)
		return cls._instance

	def __init__(self, value=None):

		print("CPacketManager.__init__ has been called")
		print()

		self.configurator = CConfigurator()

		if value is not None:
			print("configurator is alive!")

		self.businesslogic = CBusinessLogic(self.configurator)
		self.packetstore = CPacketStore(self.configurator)
		self.driver = CAIDriver(self.configurator)

		self.packet_queue = []
		self.MAX_QUEUE_SIZE = 1

		self.instructions = {}
		self.instructions["type"] = None

	def assemblePacket(self, message):

		packet = {}

		dMessage = json.loads(message)

		# First load in most of the key-value pairs in the original message whatever they are
		for key, value in dMessage.items():

			if key not in [self.configurator.getProperty("MESSAGE_TYPE_NAME"), self.configurator.getProperty("MESSAGE_DIRECTION_NAME"), self.configurator.getProperty("MESSAGE_SOURCE_NAME"),  self.configurator.getProperty("MESSAGE_TARGET_NAME"), self.configurator.getProperty("MESSAGE_AGENTPROMPT_NAME"), self.configurator.getProperty("MESSAGE_CONTENT_NAME")]:

				packet[key] = value

		if self.configurator.getProperty("MESSAGE_TYPE_NAME") in message:

			if (dMessage[self.configurator.getProperty("MESSAGE_TYPE_NAME")] == self.configurator.getProperty("MESSAGE_TYPE_IN")) or (dMessage[self.configurator.getProperty("MESSAGE_TYPE_NAME")] == self.configurator.getProperty("MESSAGE_TYPE_OUT")):
				packet["type"] = self.configurator.getProperty("MESSAGE_TYPE_IN")

			else:
				packet["type"] = dMessage[self.configurator.getProperty("MESSAGE_TYPE_NAME")]

		else:

			packet["type"] = self.configurator.getProperty("MESSAGE_TYPE_IN")

		if self.configurator.getProperty("MESSAGE_DIRECTION_NAME") in message:

			if (dMessage[self.configurator.getProperty("MESSAGE_DIRECTION_NAME")] == self.configurator.getProperty("MESSAGE_DIRECTION_REQUEST")) or (dMessage[self.configurator.getProperty("MESSAGE_DIRECTION_NAME")] == self.configurator.getProperty("MESSAGE_DIRECTION_RESPONSE")):
				packet["direction"] = self.configurator.getProperty("MESSAGE_DIRECTION_REQUEST")

			else:
				packet["direction"] = dMessage[self.configurator.getProperty("MESSAGE_DIRECTION_NAME")]

		else:

			packet["direction"] = self.configurator.getProperty("MESSAGE_DIRECTION_REQUEST")


		packet["source"] = dMessage[self.configurator.getProperty("MESSAGE_SOURCE_NAME")]
		packet["target"] = dMessage[self.configurator.getProperty("MESSAGE_TARGET_NAME")]
		packet["agentprompt"] = dMessage[self.configurator.getProperty("MESSAGE_AGENTPROMPT_NAME")]
		packet["message"] = dMessage[self.configurator.getProperty("MESSAGE_CONTENT_NAME")]
		#packet["response"] = ""		

		# Load in the system blcok from the original message
		if self.configurator.getProperty("MESSAGE_SYSTEMBLOCK_NAME") in dMessage:
			packet["system"] = dMessage[self.configurator.getProperty("MESSAGE_SYSTEMBLOCK_NAME")]

		packet["client_id"] = dMessage["client_id"]
		packet["broadcast"] = dMessage["broadcast"]

		return packet

	def disassemblePacket(self, packet):

		message = {}

		#print(packet)

		for key, value in packet.items():

			if key not in ["type", "direction", "source", "target", "agentprompt", "message", "system"]:

				packet[key] = value


		message[self.configurator.getProperty("MESSAGE_TYPE_NAME")] = packet["type"]
		
		if "direction" in packet:
			message[self.configurator.getProperty("MESSAGE_DIRECTION_NAME")] = packet["direction"]
		else:
			message[self.configurator.getProperty("MESSAGE_DIRECTION_NAME")] = "response"

		message[self.configurator.getProperty("MESSAGE_SOURCE_NAME")] = packet["source"]
		message[self.configurator.getProperty("MESSAGE_TARGET_NAME")] = packet["target"]
		
		message[self.configurator.getProperty("MESSAGE_AGENTPROMPT_NAME")] = ""
		if "agentprompt" in packet:
			message[self.configurator.getProperty("MESSAGE_AGENTPROMPT_NAME")] = packet["agentprompt"]
			
		message[self.configurator.getProperty("MESSAGE_CONTENT_NAME")] = packet["message"]
		#message[self.configurator.getProperty("MESSAGE_RESPONSE_NAME")] = packet["response"]

		print(f"engine::CPacketManager:disassemblePacket: packet = {packet}")

		message[self.configurator.getProperty("MESSAGE_SYSTEMBLOCK_NAME")] = packet["system"]
		
		if "client_id" not in packet:
			message["client_id"] = ""
			message["broadcast"] = True
		else:
			message["client_id"] = packet["client_id"]
			message["broadcast"] = packet["broadcast"]

		message_string = json.dumps(message)
		#print(message)

		return message_string

	def assemblePackets(self, messages):

		packets = []
		for message in messages:
			packet = self.assemblePacket(message)
			packets.append(packet)

		return packets

	def disassemblePackets(self, packets):

		messages = []
		for packet in packets:
			#print(f"Processing packet {packet}")
			message = self.disassemblePacket(packet)
			messages.append(message)

		return messages

	def assembleStream(self, packets):

		d = {}
		d["packets"] = packets
		d["network"] = self.configurator.getProperty("NETWORK_MEMBERS")

		stream = json.dumps(d)

		return stream

	def disassembleStream(self, stream):

		print(f"CPacketManager::disassembleStream: stream = {stream}")
		
		d = json.loads(stream)
		
		print(f"CPacketManager::disassembleStream: d = {str(d)}")

		if type(d) is dict:
			packets = d["packets"]
		elif type(d) is list:
			packets = d 

		out_packets = []
		for packet in packets:
			out_packet = packet
			if "type" not in out_packet or out_packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_IN"):
				out_packet["type"] = self.configurator.getProperty("MESSAGE_TYPE_OUT")

		return packets
	
	def streamContainsType(self, stream, packet_type_str):

		d = json.loads(stream)

		if len(d["packets"]) > 0:

			packet = d["packets"][0]

			if packet["type"] == self.configurator.getProperty(packet_type_str):

				return True
		
		return False
	
	# If any of the packets do not contain a file or there is an exception return False
	def streamContainsFile(self, stream, type_str=None):

		try:
			d = json.loads(stream)

			if len(d["packets"]) > 0:

				result = False
				for packet in d["packets"]:

					if type(packet["message"]) is dict and "filename" in packet["message"] and len(packet["message"]["filename"]) > 0:

						result = True	
						continue

					else:

						result = False
						break

				return result

		except Exception as e:
			print(f"engine::CPacketManager:streamContainsFile: error: {e}")
			return False
				
		return False	
	
	def isGeneralRequest(self, stream):

		return self.streamContainsType(stream, "MESSAGE_TYPE_IN")
	
	def isImageRequest(self, stream):

		return self.streamContainsType(stream, "MESSAGE_TYPE_IMAGE")

	def isConfigRequest(self, stream):

		return self.streamContainsType(stream, "MESSAGE_TYPE_CONFIG")

	def isFileRequest(self, stream):

		return self.streamContainsFile(stream)

	def processStream(self, packets):

		# maintain queue of incoming packets

		# add to the queue
		for packet in packets:
			self.packet_queue.append(packet)

		print(f"Packet Queue is at {len(self.packet_queue)} elements")

		# if the queue is full and the driver is ready
		if (len(self.packet_queue) >= self.MAX_QUEUE_SIZE):
			print(f"Packet Queue is full at {len(self.packet_queue)} elements")

			if self.driver.isReady(): 

				# assemble packets into stream
				stream = self.assembleStream(packets)

				# These three tests check the type parameter of the first
				# packet in the stream. It is assumed for now that there
				# will only be one packet in the stream at this point

				#print(f"Inside PacketManager::processStream stream = {stream}")

				# Upload any files in the stream then continue
				if self.isFileRequest(stream):
					stream = self.driver.fileUpload(stream)

				if self.isGeneralRequest(stream):

					# call sendStream on driver
					response = self.driver.processStream(stream)

				elif self.isConfigRequest(stream):

					# call processStream on driver for now
					response = self.driver.processStream(stream)

				elif self.isImageRequest(stream):

					# call processImage on driver

					#print(f"Inside PacketManager::processStream inside test for ImageRequest")

					response = self.driver.processImageStream(stream)

				else:

					# call sendStream on driver
					response = self.driver.processStream(stream)

				# disassemble the response
				out_packets = self.disassembleStream(response)

				print(f"PacketManager::processStream out_packets={out_packets}")

				# Clear out the queue and reset the maximum 
				self.packet_queue = []
				self.MAX_QUEUE_SIZE = 1

				return out_packets

			# if the driver is not ready
			else:

				# extend the queue
				self.MAX_QUEUE_SIZE += len(packets) + 1

		return []

	def process_messages(self, in_messages):
		'''
		This method is the top level entry point for this class
		PacketManager is the entry point for the engine
		'''
		self.instructions["type"] = self.configurator.getProperty("MESSAGE_TYPE_IN")

		print(in_messages)
		
		in_packets = self.assemblePackets(in_messages)

		print(f"Inside PacketManager::process_messages after assemblePackets in = {in_packets}")		

		checked_packets = self.businesslogic.checkPackets(in_packets, instructions={"in": True})	

		print(f"Inside PacketManager::process_messages in checked_packets = {checked_packets}")		

		stored_packets = self.packetstore.storePackets(checked_packets, self.instructions)

		print(f"Inside PacketManager::process_messages in stored_packets = {stored_packets}")	

		print("Before processStream")
		processed_packets = self.processStream(stored_packets)
		print("After processStream")

		print(f"Inside PacketManager::processMessages processed_packets = {processed_packets}")

		self.instructions["type"] = self.configurator.getProperty("MESSAGE_TYPE_OUT")		

		stored_packets = self.packetstore.storePackets(processed_packets, self.instructions)

		print(f"Inside PacketManager::process_messages out stored_packets = {stored_packets}")

		# TODO: make sure config update doesn't happen twice on input and output
		checked_packets = self.businesslogic.checkPackets(stored_packets, instructions={"in": False})

		print(f"Inside PacketManager::process_messages out checked_packets = {checked_packets}")		

		out_messages = self.disassemblePackets(checked_packets)

		#print(out_messages)

		return out_messages

