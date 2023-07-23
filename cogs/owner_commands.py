import datetime
import json

import aiohttp
import nextcord
from nextcord.ext.commands.bot import Bot
from nextcord import Interaction, Embed, Colour, slash_command, Status, SlashOption, ActivityType, Activity,\
    ChannelType, ForumTag, ChannelFlags
from nextcord.ext import commands
from nextcord.user import ClientUser
from database import sql


class OwnerCommands(commands.Cog):

    def __init__(self: ClientUser, client: Bot):
        self.bot = client

    @slash_command(name='update-panels', description='обновляет панель во всех каналах', guild_ids=[850091193190973472],
                   default_member_permissions=8)
    async def update_panels(self, interaction: Interaction):
        guilds = sql.get_guilds()
        print(guilds)
        for sqL_guild in guilds:
            print(f'guild = {sqL_guild}')
            guild = interaction.client.get_guild(sqL_guild['guild_id'])
            channel = guild.get_channel(sqL_guild['panel_channel_id'])
            from handler import update_panel, Check
            # await Check(interaction.client, interaction.guild).comparison_database_to_guild(interaction, channel,
            #                                                                                 interaction.message)
            await update_panel(interaction.client, guild)
            from buttons.general import BotPanelButtons
            message = await channel.fetch_message(sqL_guild['panel_message_id'])
            await message.edit(view=BotPanelButtons())
            # await interaction.edit(embeds=embeds, view=BotPanelButtons())

    @slash_command(name='test_command', description='test', guild_ids=[850091193190973472, 1102196413233905696],
                   default_member_permissions=8)
    async def test_command(self, interaction: Interaction):
        thread = interaction.guild.get_thread(1120326850099556423)
        async for message in thread.history(limit=100, oldest_first=True):
            print(message)
            if message.author == self.bot.user:
                print('1')
                from buttons.tasks import TasksChoice
                await message.edit(view=TasksChoice())

    @slash_command(name='sub', description='test', guild_ids=[850091193190973472, 1102196413233905696],
                   default_member_permissions=8)
    async def subscription(self, interaction: Interaction, guild_id: int, days: int):
        try:
            guild = self.bot.get_guild(guild_id)
            sql_guild = sql.get_guild(guild.id)
            sub = None
            subscription = None
            if sql_guild is not None:
                try:
                    if sql_guild['subscription_expires'] is not None:
                        subscription: datetime.date = sql_guild['subscription_expires']
                        sub = sql_guild['subscription_expires']
                    else:
                        sub = datetime.datetime.now().day + days
                except Exception as error_:
                    await interaction.send(ephemeral=True, content='Произошла ошибка... \n\n'
                                                             f'```{error_}```')
                if sub is not None:
                    sql.update_subscription(guild.id, sub)
            else:
                await interaction.send(ephemeral=True, content=f"Discord сервер с ID:`{guild_id}` не найден!")
            #TODO check for work
        except Exception as error:
            await interaction.send(ephemeral=True, content='Произошла ошибка... \n\n'
                                                     f'```{error}```')
        else:
            await interaction.send(ephemeral=True,
                                   content=f"Подписка для {guild.name} установлена до - `{sub}`"
                                           f"{f' было {subscription}' if subscription is not None else ''}")

        # thread = interaction.guild.get_thread(1120326850099556423)
        # async for message in thread.history(limit=100, oldest_first=True):
        #     print(message)
        #     if message.author == self.bot.user:
        #         print('1')
        #         from buttons.tasks import TasksChoice
        #         await message.edit(view=TasksChoice())
        # await thread.edit(flags=pinned)
        # thread = channel.get_thread(1117409819041738793)
        # print('tags', channel.available_tags)
        # webhook_url = 'https://discord.com/api/webhooks/1117413808332345394/cx1A73eMbUF5jZBENsUAB8d0fVe87xrixZEks73ynHNEEwq4nGnapBtEAKNJmf1xGOJW'
        # async with aiohttp.ClientSession() as session:
        #     webhook = nextcord.Webhook.from_url(webhook_url, session=session)
        #     await webhook.send(username='deesiigneer',
        #                        avatar_url='https://visage.surgeplay.com/face/512/63ed47877aa3470fbfc46c5356c3d797.png',
        #                        content='Это проверка, как будет выглядеть текст в форуме от лица пользователя',
        #                        thread=thread)
        # embed = Embed(title='TEST', description='__TEST__k')
        # from buttons.tasks import TasksAccept
        # url_img = 'https://media.discordapp.net/attachments/1114623864736059392/1114623864903827566/cat-angry.gif'
        # embed.set_image(url_img)
        # forum_tags = [ForumTag(name='Глобальные заказы', id=1117409113819857008),
        #               ForumTag(name='Выполненые', id=1117409113819857011)]
        # print(channel.available_tags)
        # thread = await channel.create_thread(name='test', embed=embed, view=TasksAccept(), content='TEST_CONTENT',
        #                             applied_tags=forum_tags)
        # await thread.edit(applied_tags=forum_tags)
        # print(f'applied tags - {thread.applied_tags}')

    @slash_command(name='status', description='Изменяет активность бота', guild_ids=[850091193190973472],
                   default_member_permissions=8)
    async def status(self, interaction: Interaction,
                     new_activity_name: str,
                     new_status: str = SlashOption(
                         name="status",
                         description="Новый статус бота",
                         required=False,
                         choices={"online": "online", "offline": "offline", "idle": "idle", "dnd": "dnd"},),
                     new_activity: str = SlashOption(
                         name="activity_type",
                         description="Новый тип активности бота",
                         required=False,
                         choices={"playing": "playing", "listening": "listening",
                                  "watching": "watching", "competing": "competing"},)
                     ):
        activity = Activity(type=ActivityType.listening,
                            name="t.me/deesiigneer")
        if new_activity == 'playing':
            activity = Activity(type=ActivityType.playing,
                                name=new_activity_name)
        if new_activity == 'listening':
            activity = Activity(type=ActivityType.listening,
                                name=new_activity_name)
        if new_activity == 'watching':
            activity = Activity(type=ActivityType.watching,
                                name=new_activity_name)
        if new_activity == 'competing':
            activity = Activity(type=ActivityType.competing,
                                name=new_activity_name)
        if new_status == 'online':
            await self.bot.change_presence(
                activity=activity,
                status=Status.online)
        if new_status == 'offline':
            await self.bot.change_presence(
                activity=activity,
                    status=Status.offline)
        if new_status == 'idle':
            await self.bot.change_presence(
                activity=activity,
                status=Status.idle)
        if new_status == 'dnd':
            await self.bot.change_presence(
                activity=activity,
                status=Status.dnd)
        await interaction.response.send_message(embed=Embed(title="Новый статус бота",
                      description=f"Тип активности: `{new_activity}`\n"
                                  f"Имя активности: `{new_activity_name}`\n"
                                  f"Статус: `{new_status}`",
                      color=Colour.from_rgb(47, 49, 54)), ephemeral=True)


def setup(bot):
    bot.add_cog(OwnerCommands(bot))
