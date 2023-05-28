#!/usr/bin/env python3

import sys
import asyncio
from discord import app_commands, Message, Intents, Interaction, Client, TextChannel, DMChannel
from handler import Handler
from program import MessageBasedProgram

if len(sys.argv) != 2:
  print("Error: expected bot token as the only argument", file=sys.stderr)
  sys.exit(1)

intents=Intents.default()
intents.messages = True
intents.message_content = True
client = Client(command_prefix='/', intents=intents)
tree = app_commands.CommandTree(client)

handler = Handler()

class Session:
  def __init__(self, handler: Handler, channel):
    self.prog: MessageBasedProgram = MessageBasedProgram(handler)
    self.channel = channel
    self.log_message: Message = None
    self.cur_reader = None

  async def output_event(self, line):
    if self.log_message:
      await self.log_message.edit(content=f"```{self.prog.output} ```")

  async def message_event(self, line):
    if self.channel:
      await self.channel.send(content=line)

  async def start(self, context):
    is_slash_command = isinstance(context, Interaction)

    if self.prog.is_running():
      self.prog.stop()

    self.log_message = None
    if self.cur_reader:
      self.cur_reader.cancel()
      await self.cur_reader
    self.cur_reader = None

    response = self.prog.start()
    if is_slash_command:
      self.log_message = await context.channel.send(response)
    else:
      self.log_message = await context.send(response)
    self.cur_reader = asyncio.create_task(self.prog.queue_reader_loop(callback=self.output_event, message_callback=self.message_event))

sessions = {}

def get_session(channel, create_if_not_exists = True) -> Session:
  if channel.id in sessions:
    return sessions[channel.id]
  if create_if_not_exists:
    sessions.update({channel.id: Session(handler, channel)})
    return sessions[channel.id]
  return None

delete_after_timer = 120

@client.event
async def on_ready():
  print(f"Connected as {client.user}")
  
@client.event
async def setup_hook():
  await tree.sync()

async def execute(context, command, args=None):
  is_slash_command = isinstance(context, Interaction)
  is_text_command  = isinstance(context, TextChannel) or isinstance(context, DMChannel)

  if is_slash_command:
    await context.response.defer(ephemeral=True)
    session = get_session(context.channel)
  else:
    session = get_session(context)

  if command != session.prog.update and not session.prog.is_running():
    await session.start(context)
  
  response = None
  if args:
    response = command(*args)
  else:
    response = command()

  if is_text_command:
    if response:
      await context.send(content=response, delete_after=delete_after_timer)
  elif is_slash_command:
    if response:
      await context.followup.send(content=response)
    else:
      await context.followup.send(content="Done")
  else:
    print(f"Unknown context kind {context}", file=sys.stderr)

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  username = str(message.author)
  user_message = str(message.content)
  channel = message.channel

  session = get_session(channel)

  match user_message:
    case "/start":
      await session.start(channel)
    case "/ping":
      await execute(channel, session.prog.ping)
    case "/update":
      await execute(channel, session.prog.update)
    case "/quit":
      await execute(channel, session.prog.quit)
    case "/stop":
      response = session.prog.stop()
      await channel.send(f"```{response} ```", delete_after=delete_after_timer)
    case _:
      await execute(channel, session.prog.message, (username, user_message,))

@tree.command(name="start", description="Start the bot")
async def start_command(interaction: Interaction):
  session = get_session(interaction.channel)
  await session.start(interaction)
  await interaction.response.send_message("Done", ephemeral=True)

@tree.command(name="update", description="Update the bot")
async def update_command(interaction: Interaction):
  session = get_session(interaction.channel)
  await execute(interaction, session.prog.update)

@tree.command(name="stop", description="Stop the bot")
async def stop_command(interaction: Interaction):
  session = get_session(interaction.channel)
  if not session.prog.is_running():
    await interaction.response.send_message("Use the `/start` command first!", ephemeral=True)
    return
  response = session.prog.stop()
  await interaction.response.send_message(f"```{response} ```")

@tree.command(name="ping", description="Send the 'ping' command to the bot")
async def ping_command(interaction: Interaction):
  session = get_session(interaction.channel)
  await execute(interaction, session.prog.ping)

@tree.command(name="message", description="Send the 'message' command to the bot")
async def message_command(interaction: Interaction, *, text: str):
  session = get_session(interaction.channel)
  await execute(interaction, session.prog.message, args=(str(interaction.user), text, ))

@tree.command(name="quit", description="Send the 'quit' command to the bot")
async def quit_command(interaction: Interaction):
  session = get_session(interaction.channel)
  await execute(interaction, session.prog.quit)

if __name__ == "__main__":
  handler.build()
  client.run(sys.argv[1])