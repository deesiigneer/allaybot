import nextcord
from nextcord.ui import View, Select, Modal, Button, button, TextInput, Item
from nextcord.utils import find
from nextcord import ButtonStyle, Interaction, Embed, Role, Emoji, PermissionOverwrite, Guild, SelectOption, \
    TextChannel, TextInputStyle, ChannelType
from database import sql
from sys import exc_info


async def module_callback(interaction: Interaction):
    from handler import update_applications_panel
    sql_recruiting = sql.get_requests(interaction.guild.id)
    embeds = [await update_applications_panel(interaction.client, interaction.guild)]
    from modules.requests.buttons import ApplicationToCityButtons, CreateRecruiting
    if sql_recruiting:
        await interaction.response.send_message(embeds=embeds,
                                                view=ApplicationToCityButtons(interaction=interaction),
                                                ephemeral=True)
        #  TODO
    else:
        await interaction.send(content=f'Модуль `Набор в город` для `{interaction.guild.name}` ещё не установлен',
                               embeds=embeds,
                               view=CreateRecruiting(interaction),
                               ephemeral=True)


label = 'Заявки в город.'
description = 'Модуль заявок в город.'
emoji = '👋'
value = 'applications'
