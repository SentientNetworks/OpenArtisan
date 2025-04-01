import sys, os
import json

from DatabaseDriver import CDatabaseDriver

class CMemoryStore:

	def __init__(self, config):
		self.configurator = config
		self.driver = CDatabaseDriver()
		self.database = {}		

		try:

			db = self.driver.get_database("artisan")
			if db is None:
				db = self.driver.create_database("artisan")
				if db is None:
					print(f"CMemoryStore::__init__: failed to create database artisan")
				else:			
					print(f"CMemoryStore::__init__: Acquired or created database artisan")	

			for collection in ["messages", "states", "functions", "agents"]:

				self.database[collection] = []

				table = self.driver.get_table(db, collection)
				if table is None:
					table = self.driver.create_table(db, collection)
					if table is None:
						print(f"CMemoryStore::__init__: failed to create collection {collection}")
					else:
						print(f"CMemoryStore::__init__: Acquired or created table {collection} in database artisan")

						dummy_record = {"status" : "initialized"}
						result = table.insert_one(dummy_record)
						print(f"CMemoryStore::__init__: inserted dummy record with id = {result.inserted_id}")
		
		except Exception as e:
			print(f"CMemoryStore::__init__: exception {e}")

		


	def store(self, collection, message, instructions=None):
		# instructions is a dicctionary if it is defined

		self.database[collection].append(message)
		
		# also add the message to the underlying MongoDB store

		try:
			
			if self.driver is not None:
				db = self.driver.get_database("artisan")
				if db is None:
					print(f"CMemoryStore::store: faulty database artisan")
					return False
				
				messages_table = self.driver.get_table(db, collection)
				if messages_table is None:
					print(f"CMemoryStore::store: faulty collection {collection}")
					return False

				dMessage = json.loads(message)
				row_id = self.driver.insert_row(messages_table, dMessage)
				if row_id is None:
					print(f"CMemoryStore::store: faulty insert into collection {collection} in database artisan")
					return False

		except Exception as e:

			print(f"CMemoryStore::store: problem with database: {e}")
			return False

		return True 
		
	def get(self, db_name, collection_name, matching={}):

		query = {}
		projection = {}

		if len(matching) > 0:
			if "query" in matching:
				query = matching["query"]
			if "projection" in matching:
				projection = matching["projection"]

		db = self.driver.get_database(db_name)
		if db is None:
			print(f"CMemoryStore::get: db is None")
			return None
		
		collection = self.driver.get_table(db, collection_name)
		if collection is None:
			print(f"CMemoryStore::get: collection is None")
			return None

		results = self.driver.find_row(collection, query, projection)

		return results
		

