import os
import time
import json

class CAIDriver:

	ready = True

	def __init__(self, config):

		self.ready = True

	def fileUpload(self, stream):

		pass

	def processPrompt(self, user_prompt, system_prompt):

		pass

	def processImagePrompt(self, prompt):

		pass

	def processStream(self, stream):

		pass
	
	def processImageStream(self, in_stream):
		'''
		Generate a set of images from the packets in a stream
		and return as a stream
		'''

		pass

	def isReady(self):
		return self.ready