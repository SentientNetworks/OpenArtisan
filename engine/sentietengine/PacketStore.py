class CPacketStore:

	def __init__(self, config):
		self.configurator = config

		self.database = {}

		self.database[self.configurator.getProperty("STORE_QUEUE_IN")] = []
		self.database[self.configurator.getProperty("STORE_QUEUE_OUT")] = []
		self.database[self.configurator.getProperty("STORE_QUEUE_CONFIG")] = []
		self.database[self.configurator.getProperty("STORE_QUEUE_SPECIAL")] = []
		self.database[self.configurator.getProperty("STORE_QUEUE_IMAGE")] = []

	def storePackets(self, packets, instructions=None):
		# instructions is a dicctionary if it is defined

		out_packets = []

		
		for packet in packets:

			# First we place each packet in its relevant datastore by type
			if packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_IN"):
				self.database[self.configurator.getProperty("STORE_QUEUE_IN")].append(packet)
			elif packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_OUT"):
				self.database[self.configurator.getProperty("STORE_QUEUE_OUT")].append(packet)		
			elif packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_CONFIG"):
				self.database[self.configurator.getProperty("STORE_QUEUE_CONFIG")].append(packet)		
			elif packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_SPECIAL"):
				self.database[self.configurator.getProperty("STORE_QUEUE_SPECIAL")].append(packet)		
			elif packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_IMAGE"):
				self.database[self.configurator.getProperty("STORE_QUEUE_IMAGE")].append(packet)		

			if  instructions["type"] == self.configurator.getProperty("MESSAGE_TYPE_IN"):
				if packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_IN") or packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_IMAGE") or packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_CONFIG"):
					out_packets.append(packet)
			elif instructions["type"] == self.configurator.getProperty("MESSAGE_TYPE_OUT"):
				if packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_OUT") or packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_RESPONSE"):
					out_packets.append(packet)

			if packet["type"] == self.configurator.getProperty("MESSAGE_TYPE_STORAGE"):
				out_packets.append(packet)

		return out_packets

