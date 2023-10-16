import nextcord
from nextcord.ui import View, Select, Modal, Button, button, TextInput, Item
from nextcord.utils import find
from nextcord import ButtonStyle, Interaction, Embed, Role, Emoji, PermissionOverwrite, Guild, SelectOption, \
    TextChannel, TextInputStyle, ChannelType
from database import sql
from sys import exc_info


async def module_callback(interaction: Interaction):
    from main_buttons import BotPanelButtons
    await interaction.edit(view=BotPanelButtons())
    from modules.tasks.buttons import TasksModuleSetup, TasksConfig
    sql_guild = sql.get_guild(interaction.guild.id)
    if sql_guild['task_channel_id']:
        recruiting_channel = None
        resume_channel = None
        status = False
        recruiting_message = None
        # sql_task: list = sql.get_tasks_count(interaction.guild.id)
        # await Check(bot, guild).channels_exist()
        if sql_guild['task_channel_id'] is not None:
            task_channel = interaction.guild.get_channel(sql_guild['task_channel_id'])
            task_thread = task_channel.get_thread(sql_guild['task_issue_thread_id'])
            task_tag_global_id = sql_guild['task_tag_global_id']
            task_tag_waiting_id = sql_guild['task_tag_waiting_id']
            task_tag_in_progress_id = sql_guild['task_tag_in_progress_id']
            task_tag_complete_id = sql_guild['task_tag_complete_id']
            task_webhook_url =  sql_guild['task_webhook_url']
        # disabled_emoji: Emoji = interaction.client.get_emoji(1038421382477922384)
        enabled_emoji: Emoji = interaction.client.get_emoji(1038421381085401088)
        embed = Embed(title=f'Настройка заданий для города `{interaction.guild.name}` {enabled_emoji}',
                      description=f'**```description```**',
                      color=0x2f3136)
        embed.set_thumbnail('https://static.wikia.nocookie.net/minecraft_gamepedia/images/4/45/Allay_JE2.gif')
        # todo проверка на валидный инвайт
        embed.add_field(inline=False,
            name='Канал с заданиями',
            value=f'{f"{task_channel.mention}" if task_channel.mention is not None else "*Не установлен*"}')
        embed.add_field(inline=False,
            name='Тред с оформлением заданий',
            value=f'{f"{task_thread.mention}" if task_thread.mention is not None else "*Не установлен*"}')
        embed.add_field(inline=False,
            name='ID тэгов в канале заданий',
            value=f'**[in dev]** Глобальные - `{task_tag_global_id}\n`'
                  f'Ожидают - `{task_tag_waiting_id}`\n'
                  f'В процессе - `{task_tag_in_progress_id}`\n'
                  f'Выполненные - `{task_tag_complete_id}`')
        embed.add_field(inline=False,
            name='**[in dev]** Webhook.',
            value=f'||{task_webhook_url}||')
        await interaction.send(embed=embed, view=TasksConfig(), ephemeral=True)
    else:
        await interaction.send(content=f'Модуль `Набор в город` для `{interaction.guild.name}` ещё не установлен',
                               view=TasksModuleSetup(interaction),
                               ephemeral=True)

label = 'Задания.'
description = 'Модуль заданий.'
emoji = '📌'
value = 'tasks'

