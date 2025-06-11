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

	def getProperty(self, key):
		return self.db[key]

	def setProperty(self, key, value):
		print(f"CConfigurator:: Adding key {key} with value {value}")
		self.db[key] = value

	def update(self, message):

		message_str = message["content"]

		try:
			d = json.loads(message_str)

			for key in d.keys():
				self.setProperty(key, d[key]) 
		except:
			print(f"Invalid JSON string for Configurator::update: {message_str}")
			return None
