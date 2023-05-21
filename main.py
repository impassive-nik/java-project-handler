#!/usr/bin/env python3

import sys
from handler import Handler
from program import BasicProgram

if __name__ == "__main__":
  handler = Handler()
  handler.build()

  if len(sys.argv) == 2:
    program = sys.argv[1]

    if program == "pong":
      prog = BasicProgram(handler)
      prog.start()

      prog.ping()
      prog.ping()
      prog.ping()
      prog.quit()

      prog.end()

      if prog.out:
        print("stdout:")
        print(prog.out)

      if prog.err:
        print("stderr:")
        print(prog.err)
    else:
      print("Unknown program {}".format(program), file=sys.stderr)
  else:
    handler.run()
