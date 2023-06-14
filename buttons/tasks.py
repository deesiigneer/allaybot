import nextcord
from nextcord.ui import View, Select, Modal, Button, button, TextInput, Item
from nextcord.utils import find
from nextcord import ButtonStyle, Interaction, Embed, Role, Emoji, PermissionOverwrite, Guild, SelectOption, \
    TextChannel, TextInputStyle, ChannelType, ForumTag, SortOrderType
from database import sql
from sys import exc_info


class TasksModule(View):
    def __init__(self, interaction: Interaction = None):
        super().__init__(timeout=None)
        self.interaction = interaction if interaction is not None else None
        self.sql_recruiting = None
        if self.interaction is not None:
            self.sql_recruiting = sql.get_recruiting(self.interaction.guild.id)

    @button(label='Установка модуля [Задания]', style=ButtonStyle.blurple, row=1, custom_id='tasks_installation')
    async def tasks_installation(self, btn: Button, interaction: Interaction):
        if 'COMMUNITY' in interaction.guild.features:
            # button.disabled = True
            # self.extended_installation.disabled = True
            # await interaction.edit(view=self)
            btn.disabled = True
            # self.extended_installation.disabled = True
            await interaction.edit(view=self)
            sql_guild = sql.get_guild(interaction.guild.id)
            if sql_guild:
                if sql_guild[2] is not None:
                    embed = Embed(title=f'Задания города {interaction.guild.name}!',
                                  description=f'Нажмите кнопку ниже и заполните форму, для подачи заявки в замечательный '
                                              f'город **{interaction.guild.name}**!',
                                  color=0x2f3136)
                    if interaction.guild.icon is not None:
                        embed.set_thumbnail(url=interaction.guild.icon.url)
                    else:
                        embed.set_thumbnail('https://static.wikia.nocookie.net/minecraft_gamepedia/images/4/45/Allay_JE2.gif')
                    if interaction.guild.banner is not None:
                        embed.set_image(url=interaction.guild.banner.url)
                    embed.set_author(name=f'powered by {interaction.client.user.name}',
                                     icon_url=interaction.client.user.avatar.url,
                                     url='https://discord.gg/VbyHaKRAaN')
                    citizen = interaction.guild.get_role(sql_guild[2])
                    overwrites = {interaction.guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
                                  interaction.guild.me: nextcord.PermissionOverwrite(read_messages=True),
                                  citizen: nextcord.PermissionOverwrite(
                                        read_messages=True,
                                        read_message_history=True,
                                        send_messages=False,
                                        view_channel=True)}
                    tasks_category = await interaction.guild.create_category('🔨Задания')
                    forum_tags = [ForumTag(name='Глобальные заказы', moderated=True, emoji='🌐'),
                                  ForumTag(name='Ожидают', moderated=True, emoji='⏳'),
                                  ForumTag(name='В процессе', moderated=True, emoji='💪'),
                                  ForumTag(name='Выполненые', moderated=True, emoji='✔')]
                    tasks_channel = await tasks_category.create_forum_channel(
                        name='🧱Задания',
                        topic=f'TPOQWEKQPODIQWPODIQJODIWJQDPOIQJWPOIDQJWPODIJQWODJQWPOIDJQIOWDJQPOWIDJIQWJD',
                        overwrites=overwrites,
                        available_tags=forum_tags,
                        default_reaction='🔨',
                        default_sort_order=SortOrderType.creation_date)
                    print(f'tasks_channel.tags - {tasks_channel.available_tags}')
                    # recruiting_message = await tasks_channel.send(embed=embed,
                    #                                                    view=ButtonRecruiting(interaction.guild))
                    # sql.add_recruiting(interaction.guild.id, recruiting_channel.id, recruiting_message.id, resume_channel.id,
                    #                    False)
                    # sql_resume = sql.get_resume_fields_order_by_row(interaction.guild.id)
                    # print('sql_resume', sql_resume)
                    # if not sql_resume:
                    #     sql.add_resume_field(interaction.guild.id, 'nickname', 'deesiigneer', False, True, 0)
                    # await recruiting_message.edit(view=ButtonRecruiting(interaction.guild))
                    # await interaction.send(f'Были созданы каналы:\n'
                    #                        f'{recruiting_channel.mention} - о городе, где находится кнопка для подачи '
                    #                        f'заявки в город {interaction.guild.name}\n'
                    #                        f'{resume_channel.mention} - где будут собираться заявки\n\n'
                    #                        f'Нажмите кнопку "👋 Набор в город", что бы продолжить редактирование.', ephemeral=True)
                else:
                    await interaction.send(f'Роль жителя не установлена для города {interaction.guild.name}!\n\n'
                                           f'Что бы установить используйте `/citizen`',
                                           ephemeral=True)
        else:
            await interaction.send(f'На вашем сервере не включен режим `Сообщество`', ephemeral=True)


class TasksAccept(View):

    def __init__(self):
        super().__init__(timeout=None)

    @button(label='Принять', emoji='👋', style=ButtonStyle.green, row=1, custom_id='task_accept')
    async def task_accept(self, button: Button, interaction: Interaction):
        pass


class ModuleChoice(Select):

    def __init__(self):
        select_options = [
            SelectOption(
                label=f'Заявки в город',
                description=f'Модуль заявок в город',  # TODO
                emoji='👋',
                value=f'applications'),
            SelectOption(
                label=f'Задания',
                description=f'IN DEV',  # TODO
                emoji='📌',
                value=f'tasks'),
            SelectOption(
                label=f'Список жителей',
                description=f'IN DEV',  # TODO
                emoji='😇',
                value=f'citizens')]

        super().__init__(placeholder="Выбери модуль",
                         min_values=1,
                         max_values=1,
                         options=select_options,
                         custom_id='ModuleChoice',
                         row=0)

    async def callback(self, interaction: Interaction):
        from handler import Check
        if self.values[0] == 'applications':
            from handler import update_applications_panel
            sql_recruiting = sql.get_recruiting(interaction.guild.id)
            embeds = [await update_applications_panel(interaction.client, interaction.guild)]
            from buttons.requests_to_city import ApplicationToCityButtons, CreateRecruiting
            if sql_recruiting:
                await interaction.response.send_message(embeds=embeds,
                                                        view=ApplicationToCityButtons(interaction=interaction),
                                                        ephemeral=True)
                #  TODO
            else:
                await interaction.send(content=f'Модуль `Набор в город` для `{interaction.guild.name}` ещё не установлены',
                                       embeds=embeds,
                                       view=CreateRecruiting(interaction),
                                       ephemeral=True)
        elif self.values[0] == 'tasks':
            await interaction.send(content=f'Модуль `Заданий` ещё в разработке!',
                                   ephemeral=True)
        elif self.values[0] == 'citizens':
            await interaction.send(content=f'Модуль `Список жителей` ещё в разработке!',
                                   ephemeral=True)
        await interaction.message.edit(view=BotPanelButtons())
