class Trigger(object):

	def __init__(self, pattern, function, group=None, omit=False, enabled=True):
		self.pattern = pattern
		self.function = function
		self.group = group
		self.omit = omit
		self.enabled = enabled

	def match(self, line):
		return self.pattern.search(line)
