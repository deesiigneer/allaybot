import aiohttp
import nextcord.errors
from nextcord.ext.commands.bot import Bot
from nextcord import Interaction, Embed, Colour, slash_command, Role, SlashOption, Webhook, Attachment, TextChannel
from nextcord.ext import commands
from nextcord.user import ClientUser
from sys import exc_info

import buttons
from database import sql
from handler import update_panel

guilds = sql.get_guilds()


class GeneralCommands(commands.Cog):

    def __init__(self: ClientUser, client: Bot):
        self.bot = client

    @slash_command(description='Устанавливает роль жителя в этом городе')
    async def citizen(self, interaction: Interaction, role: Role = SlashOption(
        name='role',
        description='Роль жителя используемая на этом Discord сервере'
    )):
        try:
            sql_guild = sql.get_guild(interaction.guild.id)
            if sql_guild is not None:
                if sql_guild[2] == role.id:
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
    async def resume(self, interaction: Interaction,
                     channel: TextChannel = SlashOption(name='channel',
                                                        description='Канал в который будут поступать заявки',
                                                        required=True)):
        sql_recruiting = sql.get_recruiting(interaction.guild.id)
        if sql_recruiting is not None:
            sql.update_recruiting(interaction.guild.id,
                                  sql_recruiting[1],
                                  sql_recruiting[4],
                                  channel.id,
                                  False)
            if sql.get_resume_fields_order_by_row(interaction.guild.id) is []:
                sql.add_resume_field(interaction.guild.id, 'nickname', 'deesiigneer', False, True, 0)
            from handler import update_panel
            # sql_guid = sql.get_guild(interaction.guild.id)
            await update_panel(interaction.client, interaction.guild)
            await interaction.send(f'{channel.mention} был установлен как канал в котором будут появляться заявки.',
                                   ephemeral=True)
            # TODO: доделать ответ
            # channel = interaction.guild.get_channel(sql_guid[1])
            # async for message in channel.history(oldest_first=True):
            #     if message.author == interaction.client:
            #         await message.edit(embed=update_panel[])

    @slash_command(description="EDIT ABOUT")
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
                    sql_recruiting = sql.get_recruiting(interaction.guild.id)
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
                        if sql_recruiting[1] is not None:
                            channel = await interaction.guild.fetch_channel(sql_recruiting[1])
                        if sql_recruiting[4] is not None:
                            message = await channel.fetch_message(sql_recruiting[4])
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
                                           sql_recruiting[2] if sql_recruiting is not None else None,
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
                                              sql_recruiting[2] if sql_recruiting[2] is not None else None,
                                              sql_recruiting[3])
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
