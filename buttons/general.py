import datetime

import nextcord
from nextcord.ui import View, Select, Modal, Button, button, TextInput, Item
from nextcord.utils import find
from nextcord import ButtonStyle, Interaction, Embed, Role, Emoji, PermissionOverwrite, Guild, SelectOption, \
    TextChannel, TextInputStyle, ChannelType
from database import sql
from sys import exc_info
from nextcord.ext import menus
from nextcord import Client


async def guild_embed(bot: Client, guild: Guild, sql_guild, current_page=None, max_pages=None):
    embed = Embed(color=0x2f3136)
    if guild is None:
        embed.title = 'Error'
    else:
        embed.title = 'О городе:'
        embed.description = ''
        embed.set_author(name=guild.name,
                         url=f'https://discord.gg/{sql_guild["invite"]}',
                         icon_url=guild.icon.url if guild.icon is not None else None)
        embed.set_footer(text=guild.id)
        embed.add_field(name='Кол-во жителей:', value=len(guild.get_role(sql_guild['citizen_role_id']).members))
        embed.add_field(name='Ссылка на дискорд сервер города:', value=f'https://discord.gg/{sql_guild["invite"]}')
        if guild.banner is not None:
            embed.image.url = guild.banner.url
    return embed


class GuildPages(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries):
        print('1', entries)
        for entry in [entries]:
            print('2', entry)
            guild = menu.bot.get_guild(entry['guild_id'])
            print('guild.id', entry['guild_id'])
            return await guild_embed(bot=menu.bot,
                               guild=guild,
                               sql_guild=sql.get_guild(entry['guild_id']),
                               current_page=menu.current_page,
                               max_pages=self.get_max_pages())
            # TODO
            # return await guild_embed(menu.bot,
            #
            #                          current_page=menu.current_page,
            #                          max_pages=self.get_max_pages())


class TaskPages(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries):
        print('1', entries)
        for entry in [entries]:
            print('2', entry)
            guild = menu.bot.get_guild(entry['guild_id'])
            print('guild.id', entry['guild_id'])
            return await guild_embed(bot=menu.bot,
                               guild=guild,
                               sql_task=sql.get_tasks_by_customer_id(entry['guild_id']),
                               current_page=menu.current_page,
                               max_pages=self.get_max_pages())
            # TODO
            # return await guild_embed(menu.bot,
            #
            #                          current_page=menu.current_page,
            #                          max_pages=self.get_max_pages())


class GuildsMenuPages(menus.ButtonMenuPages, inherit_buttons=False):
    def __init__(self, source, timeout=300):
        super().__init__(source, timeout=timeout, disable_buttons_after=True)
        self.add_item(menus.MenuPaginationButton(emoji=self.FIRST_PAGE))
        self.add_item(menus.MenuPaginationButton(emoji=self.PREVIOUS_PAGE))
        self.add_item(menus.MenuPaginationButton(emoji=self.NEXT_PAGE))
        self.add_item(menus.MenuPaginationButton(emoji=self.LAST_PAGE))
        # self.add_item(Button(label='Перейти на сервер', emoji='➡️', style=ButtonStyle.url, row=0,
        #                      url=f'{}'))
        self._disable_unavailable_buttons()

    # @button(emoji="➡️", label="Перейти", row=1, style=ButtonStyle.blurple)
    # async def stop_button(self, button, interaction: Interaction):
    #     for embed in interaction.message.embeds:
    #
    #         thread_id: int = embed.url.split('/')[-1]
    #         print(f'thread_id `{thread_id}`')
    #         cur = sql.get_order_by_thread_id(thread_id)
    #         if cur[7] in ['in-progress', 'waiting-approve']:
    #             print('cur', cur)
    #             sql.courier_cancel_order(thread_id=embed.url.split('/')[-1])
    #             message = await interaction.guild.get_channel(
    #                 1074054912847126608).fetch_message(sql.get_order_by_thread_id(thread_id)[0])
    #             await message.edit(view=Orders())
    #             thread = interaction.guild.get_thread(int(thread_id))
    #             await thread.send(f'`{interaction.user.display_name}` ({interaction.user.mention}) отказался от вашего заказа.')
    #             await thread.remove_user(interaction.user)
    #             await interaction.response.send_message("Вы отказались от заказа.", ephemeral=True)
    #     self.stop()

    # @button(emoji="👋", label="", row=1, style=ButtonStyle.url)
    # async def accept_button(self, button, interaction: Interaction):
    #     for embed in interaction.message.embeds:
    #         guild = interaction.client.get_guild(int(embed.footer.text))
    #         sql_guild = sql.get_guild(guild.id)
    #         sql_recruiting = sql.get_recruiting(guild.id)
    #         resume_channel = guild.get_channel(sql_recruiting['resume_channel_id'])
    #         resume_fields = sql.get_resume_fields_order_by_row(guild.id)
    #         from buttons.applications import RecruitingModal
    #         await interaction.response.send_modal(RecruitingModal(interaction.guild, preview=False,
    #                                                               interaction=interaction))
            # thread_id = embed.url.split('/')[-1]
            # cur = sql.get_order_by_thread_id(embed.url.split('/')[-1])
            # if cur[7] == 'in-progress':
            #     sql.courier_done(thread_id=thread_id)
            #     await interaction.guild.get_thread(thread_id).send(
            #         f' `{interaction.user.nick}` ({interaction.user.mention}) доставил ваш заказ!')
            #     await interaction.response.send_message("Вы доставили заказ.", ephemeral=True)
            #     await interaction.guild.get_channel(1074054912847126608).get_thread(cur[1]).send(
            #         f"{interaction.guild.get_member(cur[2]).mention},"
            #         f" курьер {interaction.guild.get_member(cur[3]).mention}"
            #         f" доставил ваш заказ `{cur[5]}` по адрессу `{cur[6]}`"
            #         f"\nПожалуйста, нажмите кнопку подтвердить, если курьер действительно доставил заказ!"
            #     )
        # self.stop()
        # self.check_buttons(self.current_page)

    # def check_buttons(self, page) -> [bool, bool]:
    #     order = sql.get_guilds()[page]
    #     if order == 'waiting-approve':
    #         self.accept_button.disabled = True
    #     elif order == 'completed':
    #         self.accept_button.disabled = True
    #         self.stop_button.disabled = True
    #     else:
    #         self.accept_button.disabled = False
    #         self.stop_button.disabled = False
    #     return self.accept_button.disabled, self.stop_button.disabled


