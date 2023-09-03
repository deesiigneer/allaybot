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

    @slash_command(description='Канал в который будут поступать заявки.')
    @application_checks.has_permissions(administrator=True)
    async def resume(self, interaction: Interaction,
                     channel: TextChannel = SlashOption(name='channel',
                                                        description='Канал в который будут поступать заявки',
                                                        required=True)):
        sql_recruiting = sql.get_requests(interaction.guild.id)
        if sql_recruiting is not None:
            sql.update_recruiting(interaction.guild.id,
                                  sql_recruiting['recruiting_channel_id'],
                                  sql_recruiting['recruiting_message_id'],
                                  channel.id,
                                  False)
            if sql.get_resume_fields_order_by_row(interaction.guild.id) is []:
                sql.add_resume_field(interaction.guild.id, 'nickname', 'deesiigneer', False, True, 0)
            from handler import update_panel
            # sql_guid = sql.get_guild(interaction.guild.id)
            await update_panel(interaction.client, interaction.guild)
            await interaction.send(f'{channel.mention} был установлен как канал в котором будут появляться заявки.',
                                   ephemeral=True)
        else:
            await interaction.send(f'Модуль заявок в город не установлен. Установите его через панель.',
                                   ephemeral=True)

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

    @slash_command(description="редактирует сообщение в канале с кнопкой")
    @application_checks.has_permissions(administrator=True)
    async def recruiting(self,
                         interaction: Interaction,
                         file: Attachment = SlashOption(
                             name='embed_file',
                             description='.json файл с сайта discohook.org',
                             required=True)):
        if file.filename.endswith('.json') and 'application/json' in file.content_type:
            async with aiohttp.ClientSession() as session:
                # print(await file.read(use_cached=True))
                async with session.get(file.url) as response:
                    sql_recruiting = sql.get_requests(interaction.guild.id)
                    message = None
                    channel = None
                    data = await response.json()
                    embeds = []
                    for index, embed in enumerate(data['embeds']):
                        if 'timestamp' in embed:
                            embed['timestamp'] = embed['timestamp'].replace('Z', '+00:00')
                        # embed['footer']['text'] = f'dev by deesiigneer'
                        # embed['footer']['icon_url'] = 'https://visage.surgeplay.com/face/512/' \
                        #                               '63ed47877aa3470fbfc46c5356c3d797.png'
                        if index == 0:
                            embed['author'] = {'name': f'powered by {interaction.client.user.name}',
                                               'icon_url': interaction.client.user.avatar.url,
                                               'url': 'https://discord.gg/VbyHaKRAaN'}
                        embeds.append(Embed.from_dict(embed))
                    if sql_recruiting:
                        if sql_recruiting['recruiting_channel_id'] is not None:
                            channel = await interaction.guild.fetch_channel(sql_recruiting['recruiting_channel_id'])
                        if sql_recruiting['recruiting_message_id'] is not None:
                            message = await channel.fetch_message(sql_recruiting['recruiting_message_id'])
                    print('message is ', message)
                    if sql_recruiting is None and message is None:
                        if data['content'] is not None:
                            message = await channel.send(content=data['content'],
                                                         embeds=embeds,
                                                         view=buttons.ButtonRecruiting(guild=interaction.guild))
                        else:
                            message = await channel.send(embeds=embeds,
                                                         view=buttons.ButtonRecruiting(guild=interaction.guild))
                        sql.add_recruiting(interaction.guild.id,
                                           message.channel.id,
                                           message.id,
                                           sql_recruiting['resume_channel_id'] if sql_recruiting is not None else None,
                                           status=False)
                        await interaction.send(content=f'{message.jump_url} был успешно опубликован.',
                                               ephemeral=True)
                        from handler import update_panel
                        await update_panel(interaction.client, interaction.guild)
                    elif sql_recruiting is not None and message is not None:
                        if data['content'] is not None:
                            await message.edit(content=data['content'],
                                               view=buttons.ButtonRecruiting(interaction.guild),
                                               embeds=embeds)
                        else:
                            await message.edit(view=buttons.ButtonRecruiting(interaction.guild),
                                               embeds=embeds)
                        sql.update_recruiting(interaction.guild.id,
                                              channel.id,
                                              message.id,
                                              sql_recruiting['resume_channel_id'] if sql_recruiting['resume_channel_id'] is not None else None,
                                              sql_recruiting['status'])
                        await interaction.send(f"{message.jump_url} был успешно отредактирован.",
                                               ephemeral=True)
                        from handler import update_panel
                        await update_panel(interaction.client, interaction.guild)
        else:
            if interaction.response.is_done() is False:
                await interaction.send(f"Команда принимает только `.json` файлы",
                                       ephemeral=True)
        # TODO: доделать ответ


def setup(bot):
    bot.add_cog(GeneralCommands(bot))
