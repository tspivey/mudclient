import re
from twisted.internet import reactor
import protocol
import connection
import lupa
import yaml
import os

class World(object):

	def __init__(self, write_callback=None):
		#The callback called when we need to write a line to the user
		self.write_callback = write_callback
		self.connection = connection.Connection(self)
		#the lua runtime
		self.runtime = lupa.LuaRuntime()
		self.runtime.globals()['world'] = self
		#Input history, oldest to newest
		self.history = []
		self.config = {}


	def handle_line(self, line):
		line = self.strip_ansi(line)
		self.write_callback(line)

	ansi_re = re.compile(r'\x1b\[\d+(?:;\d+)?m')
	def strip_ansi(self, line):
		return self.ansi_re.sub('', line)

	def send(self, text):
		if isinstance(text, unicode):
			text = text.encode('utf-8')
		self.connection.send(text)

	def connect(self, host, port):
		self.connection.connect(host, port)

	def disconnect(self):
		self.connection.disconnect()

	def load_config(self, path):
		with open(path, 'rb') as fp:
			self.config = yaml.safe_load(fp)
		if 'name' not in self.config:
			self.config['name'] = 'Untitled'

	def load_script_file(self):
		script_file = self.config.get('script_file', None)
		if script_file and os.path.exists(script_file):
			self.runtime.globals().dofile(script_file)