class BotPanelButtons(View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ModuleChoice())

    @button(label='Обновить', emoji='🔃', style=ButtonStyle.blurple, row=2, custom_id='settings_panel_update')
    async def update(self, button: Button, interaction: Interaction):
        print('updating panel')
        try:
            from handler import update_panel, Check
            channel = interaction.guild.get_channel(interaction.channel.id)
            await Check(interaction.client, interaction.guild).comparison_database_to_guild(interaction, channel,
                                                                                            interaction.message)
            await update_panel(interaction.client, interaction.guild)
            await interaction.message.edit(view=BotPanelButtons())
            # await interaction.edit(embeds=embeds, view=BotPanelButtons())
        except Exception as e:
            raise f"Update Exception {e}"


class HelpButtons(View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpChoice())

    # @button(label='Набор в город', emoji='👋', style=ButtonStyle.blurple, row=1, custom_id='application_to_city')
    # async def application_to_city(self, button: Button, interaction: Interaction):
    #     from handler import update_applications_panel
    #     sql_recruiting = sql.get_recruiting(interaction.guild.id)
    #     embeds = [await update_applications_panel(interaction.client, interaction.guild)]
    #     if sql_recruiting:
    #         await interaction.response.send_message(embeds=embeds,
    #                                                 view=ApplicationToCityButtons(interaction=interaction),
    #                                                 ephemeral=True)
    #         #  TODO
    #     else:
    #         await interaction.send(content=f'Модуль `Набор в город` для `{interaction.guild.name}` ещё не установлены',
    #                                embeds=embeds,
    #                                view=CreateRecruiting(interaction),
    #                                ephemeral=True)
        # await interaction.response.send_modal(application_to_city_modal(guild=interaction.guild))


class HelpChoice(Select):

    def __init__(self):
        select_options = [
            SelectOption(
                label=f'Хочу в город',
                description=f'Список городов.',  # TODO
                emoji='👋',
                value=f'help_city_list'),
            SelectOption(
                label=f'Нужна работа.',
                description=f'IN DEV.',  # TODO
                emoji='📌',
                value=f'help_tasks_list')]

        super().__init__(placeholder="Выбери чем тебе помочь.",
                         min_values=1,
                         max_values=1,
                         options=select_options,
                         custom_id='HelpChoice',
                         row=0)

    async def callback(self, interaction: Interaction):
        await interaction.edit(view=HelpButtons())
        if self.values[0] == 'help_city_list':
            data: dict = sql.get_recruiting_where_status_true()
            print('2', data)
            for index, d in enumerate(data):
                print('3', d)
                if not interaction.client.get_guild(d['guild_id']):
                    print('4', d)
                    print(5, data)
                    del data[index]
                    print(6, d)
                    print(7, data)
            print(data)
            print(type(data))
            pages = GuildsMenuPages(source=GuildPages(list(data)))
            print(interaction.data)
            await pages.start(interaction=interaction, ephemeral=True, channel=interaction.user.dm_channel)
        elif self.values[0] == 'help_tasks_list':
            await interaction.send(ephemeral=True, content='in dev...')


class ModuleChoice(Select):

    def __init__(self):
        select_options = [
            SelectOption(
                label=f'Заявки в город',
                description=f'Модуль заявок в город.',  # TODO
                emoji='👋',
                value=f'applications'),
            SelectOption(
                label=f'Задания',
                description=f'Модуль заданий.',  # TODO
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
            from buttons.applications import ApplicationToCityButtons, CreateRecruiting
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
        elif self.values[0] == 'tasks':
            sql_guild = sql.get_guild(interaction.guild.id)
            subscription: datetime.date = sql_guild['subscription_expires'] if sql_guild is not None else None
            if sql_guild['subscription_expires'] is not None:
                subscription_expires = subscription.isoformat()
                now = datetime.datetime.utcnow().isoformat()
                if subscription_expires > now:
                    if sql_guild['task_channel_id']:
                        from buttons.tasks import TasksConfig
                        await interaction.send(content=f'Настройка `Заданий` для {interaction.guild.name}!',
                                               view=TasksConfig(),
                                               ephemeral=True) # TODO: normal description
                    else:
                        from buttons.tasks import TasksModuleSetup
                        embed = Embed(title='')
                        await interaction.send(content=f'Установка модуля `Задания` для {interaction.guild.name}!',
                                               view=TasksModuleSetup(),
                                               ephemeral=True) # TODO: normal description
                else:
                    await interaction.send(content=f'Похоже у вас закончилась подписка :( {subscription_expires}',
                                           ephemeral=True) # TODO: normal description
            else:
                await interaction.send(content=f'Похоже у вас нету подписки :(',
                                       ephemeral=True) # TODO: normal description
        elif self.values[0] == 'citizens':
            await interaction.send(content=f'Модуль `Список жителей` ещё в разработке!',
                                   ephemeral=True)
        await interaction.message.edit(view=BotPanelButtons())
