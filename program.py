from handler import Handler

class BasicProgram:
  def __init__(self, handler: Handler):
    self.handler = handler
    self.prog = None
    self.out = None
    self.err = None
  
  def is_running(self):
    return self.prog is not None
  
  def start(self):
    restarted = False
    if self.is_running():
      self.end()
      restarted = True
    
    self.out = None
    self.err = None
    self.prog = self.handler.popen()

    return "The bot was restarted" if restarted else "The bot is online now"

  def write(self, line):
    if self.prog:
      self.prog.stdin.write(line + "\n")
      self.prog.stdin.flush()
  
  def end(self):
    if self.prog:
      self.out, self.err = self.prog.communicate()
      self.prog = None
  
  def update(self):
    self.end()
    self.handler.update()
    self.handler.build()
    return "The bot was updated"
  
  def ping(self):
    self.write("ping")
    return None
  
  def quit(self):
    self.write("quit")
    return "The bot is offline now"