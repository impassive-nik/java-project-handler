#!/usr/bin/env python3

import sys
from handler import Config, Handler
from program import BasicProgram

if __name__ == "__main__":
  config = Config()
  handler = Handler(config)
  if config.is_autobuilding():
    handler.build()

  if len(sys.argv) == 2:
    program = sys.argv[1]

    if program == "pong":
      prog = BasicProgram(handler)
      prog.start()

      prog.ping()
      prog.message("User", "Hello world")
      prog.quit()

      prog.stop()

      if prog.output:
        print("output:")
        print(prog.output)
    else:
      print("Unknown program {}".format(program), file=sys.stderr)
  else:
    handler.run()
