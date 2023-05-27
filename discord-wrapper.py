#!/usr/bin/env python3

import sys
import asyncio
from discord import app_commands, Message, Intents, Interaction, Client, TextChannel, DMChannel
from handler import Handler
from program import BasicProgram

if len(sys.argv) != 2:
  print("Error: expected bot token as the only argument", file=sys.stderr)
  sys.exit(1)

intents=Intents.default()
intents.messages = True
intents.message_content = True
client = Client(command_prefix='/', intents=intents)
tree = app_commands.CommandTree(client)

handler = Handler()
prog = BasicProgram(handler)
cur_message = None
cur_reader = None

delete_after_timer = 120

@client.event
async def on_ready():
  print(f"Connected as {client.user}")
  
@client.event
async def setup_hook():
  await tree.sync()

async def output_event(line):
  if cur_message:
    await cur_message.edit(content=f"```{prog.output} ```")

async def start(context):
  global cur_reader
  global cur_message

  is_slash_command = isinstance(context, Interaction)

  if prog.is_running():
    prog.stop()

  cur_message = None
  if cur_reader:
    cur_reader.cancel()
    await cur_reader
  cur_reader = None

  response = prog.start()
  cur_message = await (context.channel if is_slash_command else context).send(response)
  cur_reader = asyncio.create_task(prog.queue_reader_loop(callback=output_event))

async def execute(context, command, args=None):
  is_slash_command = isinstance(context, Interaction)
  is_text_command  = isinstance(context, TextChannel) or isinstance(context, DMChannel)

  if is_slash_command:
    await context.response.defer()

  if command != prog.update and not prog.is_running():
    await start(context)
  
  response = None
  if args:
    response = command(*args)
  else:
    response = command()

  if is_text_command:
    if response:
      await context.send(content=response, delete_after=delete_after_timer)
  elif is_slash_command:
    await context.followup.send(content=(response if response else "Done"), ephemeral=True)
  else:
    print(f"Unknown context kind {context}", file=sys.stderr)

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  username = str(message.author)
  user_message = str(message.content)
  channel = message.channel

  match user_message:
    case "/start":
      await start(channel)
    case "/ping":
      await execute(channel, prog.ping)
    case "/update":
      await execute(channel, prog.update)
    case "/quit":
      await execute(channel, prog.quit)
    case "/stop":
      response = prog.stop()
      await channel.send(f"```{response} ```", delete_after=delete_after_timer)
    case _:
      await execute(channel, prog.message, (username, user_message,))

@tree.command(name="start", description="Start the bot")
async def start_command(interaction: Interaction):
  await start(interaction)
  await interaction.response.send_message("Done", ephemeral=True)

@tree.command(name="update", description="Update the bot")
async def update_command(interaction: Interaction):
  await execute(interaction, prog.update)

@tree.command(name="stop", description="Stop the bot")
async def stop_command(interaction: Interaction):
  if not prog.is_running():
    await interaction.response.send_message("Use the `/start` command first!", ephemeral=True)
    return
  response = prog.stop()
  await interaction.response.send_message(f"```{response} ```")

@tree.command(name="ping", description="Send the 'ping' command to the bot")
async def ping_command(interaction: Interaction):
  await execute(interaction, prog.ping)

@tree.command(name="message", description="Send the 'message' command to the bot")
async def message_command(interaction: Interaction, *, text: str):
  await execute(interaction, prog.message, args=(str(interaction.user), text, ))

@tree.command(name="quit", description="Send the 'quit' command to the bot")
async def quit_command(interaction: Interaction):
  await execute(interaction, prog.quit)

if __name__ == "__main__":
  handler.build()
  client.run(sys.argv[1])