from twisted.internet.protocol import Factory, Protocol

class Client(Protocol):

	def __init__(self, connection):
		self.connection = connection

	def connectionMade(self):
		self.connection.on_connect()

	def dataReceived(self, data):
		self.connection.handle_data(data)

	def connectionLost(self, reason):
		self.connection.on_disconnect(reason)

class ClientFactory(Factory):
	def __init__(self, connection, *args, **kwargs):
		self.connection = connection

	def buildProtocol(self, addr):
		protocol = Client(self.connection)
		self.connection.protocol = protocol
		return protocol
