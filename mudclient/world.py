import re
from twisted.internet import reactor
import protocol
import connection
import lupa
import yaml
import os
from triggers import Trigger
import application
import six

class World(object):

	def __init__(self, write_callback=None):
		#The callback called when we need to write a line to the user
		self.write_callback = write_callback
		self.runtime_initializing_callback = None
		self.connection = connection.Connection(self)
		self.init_runtime()
		#Input history, oldest to newest
		self.history = []
		self.config = {}
		self.config_file = None
		self.aliases = []
		self.triggers = []


	def init_runtime(self):
		self.runtime = lupa.LuaRuntime()
		self.runtime.globals()['world'] = self
		self.runtime.globals().send = self.send
		self.runtime.globals().alias = self.alias
		self.runtime.globals().trigger = self.trigger
		self.runtime.globals().output = application.output
		self.runtime.globals()['print'] = self.print_
		if self.runtime_initializing_callback is not None:
			self.runtime_initializing_callback()

	def print_(self, *args):
		s = " ".join([str(a) for a in args])
		self.write_callback(s+"\r\n")

	def reload_runtime(self):
		self.triggers = []
		self.aliases = []
		self.init_runtime()
		self.load_script_file()

	def handle_line(self, line):
		line = line.decode('utf-8')
		line = self.strip_ansi(line)
		matchline = line.rstrip('\n')
		for trigger in self.triggers:
			if not trigger.enabled:
				continue
			match = trigger.match(matchline)
			if match is None:
				continue
			if trigger.function is not None:
				groups = [g or "" for g in match.groups()]
				try:
					trigger.function(self.runtime.table(*groups), matchline)
				except Exception as e:
					self.print("Error calling trigger: " + str(e))
					continue
			if trigger.omit:
				return
			break
		self.write_callback(line)

	ansi_re = re.compile(r'\x1b\[\d+(?:;\d+)?m')
	def strip_ansi(self, line):
		return self.ansi_re.sub('', line)

	def send(self, text):
		if isinstance(text, six.text_type):
			text = text.encode('utf-8')
		self.connection.send(text+b"\n")

	def connect(self, host, port):
		self.connection.connect(host, port)

	def disconnect(self):
		self.connection.disconnect()

	def load_config(self, path):
		self.config_file = os.path.abspath(path)
		with open(path, 'rb') as fp:
			self.config = yaml.safe_load(fp)
		if 'name' not in self.config:
			self.config['name'] = 'Untitled'

	def load_script_file(self):
		script_file = self.config.get('script_file', None)
		if script_file:
			script_file = os.path.join(os.path.dirname(self.config_file), script_file)
		if script_file and os.path.exists(script_file):
			self.runtime.globals().dofile(script_file)

	def input(self, line):
		for match, func in self.aliases:
			res = match.search(line)
			if res:
				#We want a list for translating None into ""
				groups = [g or "" for g in res.groups()]
				func(self.runtime.table(*groups))
				return
		self.send(line)

	def alias(self, match, func):
		match = re.compile(match)
		self.aliases.append((match, func))

	def trigger(self, match, func, options=None):
		pattern = re.compile(match)
		if options is None:
			options = {}
		trigger = Trigger(pattern, func, **options)
		self.triggers.append(trigger)

	def finalize(self):
		self.init_runtime()
		try:
			self.load_script_file()
		except Exception as e:
			self.write_callback("Error loading script file: %s\n" % e)
			return
		if 'host' in self.config and 'port' in self.config:
			self.connect(self.config['host'], self.config['port'])
