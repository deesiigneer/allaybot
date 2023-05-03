from nextcord.ext import commands
from nextcord import Guild, TextChannel, Role, Emoji, Embed, Interaction, PartialMessage, Message
from database import sql
from pyspapi import SPAPI, MojangAPI


async def send_to_system_channel(guild: Guild, text: str):
    try:
        await guild.system_channel.send(f'{text}')
    except PermissionError as e:
        raise f"Don`t enough permission for send message to system channel! {e}"


class Check:
    def __init__(self, bot: commands.Bot, guild: Guild):
        self.bot = bot
        self.guild = guild
        self.__log_guild = bot.get_guild(850091193190973472)
        self.log_channel = self.__log_guild.get_channel(1103024684003508274)

    async def comparison_database_to_guild(self, interaction: Interaction,
                                           channel: TextChannel = None, message: Message = None):
        sql_guild = sql.get_guild(self.guild.id)
        if sql_guild:
            guild = self.bot.get_guild(sql_guild[0])
            if guild:
                repair = 0
                if sql_guild[1]:
                    panel_channel = self.bot.get_guild(sql_guild[0]).get_channel(sql_guild[1])
                    if not panel_channel:
                        await self.log_channel.send(f'channel with id `{sql_guild[1]}` not found in:\n'
                                                    f'guild: `{self.guild.id}`')
                        await interaction.send(f'Канал с id {sql_guild[1]} не найден!\n'
                                               f'Возможно его удалили, что бы починить используйте команду /repair',
                                               ephemeral=True)
                        repair = 1
                else:
                    repair = 1
                if repair == 1:
                    await self.log_channel.send(f'У `{self.guild.id}` нету канала с панелью... создаю.')
                    if guild.me.guild_permissions.manage_channels:
                        panel_channel = await guild.create_text_channel(name=f'🤖ㆍ{self.bot.user.display_name}-panel')
                        sql.update_guild(sql_guild[0], panel_channel.id, sql_guild[3], sql_guild[2])
                        await update_panel(self.bot, guild)
                    else:
                        await self.log_channel.send(f'Неудалось создать панель для guild `{self.guild.id}`'
                                                    f' недостаточно прав. ||manage_channels||')
                sql_guild = sql.get_guild(self.guild.id)
                panel_msg = self.bot.get_guild(sql_guild[0]).get_channel(sql_guild[1]).get_partial_message(sql_guild[3])
                if not panel_msg:
                    await self.log_channel.send(f'message with id `{sql_guild[3]}` not found in:\n'
                                                f'channel: `{self.bot.get_guild(sql_guild[0]).get_channel(sql_guild[1]).id}`\n'
                                                f'guild: `{self.guild.id}`')
                    await interaction.send(f'Сообщение с id {sql_guild[3]} в канале с id {sql_guild[1]} не найден!\n'
                                           f'Возможно его удалили, что бы починить используйте команду /repair',
                                           ephemeral=True)
                    pass
            else:
                print('guild', guild)
                await self.log_channel.send(f'{self.bot.user.mention} не имеет доступа к {self.guild.id}')
                pass
        else:
            based = await self.log_channel.send(f'{self.guild.id} не найдена в базе данных, добавляю..')
            print(type(self.guild.id))
            if self.bot.get_guild(self.guild.id):
                sql.add_guild(self.guild.id, None, None, None)
                await Check(self.bot, self.guild).comparison_database_to_guild(interaction)
                pass
            else:
                await based.reply(f'Не могу добавить {self.guild.id}. Видимо меня выгнали :(')
                pass


