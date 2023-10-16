import aiohttp
import nextcord.errors
from nextcord.ext.commands.bot import Bot
from nextcord import Interaction, Embed, Colour, slash_command, Role, SlashOption, Webhook, Attachment, TextChannel
from nextcord.ext import commands, application_checks
from nextcord.user import ClientUser
from sys import exc_info

import buttons
from database import sql
from handler import update_panel

guilds = sql.get_guilds()[0]


class GeneralCommands(commands.Cog):

    def __init__(self: ClientUser, client: Bot):
        self.bot = client

    @slash_command(description='Устанавливает роль жителя в этом городе')
    @application_checks.has_permissions(administrator=True)
    async def citizen(self, interaction: Interaction, role: Role = SlashOption(
        name='role',
        description='Роль жителя используемая на этом Discord сервере'
    )):
        try:
            sql_guild = sql.get_guild(interaction.guild.id)
            if sql_guild is not None:
                if sql_guild['citizen_role_id'] == role.id:
                    await interaction.send(
                        content=f'{role.mention} уже используется как роль жителя для города {interaction.guild.name}',
                        ephemeral=True)
                else:
                    sql.update_citizen_role_id(interaction.guild.id, citizen_role_id=role.id)
                    await interaction.response.send_message(
                        f"{role.mention} была установлена как роль жителя в этом городе!",
                        ephemeral=True)
                    await update_panel(interaction.client, interaction.guild)
        except Exception as e:
            print(e, f'\nat line {exc_info()[2].tb_lineno}')

    @slash_command(name='ping', description='Проверяет задержку бота', guild_ids=guilds)
    async def ping(self, interaction: Interaction):
        embed = Embed(title="Ping-pong",
                      description=f"Задержка примерно {round(self.bot.latency * 1000)}ms.",
                      color=Colour.from_rgb(47, 49, 54))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @slash_command(name='help', description='Помощь по боту', guild_ids=guilds)
    async def help(self, interaction: Interaction):
        await interaction.response.send_message('in dev', ephemeral=True)

    @slash_command(description='for bot owner only.', guild_ids=[850091193190973472])
    @application_checks.is_owner()
    async def check(self, interaction: Interaction,
                    guild: str = SlashOption(name='guild__id',
                                            description='guild-id',
                                            required=True)):
        guild = int(guild)
        await interaction.send(
            f'name: {interaction.client.get_guild(guild).name}\n'
            f'invites: {[invite for invite in await interaction.client.get_guild(guild).invites()]}\n'
            f'members: {interaction.client.get_guild(guild).members}\n',
            ephemeral=True)

    @slash_command(description='for bot owner only.', guild_ids=[850091193190973472, 1102196413233905696])
    @application_checks.is_owner()
    async def test(self, interaction: Interaction):
        # import modules
        # for module in modules.list:
        #     print(module)
        #     from sys import modules
        #     from importlib.machinery import SourceFileLoader
        #
        #     config = SourceFileLoader("config", f"modules/{module}/config.py").load_module()
        #     print(f"label={config.ModuleConfig.label}")
        #     print(f"description={config.ModuleConfig.description}")
        #     print(f"emoji={config.ModuleConfig.emoji}")
        #     print(f"value={config.ModuleConfig.value}")
        #     await config.module_callback(interaction=interaction)
        from handler import check_user_pass
        user_pass = await check_user_pass(interaction.user)
        await interaction.send(f"{interaction.user.name} {'имеет проходку на сервер СПм!'if user_pass is True else 'не имеет проходку на сервер СПм!'}", ephemeral=True)

    @slash_command(description='for bot owner only.', guild_ids=[850091193190973472])
    @application_checks.is_owner()
    async def leave(self, interaction: Interaction,
                    guild: str = SlashOption(name='guild__id',
                                            description='guild-id',
                                            required=True)):
        guild = interaction.client.get_guild(int(guild))
        await guild.leave()
        await interaction.send(f'leaved from {guild.name} ||{guild.id}||')

    @slash_command(description='for bot owner only.', guild_ids=[850091193190973472])
    @application_checks.is_owner()
    async def guilds(self, interaction: Interaction):
        guilds = interaction.client.guilds
        message = ''
        for guild in guilds:
            invites = ''
            for invite in await guild.invites():
                if invites is None:
                    invites = 'None'
                else:
                    invites += (f'https://discord.gg/{invite.code}\n')
            message += f'`{guild.name}` ({guild.id}) \n||{invites}||\n\n'
        await interaction.send(message, suppress_embeds=True,ephemeral=True)

    @slash_command(description='for bot owner only.', guild_ids=[850091193190973472, 1102196413233905696])
    @application_checks.is_owner()
    async def upd_tasks(self, interaction: Interaction):
        message = interaction.client.get_guild(1102196413233905696).get_thread(1128333588958560387).get_partial_message(1128333588958560387)
        from buttons.tasks import TasksChoice
        await message.edit(view=TasksChoice())


def setup(bot):
    bot.add_cog(GeneralCommands(bot))
