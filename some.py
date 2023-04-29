import nextcord
from nextcord.utils import find
from nextcord.ext.commands.bot import Bot
from nextcord import Embed, Guild
from nextcord.user import ClientUser
from nextcord.ext import commands
from sys import exc_info

from database import sql
from buttons import BotPanelButtons


class Panel(commands.Cog):
    def __init__(self: ClientUser, client: Bot):
        self.bot = client

    async def update_panel(self, guild: Guild):
        try:
            citizen: int = sql.one(f"SELECT citizen_role_id FROM guilds WHERE guild_id = '{guild.id}'")[0]
            if citizen is not None:
                citizen: nextcord.Role = guild.get_role(citizen)
            embed = Embed(title=f'Настройки функций бота для города "{guild.name}"',
                          description=f"Роль жителя в этом городе: '{citizen.mention if citizen is not None else None}"
                                      f" (`{citizen.id if citizen is not None else None}`)'\n"
                                      f"*что бы изменить, введите:* **`/citizen`**",
                          colour=0x2f3136)
            embed.set_author(name='Golem settings panel',
                             icon_url='https://img.icons8.com/color/48/null/dashboard-layout.png')
            emoji: nextcord.Emoji = self.bot.get_emoji(1038421382477922384)
            value = None
            application_to_city = sql.one(f"SELECT field_1_name, field_2_name, field_3_name, field_4_name, field_5_name"
                                          f" FROM application_to_city WHERE guild_id = '{guild.id}'")
            if application_to_city is not None:
                emoji: nextcord.Emoji = self.bot.get_emoji(1038421381085401088)
                for names in application_to_city:
                    if names is not None:
                        value += f"> {names}\n"
            embed.add_field(name=f'Заявки в город {emoji}',
                            value=value)
            emoji: nextcord.Emoji = self.bot.get_emoji(1038421382477922384)
            citizens = sql.one(f"SELECT guild_id FROM citizens WHERE guild_id = '{guild.id}'")
            if citizens is not None:
                emoji: nextcord.Emoji = self.bot.get_emoji(1038421381085401088)

            embed.add_field(name=f'Список жителей {emoji}',
                            value=value)
            emoji: nextcord.Emoji = self.bot.get_emoji(1038421382477922384)
            profession_chose = sql.one(f"SELECT guild_id FROM profession_chose WHERE guild_id = '{guild.id}'")
            if profession_chose is not None:
                emoji: nextcord.Emoji = self.bot.get_emoji(1038421381085401088)
            embed.add_field(name=f'Выбор профессии {emoji}',
                            value=value)
            embed.set_footer(text='dev by deesiigneer')
            embeds = [embed]
            panel_channel = find(lambda channel: channel.name == '🤖ㆍgolem-panel', guild.text_channels)
            panel = None
            if panel_channel and panel_channel.permissions_for(guild.me).send_messages:
                channel = guild.get_channel(sql.one(f"SELECT settings_panel_channel_id"
                                                    f"FROM guilds"
                                                    f"WHERE guild_id = '{guild.id}'"))
                async for channel_message in channel.history(limit=1000, oldest_first=True):
                    channel_message_embeds = channel_message.embeds
                    for channel_message_embed in channel_message_embeds:
                        if 'Настройки функций бота для города ' in channel_message_embed.title:
                            panel = await channel_message.edit(embeds=embeds, view=BotPanelButtons())
                        else:
                            panel = await panel_channel.send(embeds=embeds, view=BotPanelButtons())
            elif panel_channel is None:
                pannel_channel = await guild.create_text_channel(name='🤖ㆍgolem-panel', overwrites={
                    guild.default_role: nextcord.PermissionOverwrite(read_messages=False)})
                panel = await pannel_channel.send(embeds=embeds, view=BotPanelButtons())
            if sql.one(f"SELECT guild_id FROM guilds WHERE guild_id = '{guild.id}'") is None:
                sql.commit(f"INSERT INTO guilds (guild_id, settings_panel_channel_id)"
                           f"VALUES('{guild.id}', {panel.id})")
        except Exception as error:
            tb = exc_info()[2]
            print(error, '\nat line {}'.format(tb.tb_lineno))


def setup(bot):
    bot.add_cog(Panel(bot))
