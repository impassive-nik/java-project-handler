import asyncio
import threading
from queue import Queue
from handler import Handler

class BasicProgram:
  def __init__(self, handler: Handler):
    # Handler providing methods for updating, building and running the underlying java project
    self.handler = handler
    # Underlying program, returned by the self.handler.run()
    self.prog = None
    # A separate thread which reads lines of text from self.prog and puts it into output_queue
    self.reader_thread = None
    # A queue of lines, produced by the underlying program
    self.output_queue = None
    # Whole output of the program
    self.output = ""
  
  def is_running(self):
    return self.prog is not None
  
  def _reader_loop(self):
    while True:
      line = self.prog.stdout.readline()
      if not line:
        break
      line = line.rstrip()
      self.output_queue.put(line)
  
  async def queue_reader_loop(self, delay : int = 1, callback = None):
    while True:
      if not self.output_queue:
        break
      while not self.output_queue.empty():
        line = self.output_queue.get_nowait()
        self.output += line + "\n"
        if callback:
          await callback(line)
      await asyncio.sleep(delay)
  
  def start(self, use_reader_thread = True):
    if self.is_running():
      return None
    
    self.output = ""
    self.prog = self.handler.popen(merge_stderr=True)

    if use_reader_thread:
      self.output_queue = Queue()
      self.reader_thread = threading.Thread(target=self._reader_loop)
      self.reader_thread.start()

    return "The bot is online now"
  
  def stop(self):
    if not self.prog:
      return None
    
    out, err = self.prog.communicate()

    if self.reader_thread:
      self.reader_thread.join()
      self.reader_thread = None
      
    self.prog = None

    while self.output_queue and not self.output_queue.empty():
      self.output += self.output_queue.get() + "\n"
    self.output_queue = None

    if out:
      self.output += out
    if err:
      self.output += err
    return self.output

  def write(self, line):
    if self.prog:
      self.prog.stdin.write(line + "\n")
      self.prog.stdin.flush()
  
  def update(self):
    self.stop()
    self.handler.update()
    self.handler.build()
    return "The bot was updated"
  
  def ping(self):
    self.write("ping")
    return None
  
  def message(self, sender : str, text : str):
    self.write("message")
    self.write(sender.split("\n")[0])
    self.write(text.split("\n")[0])
    return None
  
  def quit(self):
    self.write("quit")
    return None