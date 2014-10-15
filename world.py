import re
from twisted.internet import reactor
import protocol
import connection
import lupa


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
