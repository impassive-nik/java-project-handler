#!/usr/bin/env python3

import sys
from discord import app_commands, Intents, Interaction, Client, TextChannel, DMChannel
from handler import Handler
from program import BasicProgram

if len(sys.argv) != 2:
  print("Error: expected bot token as the only argument", file=sys.stderr)
  sys.exit(1)

intents=Intents.default()
client = Client(command_prefix='/', intents=intents)
tree = app_commands.CommandTree(client)

handler = Handler()
prog = BasicProgram(handler)

@client.event
async def on_ready():
  print(f"Connected as {client.user}")

async def execute(context, command):
  response = None
  if command != prog.start and command != prog.update and not prog.is_running():
    response = "Use the `/start` command first!"
  else:
    response = command()

  if isinstance(context, TextChannel) or isinstance(context, DMChannel):
    if response:
      await context.send(response)
  elif isinstance(context, Interaction) and response:
    if response:
      await context.response.send_message(response)
    else:
      await context.response.defer()
  else:
    print(f"Unknown context kind {context}")

@client.event
async def on_message(message):
  if message.author == client.user:
      return

  username = str(message.author)
  user_message = str(message.content)
  channel = message.channel

  match user_message:
    case "/start":
      await execute(channel, prog.start)
    case "/ping":
      await execute(channel, prog.ping)
    case "/update":
      await execute(channel, prog.update)
    case "/quit":
      await execute(channel, prog.quit)
    case "/stop":
      prog.end()
      await channel.send(f"```{prog.out} ```\n```{prog.err} ```")
    case _:
      print(f'{username} said: "{user_message}" ({channel})')

@tree.command(name="start", description="Start the bot")
async def start_command(interaction: Interaction):
  await execute(interaction, prog.start)

@tree.command(name="update", description="Start the bot")
async def update_command(interaction: Interaction):
  await execute(interaction, prog.update)

@tree.command(name="ping", description="Send the 'ping' command to the bot")
async def ping_command(interaction: Interaction):
  await execute(interaction, prog.ping)

@tree.command(name="quit", description="Send the 'quit' command to the bot")
async def quit_command(interaction: Interaction):
  await execute(interaction, prog.quit)

@tree.command(name="stop", description="Stop the bot")
async def stop_command(interaction: Interaction):
  if not prog.is_running():
    await interaction.response.send_message("Use the `/start` command first!")
    return
  prog.end()
  await interaction.response.send(f"```{prog.out}```\n```{prog.err}```")

if __name__ == "__main__":
  handler.build()
  client.run(sys.argv[1])