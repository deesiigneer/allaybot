import nextcord
import logging
from nextcord.ext import commands
from nextcord.flags import Intents
from nextcord import Permissions, Embed, errors, Interaction, ApplicationError, DMChannel
from os import environ, listdir
from sys import exc_info
from database import sql
from typing import Any
import aiohttp
# from some import Panel

logging.basicConfig(level=logging.WARNING)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.persistent_views_added = False

        for fn in listdir("./cogs"):
            if fn.endswith(".py"):
                self.load_extension(f"cogs.{fn[:-3]}")

    async def on_ready(self):
        if not self.persistent_views_added:
            self.persistent_views_added = True
            from main_buttons import BotPanelButtons, HelpButtons
            from modules.requests.buttons import ButtonRecruiting, CreateRecruiting, ApplicationToCityButtons,\
                ResumeEdit
            from modules.tasks.buttons import TasksModuleSetup, TasksChoice, TasksConfig, TasksAccept, NewTask
            self.add_view(BotPanelButtons())
            self.add_view(HelpButtons())
            # requests
            self.add_view(ButtonRecruiting())
            self.add_view(CreateRecruiting())
            self.add_view(ResumeEdit())
            self.add_view(ApplicationToCityButtons())
            # tasks
            self.add_view(TasksModuleSetup())
            self.add_view(TasksChoice())
            self.add_view(TasksConfig())
            self.add_view(TasksAccept())
            self.add_view(NewTask())
            # self.add_view(ExtendedInstallation())

        sql_guilds = sql.get_guilds()
        guild_db_list = [sql_guild['guild_id'] for sql_guild in sql_guilds]
        print('searchin for guilds not in database')
        for guild in self.guilds:
            if guild.id not in guild_db_list:
                print(f'adding {guild} ({guild.id}) in database')
                await self.on_guild_join(guild)

        await self.change_presence(
            activity=nextcord.Activity(
                type=nextcord.ActivityType.watching,
                name=f"t.me/deesiigneer"),
            status=nextcord.Status.online)
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        # print('guilds in service: ' + str([len(guilds) for guilds in sql.get_guilds()]))
        print(sql.version())
        # await client.sync_all_application_commands()

    async def on_close(self):
        print('CLOSE')
        try:
            sql.close()
        except Exception as e:
            print('on_close error ', e)

    # async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
    #     print(event_method)
    #     print(*args)
    #     print(**kwargs)

    async def on_message(self, message: nextcord.Message) -> None:
        if message.author.bot is False and message.author is not self.user:
            if type(message.channel) == DMChannel:
                if 'помощь' in message.content.lower():
                    guilds = sql.get_guilds
                    from main_buttons import HelpButtons
                    await message.reply(content=f'Привет, {message.author.mention}!\n\n',
                                        view=HelpButtons())
                    # TODO: guilds list
            else: 
                sql_tasks = sql.get_tasks_by_thread_id(message.channel.id)
                channel = await self.fetch_channel(message.channel.id)
                guild = channel.guild
                sql_guild = sql.get_guild(guild.id)
                thread = None
                print(1,sql_tasks['customer_guild_id'])
                print(2,sql_tasks['customer_id'])
                print(3,sql_tasks['customer_thread_message_id'])
                print(4,sql_tasks['contactor_guild_id'])
                print(5,sql_tasks['contactor_id'])
                print(6,sql_tasks['contactor_thread_message_id'])
                if sql_tasks['customer_guild_id'] == guild.id and sql_tasks['customer_id'] == message.author.id and message.channel.id == sql_tasks['customer_thread_message_id']:
                        customer_guild = self.get_guild(sql_tasks['contactor_guild_id'])
                        thread = await customer_guild.fetch_channel(sql_tasks['contactor_thread_id'])
                        sql_guild = sql.get_guild(customer_guild.id)
                elif sql_tasks['contactor_guild_id'] == guild.id and sql_tasks['contactor_id'] == message.author.id and message.channel.id == sql_tasks['contactor_thread_message_id']:
                    contactor_guild = self.get_guild(sql_tasks['customer_guild_id'])
                    thread = await self.fetch_channel(sql_tasks['customer_thread_id'])
                    sql_guild = sql.get_guild(contactor_guild.id)
                print('thread tags',sql_guild['task_tag_global_id'], thread.applied_tag_ids)
                if sql_tasks['global_status'] is True and sql_guild['task_tag_global_id'] in thread.applied_tag_ids:
                    webhook_url = f'{sql_guild["task_webhook_url"]}'
                    async with aiohttp.ClientSession() as session:
                        webhook = nextcord.Webhook.from_url(webhook_url, session=session)
                        from pyspapi import SPAPI, MojangAPI
                        spapi = SPAPI('6273cba5-add3-44b8-a9a6-d528fcf0f29a', 'hQvWsc9FssggbtNXukG/3XbgNXtyTgos')
                        username = spapi.get_user(message.author.id)
                        if username is not None:
                            username = username.username
                            avatar_url = f'https://visage.surgeplay.com/face/512/{MojangAPI.get_uuid(username)}.png'
                        else:
                            username = f'[{self.user.display_name}] - {message.author.name}'
                            avatar_url = self.user.avatar.url
                        await webhook.send(username=username,
                                           avatar_url=avatar_url,
                                           content=message.content,
                                           thread=thread) if thread is not None else print('error') # TODO

    async def on_guild_remove(self, guild: nextcord.Guild):
        log_guild = self.get_guild(850091193190973472)
        log_channel = log_guild.get_channel(1103024684003508274)
        sql.delete_guild(guild.id)
        sql.delete_recruiting(guild.id)
        await log_channel.send(f'Удален из guild: {guild.name} ({guild.id})')

    async def on_guild_join(self, guild: nextcord.Guild):
        log_guild = self.get_guild(850091193190973472)
        log_channel = log_guild.get_channel(1103024684003508274)
        await log_channel.send(f'Добавлен на сервер `{guild.name}` ({guild.id}) \n||{[invite for invite in await guild.invites()]}||')
        await client.sync_application_commands(guild_id=guild.id)
        try:
            guild_bot = guild.get_member(self.user.id)
            sql_guild = sql.get_guild(guild.id)
            panel_channel = None
            resume_channel = None
            citlist_channel = None
            citizen_role = None
            if sql_guild:
                panel_channel = guild.get_channel(sql_guild['panel_channel_id']) if sql_guild['panel_channel_id'] is not None else None
                panel_message = panel_channel.get_partial_message(sql_guild['panel_message_id']) if sql_guild['panel_message_id'] is not None else None
                citizen_role = guild.get_role(sql_guild['citizen_role_id']) if sql_guild['citizen_role_id'] is not None else None
                print('sys channel:', guild.system_channel.id)
                if panel_channel is not None and panel_channel.permissions_for(guild_bot).send_messages:
                    from handler import update_panel
                    await update_panel(self, guild)
                    sql.update_panel(guild.id,
                                     panel_channel.id if panel_channel is not None else None,
                                     panel_message.id)
                    if citizen_role is not None:
                        sql.update_citizen_role_id(guild.id, citizen_role.id)
                elif panel_channel is None:
                    if guild_bot.guild_permissions.manage_channels:
                        overwrites = {
                            guild.get_member(self.user.id): nextcord.PermissionOverwrite(view_channel=True,
                                                                                         send_messages=True),
                            guild.default_role: nextcord.PermissionOverwrite(read_messages=False)
                        }
                        panel_channel = await guild.create_text_channel(name=f'🤖ㆍ{self.user.display_name}-panel',
                                                                        overwrites=overwrites)
                        from handler import update_panel
                        sql.update_panel(guild.id,
                                         panel_channel.id if panel_channel is not None else None,
                                         panel_message.id)
                        if citizen_role is not None:
                            sql.update_citizen_role_id(guild.id, citizen_role.id)
                        await update_panel(self, guild)
            else:
                # try:
                if guild_bot.guild_permissions.manage_channels:
                    overwrites = {
                        guild.get_member(self.user.id): nextcord.PermissionOverwrite(view_channel=True,
                                                                                     send_messages=True),
                        guild.default_role: nextcord.PermissionOverwrite(read_messages=False)
                    }
                    panel_channel = await guild.create_text_channel(name=f'🤖ㆍ{self.user.display_name}-panel',
                                                                    overwrites=overwrites)
                    sql.add_guild(guild_id=guild.id,
                                  panel_channel_id=panel_channel.id, citizen_role_id=None, invite=None)
                    from handler import update_panel
                    await update_panel(self, guild)
                else:
                    raise PermissionError
                # except PermissionError as e:
                #     if guild.system_channel is not None and guild.system_channel.permissions_for(
                #             guild_bot).send_messages:
                #         from handler import send_to_system_channel
                #         await send_to_system_channel(guild=guild, text=f'Не хватает прав! {e}')
        except Exception as e:
            raise f'Error {e} \nat line {exc_info()[2].tb_lineno}'

        # await Panel(client).update_panel(guild)
        # try:
        #     citizen: int = sql.one(f"SELECT citizen_role_id FROM guilds WHERE guild_id = '{guild.id}'")
        #                    f"VALUES('{guild.id}', {panel.id})")
        # except Exception as error:
        #     tb = exc_info()[2]
        #     print(error, '\nat line {}'.format(tb.tb_lineno))


client = Bot(intents=Intents.all())
client.run(environ.get('BOT_TOKEN', None))
