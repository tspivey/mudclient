import re
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
import protocol

#Telnet protocol constants
IAC = chr(255)
EOR = chr(239)
SE = chr(240)
GA = chr(249)
SB = chr(250)
WILL = chr(251)
WONT = chr(252)
DO = chr(253)
DONT = chr(254)

class NeedMoreDataException(Exception):
	pass

class Connection(object):

	def __init__(self, world):
		self.world = world
		self.parsed = ""
		#Store the telnet negotiation sequences here until we fully have them
		self.buffer = ""
		#Determines whether we use IAC GA/EOR to delimit prompts.
		#If set, any partial lines will be buffered until we get one.
		self.has_ga = False
		#The factory used for creating new connections
		self.client_factory = protocol.ClientFactory(self)

	def handle_data(self, data):
		"""Handle data received by the MUD."""
		data = self.buffer + data
		self.buffer = ""
		curpos = 0
		while curpos < len(data):
			iacpos = data.find(IAC, curpos)
			if iacpos == -1:
				self.parsed += data[curpos:]
				curpos += len(data[curpos:])
				continue
			#We have an iac in here
			self.parsed += data[curpos:iacpos]
			curpos = iacpos
			try:
				curpos += self.parse_iac(data[curpos:])
			except NeedMoreDataException:
				print "in the middle of iac"
				self.buffer = data[curpos:]
				return
		self.parse_all_data()

	def parse_iac(self, data):
		if len(data) == 1:
			raise NeedMoreDataException()
		if data[1] == IAC:
			self.parsed += IAC
			return 2
		elif data[1] in (GA, EOR):
			print "ga/eor found"
			self.has_ga = True
			self.parse_all_data(True)
			return 2
		elif data[1] in (WILL, WONT, DO, DONT):
			if len(data) < 3:
				raise NeedMoreDataException()
			self.handle_option(data[1], data[2])
			return 3
		elif data[1] == SB:
			pos = data.find(IAC+SE)
			if pos == -1:
				raise NeedMoreDataException()
				return
			self.handle_subnegotiation(data[:pos+2])
			return pos+2
		else: #Don't know what this is
			self.parsed += data[1]
			return 2

	line_re = re.compile(r'\n')
	def parse_all_data(self, force=False):
		"""Handle any unhandled data received from the mud, and send it for further processing.
		If force is True, send it anyway, terminator or not. This is used if we detect a GA."""
		if not self.parsed:
			return
		#Muds send \n\r, get rid of the \r
		self.parsed = self.parsed.replace('\r', '')
		#Split by lines and deal with them
		cur = 0
		for match in self.line_re.finditer(self.parsed):
			line = self.parsed[cur:match.end()]
			self.world.handle_line(line)
			cur = match.end()
		#Now we're left with what's left, the unterminated line.
		#If we do GA, wait until we get one. Otherwise, display it.
		if self.has_ga and not force:
			#Delete everything up to the remaining chunk and exit
			self.parsed = self.parsed[cur:]
			return
		elif cur < len(self.parsed) - 1:
			#Parse the incomplete line
			remaining = self.parsed[cur:]
			self.world.handle_line(remaining)
			cur += len(remaining)
		self.parsed = self.parsed[cur:]

	def handle_subnegotiation(self, data):
		print "hs: %r" % data

	def handle_option(self, type, opt):
		if type == WILL and opt == chr(25):
			self.send(IAC+DO+chr(25))
		print "ok"

	def connect(self, host, port):
		point = TCP4ClientEndpoint(reactor, host, port)
		d = point.connect(self.client_factory)
		d.addErrback(self.connection_failed)

	def connection_failed(self, deferred):
		self.world.write_callback("Failed to connect, reason: %s\n" % deferred.getErrorMessage())

	def send(self, text):
		self.protocol.transport.write(text)

	def on_connect(self):
		self.world.write_callback("connected\n")

	def on_disconnect(self, reason):
		"""Event called when the world disconnected. Clear any
		connection specific data and prepare for another connection."""
		self.parse_all_data(True)
		self.buffer = "" #clear any in-progress IAC sequences
		self.has_ga = False
		self.world.write_callback("Disconnected, reason: %s\n" % reason.getErrorMessage())
