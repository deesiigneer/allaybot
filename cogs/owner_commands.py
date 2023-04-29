import json

import nextcord
from nextcord.ext.commands.bot import Bot
from nextcord import Interaction, Embed, Colour, slash_command, Status, SlashOption, ActivityType, Activity
from nextcord.ext import commands
from nextcord.user import ClientUser


class OwnerCommands(commands.Cog):

    def __init__(self: ClientUser, client: Bot):
        self.bot = client

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
