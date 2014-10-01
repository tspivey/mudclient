import application
import wx
from twisted.internet import wxreactor
wxreactor.install()
from twisted.internet import reactor
import world
import protocol

class MainFrame(wx.MDIParentFrame):
	def __init__(self, *args, **kwargs):
		super(MainFrame, self).__init__(*args, **kwargs)
		menubar = wx.MenuBar()
		file_menu = wx.Menu()
		new = file_menu.Append(wx.ID_NEW, "&New")
		quit = file_menu.Append(wx.ID_EXIT, "E&xit")
		menubar.Append(file_menu, "&File")
		self.SetMenuBar(menubar)
		self.Bind(wx.EVT_MENU, self.on_new, new)
		self.Bind(wx.EVT_MENU, self.on_quit, quit)
		self.windows = {}

	def on_quit(self, evt):
		reactor.stop()

	def on_new(self, evt):
		frame = SessionFrame(self, -1, "Untitled")
		frame.Maximize()
		application.worlds.append(frame)

class SessionFrame(wx.MDIChildFrame):
	def __init__(self, parent, *args, **kwargs):
		super(SessionFrame, self).__init__(parent, *args, **kwargs)
		self.parent = parent
		self.input = wx.TextCtrl(self)
		self.output = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(self.output, 8, wx.EXPAND)
		self.sizer.Add(self.input, 1, wx.EXPAND)
		self.SetSizerAndFit(self.sizer)
		#When enter is pressed, don't beep, send input
		self.input.Bind(wx.EVT_KEY_DOWN, self.on_key)
		self.Show(True)
		self.history_index = -1
		self.world = world.World(self.append)

	def on_key(self, evt):
		if evt.GetKeyCode() == 13: #enter
			text = self.input.GetValue().encode('utf-8')
			if text.startswith('$'):
				self.world.runtime.eval(text[1:])
				self.input.Clear()
			else:
				self.world.send(text+"\r\n")
				self.append(text+"\r\n", False)
				self.input.Clear()
		else:
			evt.Skip()

	def append(self, data, speak=True):
		data = data.replace('\r\n', '\n')
		data = data.replace('\n', '\r\n')
		location = self.output.GetInsertionPoint()
		self.output.AppendText(data)
		if self.FindFocus() == self.output:
			self.output.SetInsertionPoint(location)
		if speak and data.strip():
			application.output.speak(data)

def main():
	app = wx.App()
	frame = MainFrame(None, -1, "Client")
	frame.Maximize()
	frame.Show(True)
	reactor.registerWxApp(app)
	reactor.run()

if __name__ == '__main__':
	main()
