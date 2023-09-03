import nextcord
from nextcord.ui import View, Select, Modal, Button, button, TextInput, Item
from nextcord.utils import find
from nextcord import ButtonStyle, Interaction, Embed, Role, Emoji, PermissionOverwrite, Guild, SelectOption, \
    TextChannel, TextInputStyle, ChannelType
from database import sql
from sys import exc_info


async def module_callback(interaction: Interaction):
    await interaction.send(content=f'Модуль ещё не установлен', ephemeral=True)

label = 'Задания.'
description = 'Модуль заданий.'
emoji = '📌'
value = 'tasks'