async def update_panel(bot: commands.Bot, guild: Guild) -> None:
    try:
        panel_channel = None
        recruiting_channel = None
        resume_channel = None
        recruiting_status = False
        citlist_channel = None
        citizen_role = None
        sql_guild: list = sql.get_guild(guild.id)
        sql_recruiting: list = sql.get_recruiting(guild.id)
        if sql_guild:
            panel_channel = guild.get_channel(sql_guild[1]) if sql_guild[1] is not None else None
            citizen_role = guild.get_role(sql_guild[2]) if sql_guild[2] is not None else None
            if sql_recruiting:
                recruiting_channel = guild.get_channel(sql_recruiting[1]) if sql_recruiting[1] is not None else None
                resume_channel = guild.get_channel(sql_recruiting[2]) if sql_recruiting[2] is not None else None
                recruiting_status: bool = sql_recruiting[3] if sql_recruiting[3] is not None else None
        embed = Embed(title=f'Управление городом - `{guild.name}`', colour=0x2f3136)
        embed.set_thumbnail(guild.icon.url if guild.icon is not None else
                            'https://static.wikia.nocookie.net/minecraft_gamepedia/images/4/45/Allay_JE2.gif')
        embed.set_author(name=f'{bot.user.display_name} panel',
                         icon_url=bot.user.avatar.url,
                         url='https://discord.gg/VbyHaKRAaN')
        # https://img.icons8.com/color/48/null/dashboard-layout.png
        embed.set_footer(text='dev by deesiigneer',
                         icon_url='https://visage.surgeplay.com/face/512/63ed47877aa3470fbfc46c5356c3d797.png')
        if citizen_role is None:
            embed.description = f"**Роль жителя не установлена.**"
        if citizen_role is not None:
            embed.description = f"Роль жителя в этом городе: " \
                                f"{citizen_role.mention}"
        embed.description += f"\n**что бы изменить, используйте:**\n" \
                             f"*`/citizen`*"
        disabled_emoji: Emoji = bot.get_emoji(1038421382477922384)
        enabled_emoji: Emoji = bot.get_emoji(1038421381085401088)
        print('recruiting_status', recruiting_status)
        embed.add_field(
            name=f'Набор в город {guild.name} {disabled_emoji if recruiting_status is False else enabled_emoji}',
            value=f'{recruiting_channel.mention if recruiting_channel is not None else "*Не установлено*"}\n'
                  f'{resume_channel.mention if resume_channel is not None else ""} ',
            inline=False)

        if citlist_channel is None:
            emoji: Emoji = bot.get_emoji(1038421382477922384)
        else:
            emoji: Emoji = bot.get_emoji(1038421381085401088)
        embed.add_field(name=f'Список жителей города {guild.name} {emoji}',
                        value=citlist_channel.mention if citlist_channel is not None else '*Не установлено*',
                        inline=False)
        embeds = [embed]
        msg = None
        async for message in panel_channel.history(limit=100, oldest_first=True):
            if message.author == bot.user:
                from buttons import BotPanelButtons
                msg = await message.edit(embeds=embeds, view=BotPanelButtons())
        if msg is None:
            from buttons import BotPanelButtons
            await panel_channel.send(embeds=embeds, view=BotPanelButtons())
        sql.update_guild(
            guild.id,
            panel_channel.id if panel_channel is not None else None,
            msg.id if msg is not None else None,
            citizen_role.id if citizen_role is not None else None,

        )
        return
    except PermissionError as e:
        raise f"Don`t enough permission for send message to system channel! {e}"


async def update_applications_panel(bot: commands.Bot, guild: Guild):
    recruiting_channel = None
    resume_channel = None
    status = False
    recruiting_message = None
    sql_recruiting: list = sql.get_recruiting(guild.id)
    if sql_recruiting is not None:
        recruiting_channel = guild.get_channel(sql_recruiting[1])
        resume_channel = guild.get_channel(sql_recruiting[2])
        status = bool(sql_recruiting[3])
        recruiting_message = recruiting_channel.get_partial_message(sql_recruiting[4]) if sql_recruiting[4] is not None else None
    disabled_emoji: Emoji = bot.get_emoji(1038421382477922384)
    enabled_emoji: Emoji = bot.get_emoji(1038421381085401088)
    embed = Embed(title=f'Настройка заявок в город `{guild.name}` {enabled_emoji if status else disabled_emoji}',
                  description=f'**Используйте команду** *`/recruiting`* - для редактирования канала '
                              f'с описанием города и кнопкой\n\n'
                              f'**Используйте команду** *`/resume`* - для редактирования канала с заявками в город\n\n',
                  color=0x2f3136)
    embed.add_field(name='Канал с описанием города.',
                    value=f'{recruiting_channel.mention if recruiting_channel is not None else "*Не установлен*"}\n'
                          f'{f"||{recruiting_message.jump_url}||" if recruiting_message is not None else ""}')
    embed.add_field(name=f'Канал с заявками в город.',
                    value=f'{resume_channel.mention if resume_channel is not None else "*Не установлен*"}')
    embed.set_thumbnail('https://static.wikia.nocookie.net/minecraft_gamepedia/images/4/45/Allay_JE2.gif')
    return embed


async def update_resume_preview(interaction: Interaction, preview_labels: list = None, channel: TextChannel = None):
    sql_user = sql.get_user(interaction.user.id)
    spapi = SPAPI('6273cba5-add3-44b8-a9a6-d528fcf0f29a', 'hQvWsc9FssggbtNXukG/3XbgNXtyTgos')
    sp_user = spapi.get_user(interaction.user.id)
    if sql_user is None and sp_user is not None:
        sql.add_user(interaction.user.id, MojangAPI().get_uuid(sp_user.username))
    else:
        return [None, None]
    # TODO: проверка на никнейм by pyspapi
    embed = Embed(title=f'Заявка №{len(await channel.history().flatten()) if channel is not None else "ПРЕДПРОСМОТР"}',
                  description=f'От - {interaction.user.mention}',
                  color=0x2f3136)
    user = None
    if sql_user is not None:
        user = sql_user
    embed.set_author(
        name=f'{interaction.user.nick if interaction.user.nick is not None else interaction.user.display_name}',
        url=f'https://namemc.com/profile/{user[1]}' if user is not None else None,
        icon_url=f'https://visage.surgeplay.com/face/512/{user[1]}.png' if user is not None else None
    )
    sql_resume_fields = sql.get_resume_fields_order_by_row(interaction.guild.id)
    if sql_resume_fields is not None:
        for index, field in enumerate(sql_resume_fields):
            embed.add_field(
                name=field[1],
                value=f'{preview_labels[index] if preview_labels is not None else "*ПРЕДПРОСМОТР*"}',
                inline=False)
    if interaction.user.avatar is not None:
        embed.set_footer(text=f'{interaction.user.name}#{interaction.user.discriminator}',
                         icon_url=interaction.user.avatar.url)
    return [embed, sql_resume_fields]
