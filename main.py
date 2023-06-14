import nextcord
import logging
from nextcord.ext import commands
from nextcord.flags import Intents
from nextcord import Permissions, Embed, errors, Interaction, ApplicationError
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
            from buttons.general import BotPanelButtons
            from buttons.requests_to_city import ButtonRecruiting, CreateRecruiting, ApplicationToCityButtons,\
                ResumeEdit
            from buttons.tasks import TasksModule
            self.add_view(TasksModule())
            self.add_view(ButtonRecruiting())
            self.add_view(BotPanelButtons())
            self.add_view(CreateRecruiting())
            # self.add_view(ExtendedInstallation())
            self.add_view(ApplicationToCityButtons())
            self.add_view(ResumeEdit())

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
        guild = message.guild
        sql_guild = sql.get_guild(guild.id)
        thread = message.channel.category.channels
        print(thread)
        for channel in message.channel.category.channels:
            if sql_guild[9] == channel.id and not message.author.bot:
                sql_task = sql.get_tasks(guild.id)
                print('sql_task2', sql_task[0][2])
                print(message.channel.id, sql_task[0][2])
                print(message.channel.applied_tags, sql_task[0][8])
                if message.channel.id == sql_task[0][2] and sql_task[0][8] in message.channel.applied_tag_ids:
                    webhook_url = 'https://discord.com/api/webhooks/1117413808332345394/cx1A73eMbUF5jZBENsUAB8d0fVe87xrixZEks73ynHNEEwq4nGnapBtEAKNJmf1xGOJW'
                    async with aiohttp.ClientSession() as session:
                        webhook = nextcord.Webhook.from_url(webhook_url, session=session)
                        from pyspapi import SPAPI, MojangAPI
                        spapi = SPAPI('6273cba5-add3-44b8-a9a6-d528fcf0f29a', 'hQvWsc9FssggbtNXukG/3XbgNXtyTgos')
                        username = spapi.get_user(message.author.id)
                        username = username.username if username is not None else 'deesiigneer'
                        avatar_url = f'https://visage.surgeplay.com/face/512/{MojangAPI.get_uuid(username)}.png'
                        print(avatar_url)
                        print(message.content)
                        thread = guild.get_thread(sql_task[0][4])
                        await webhook.send(username=username,
                                           avatar_url=avatar_url,
                                           content=message.content,
                                           thread=thread)



    async def on_guild_remove(self, guild: nextcord.Guild):
        log_guild = self.get_guild(850091193190973472)
        log_channel = log_guild.get_channel(1103024684003508274)
        sql.delete_guild(guild.id)
        sql.delete_recruiting(guild.id)
        await log_channel.send(f'Удален из guild: {guild.name} ({guild.id})')

    async def on_guild_join(self, guild: nextcord.Guild):
        log_guild = self.get_guild(850091193190973472)
        log_channel = log_guild.get_channel(1103024684003508274)
        sql.delete_guild(guild.id)
        sql.delete_recruiting(guild.id)
        await log_channel.send(f'Добавлен на сервер `{guild.name}` ({guild.id}) \n||{[invite for invite in await guild.invites()]}||')
        await client.sync_application_commands(guild_id=guild.id)
        try:
            guild_bot = guild.get_member(self.user.id)
            sql_guild: list = sql.get_guild(guild.id)
            panel_channel = None
            resume_channel = None
            citlist_channel = None
            citizen_role = None
            if sql_guild:
                panel_channel = guild.get_channel(sql_guild[1]) if sql_guild[1] is not None else None
                resume_channel = guild.get_channel(sql_guild[2]) if sql_guild[2] is not None else None
                citlist_channel = guild.get_channel(sql_guild[3]) if sql_guild[3] is not None else None
                citizen_role = guild.get_role(sql_guild[4]) if sql_guild[4] is not None else None
                print('sys channel:', guild.system_channel.id)
                if panel_channel is not None and panel_channel.permissions_for(guild_bot).send_messages:
                    from handler import update_panel
                    await update_panel(self, guild)
                    sql.update_guild(guild.id,
                                     panel_channel.id,
                                     resume_channel.id if resume_channel is not None else None,
                                     citlist_channel.id if citlist_channel is not None else None,
                                     citizen_role.id if citizen_role is not None else None)
                elif panel_channel is None:
                    if guild_bot.guild_permissions.manage_channels:
                        overwrites = {
                            guild.get_member(self.user.id): nextcord.PermissionOverwrite(view_channel=True,
                                                                                         send_messages=True),
                            guild.default_role: nextcord.PermissionOverwrite(read_messages=False)
                        }
                        panel_channel = await guild.create_text_channel(name=f'🤖ㆍabc-{self.user.display_name}-panel',
                                                                        overwrites=overwrites)
                        from handler import update_panel
                        sql.update_guild(guild.id,
                                         panel_channel.id,
                                         resume_channel.id if resume_channel is not None else None,
                                         citlist_channel.id if citlist_channel is not None else None,
                                         citizen_role.id if citizen_role is not None else None)
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
                                  panel_channel_id=panel_channel.id, citizen_role_id=None)
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
