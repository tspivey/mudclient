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
		open_world = file_menu.Append(wx.ID_OPEN, "&Open...\tCtrl+O")
		quit = file_menu.Append(wx.ID_EXIT, "E&xit")
		menubar.Append(file_menu, "&File")
		self.SetMenuBar(menubar)
		self.Bind(wx.EVT_MENU, self.on_new, new)
		self.Bind(wx.EVT_MENU, self.on_open, open_world)
		self.Bind(wx.EVT_MENU, self.on_quit, quit)
		self.Bind(wx.EVT_CLOSE, self.on_quit)
		self.windows = {}

	def on_quit(self, evt):
		reactor.stop()

	def on_new(self, evt):
		w = world.World()
		frame = SessionFrame(w, self, -1, "Untitled")
		frame.Maximize()
		application.worlds.append(frame)

	def on_open(self, evt):
		dlg = wx.FileDialog(self, "Open", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		if dlg.ShowModal() != wx.ID_OK:
			return
		w = world.World()
		try:
			w.load_config(dlg.GetPath())
		except Exception as e:
			wx.MessageBox(str(e), "Error loading world", style=wx.OK | wx.ICON_ERROR)
			raise
		frame = SessionFrame(w, self, -1, w.config['name'])
		frame.Maximize()
		application.worlds.append(frame)

class SessionFrame(wx.MDIChildFrame):
	def __init__(self, world, parent, *args, **kwargs):
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
		self.world = world
		self.world.write_callback = self.append
		try:
			self.world.load_script_file()
		except Exception as e:
			self.world.write_callback("Error loading script file: %s\n" % e)
			return
		if 'host' in self.world.config and 'port' in self.world.config:
			self.world.connect(self.world.config['host'], self.world.config['port'])

	def on_key(self, evt):
		if evt.GetKeyCode() == 13: #enter
			text = self.input.GetValue().encode('utf-8')
			if text.strip():
				self.world.history.append(text)
				self.history_index = len(self.world.history)
			if text.startswith('$'):
				self.world.runtime.eval(text[1:])
				self.input.Clear()
			else:
				self.world.send(text)
				self.append(text+"\r\n", False)
				self.input.Clear()
		elif evt.GetKeyCode() == wx.WXK_UP:
			self.previous_history()
		elif evt.GetKeyCode() == wx.WXK_DOWN:
			self.next_history()
		else:
			evt.Skip()

	def previous_history(self):
		if len(self.world.history) == 0 or self.history_index == 0:
			return
		self.history_index -= 1
		self.input.SetValue(self.world.history[self.history_index])

	def next_history(self):
		if len(self.world.history) == 0:
			return
		if self.history_index + 1 >= len(self.world.history):
			self.input.Clear()
			self.history_index = len(self.world.history)
			return
		self.history_index += 1
		self.input.SetValue(self.world.history[self.history_index])

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
