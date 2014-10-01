from twisted.internet.protocol import Factory, Protocol

class Client(Protocol):
	def connectionMade(self):
		print "connected"

	def dataReceived(self, data):
		self.world.handle_data(data)

class ClientFactory(Factory):
	def __init__(self, world, *args, **kwargs):
		self.world = world

	def buildProtocol(self, addr):
		protocol = Client()
		self.world.protocol = protocol
		protocol.world = self.world
		return protocol
