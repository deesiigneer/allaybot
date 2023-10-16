import logging

import nextcord
from nextcord.ext import commands
from nextcord import Guild, TextChannel, Role, Emoji, Embed, Interaction, PartialMessage, Message, Permissions
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

    async def channel_permissions(self, channel: TextChannel):
        guild = self.guild
        bot = self.bot
        return channel.permissions_for(guild.get_member(bot.user.id))

    async def permissions(self, permsission: Permissions):
        guild = self.guild
        bot = self.bot
        permissions = guild.get_member(bot.user.id).guild_permissions

    async def channels_exist(self):
        guild = self.guild
        bot = self.bot
        sql_guild = sql.get_guild(guild.id)
        sql_recruiting = sql.get_requests(guild.id)
        if sql_guild is not None:
            perms: Permissions = guild.get_member(bot.user.id).guild_permissions
            if perms.manage_channels and perms.send_messages:
                panel_channel_id = sql_guild['guild_id']
                panel_message_id = sql_guild['panel_message_id']
                citizen_role_id = sql_guild['citizen_role_id']
                panel_channel = guild.get_channel(panel_channel_id)
                if panel_channel is not None:
                    panel_message = panel_channel.get_partial_message(panel_message_id)
            # else:

            # else:
            #
            # citizen_role_id = guild.get_role(citizen_role_id)


    async def comparison_database_to_guild(self, interaction: Interaction,
                                           channel: TextChannel = None, message: Message = None):
        sql_guild = sql.get_guild(self.guild.id)
        if sql_guild:
            guild = self.bot.get_guild(sql_guild['guild_id'])
            if guild:
                repair = 0
                if sql_guild['panel_channel_id']:
                    panel_channel = self.bot.get_guild(sql_guild['guild_id']).get_channel(sql_guild['panel_channel_id'])
                    if not panel_channel:
                        await self.log_channel.send(f'channel with id `{sql_guild["panel_channel_id"]}` not found in:\n'
                                                    f'guild: `{self.guild.id}`')
                        await interaction.send(f'Канал с id {sql_guild["panel_channel_id"]} не найден!\n'
                                               f'Возможно его удалили, что бы починить используйте команду /repair',
                                               ephemeral=True)
                        repair = 1
                else:
                    repair = 1
                if repair == 1:
                    await self.log_channel.send(f'У `{self.guild.id}` нету канала с панелью... создаю.')
                    if guild.me.guild_permissions.manage_channels:
                        panel_channel = await guild.create_text_channel(name=f'🤖ㆍ{self.bot.user.display_name}-panel')
                        sql.update_panel(sql_guild['guild_id'], panel_channel.id)
                        await update_panel(self.bot, guild)
                    else:
                        await self.log_channel.send(f'Неудалось создать панель для guild `{self.guild.id}`'
                                                    f' недостаточно прав. ||manage_channels||')
                sql_guild = sql.get_guild(self.guild.id)
                panel_msg = self.bot.get_guild(sql_guild['guild_id']).get_channel(sql_guild['panel_channel_id']).get_partial_message(sql_guild["panel_message_id"])
                if not panel_msg:
                    await self.log_channel.send(f'message with id `{sql_guild["panel_message_id"]}` not found in:\n'
                                                f'channel: `{self.bot.get_guild(sql_guild["guild_id"]).get_channel(sql_guild["panel_channel_id"]).id}`\n'
                                                f'guild: `{self.guild.id}`')
                    await interaction.send(f'Сообщение с id {sql_guild["panel_message_id"]} в канале с id {sql_guild["panel_channel_id"]} не найден!\n'
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
                sql.add_guild(self.guild.id, None, None, None, None, None)
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
        sql_guild = sql.get_guild(guild.id)
        sql_recruiting = sql.get_requests(guild.id)
        print(f'updatepanel {sql_guild}')
        if sql_guild:
            panel_channel = guild.get_channel(sql_guild['panel_channel_id']) if sql_guild['panel_channel_id'] is not None else None
            citizen_role = guild.get_role(sql_guild['citizen_role_id']) if sql_guild['citizen_role_id'] is not None else None
            if sql_recruiting:
                recruiting_channel = guild.get_channel(sql_recruiting['requests_channel_id']) if sql_recruiting['requests_channel_id'] is not None else None
                recruiting_status: bool = sql_recruiting['status'] if sql_recruiting['status'] is not None else None
        from datetime import datetime
        subscription = datetime.combine(sql_guild['subscription_expires'], datetime.min.time()) if sql_guild['subscription_expires'] is not None else None
        print('sub', subscription)
        embed = Embed(title=f'Управление городом - `{guild.name}`', colour=0x2f3136, timestamp=subscription)
        embed.set_thumbnail(guild.icon.url if guild.icon is not None else
                            'https://static.wikia.nocookie.net/minecraft_gamepedia/images/4/45/Allay_JE2.gif')
        embed.set_author(name=f'{bot.user.display_name} panel',
                         icon_url=bot.user.avatar.url,
                         url='https://discord.gg/VbyHaKRAaN')
        # https://img.icons8.com/color/48/null/dashboard-layout.png
        # if subscription is not None:
        #     sub = subscription.isoformat()
        #     now = datetime.utcnow().isoformat()
        #     embed.set_footer(text=f'Премиум подписка {"активна до" if sub > now else "истекла"}',
        #                      icon_url='https://static.wikia.nocookie.net/minecraft_gamepedia/images/4/45/Allay_JE2.gif')
        # else:
        #     embed.set_footer(text=f'Нету активной премиум подписки',
        #                      icon_url='https://static.wikia.nocookie.net/minecraft_gamepedia/images/4/45/Allay_JE2.gif')
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
        # embed.add_field(
        #     name=f'v',
        #     value=f'{recruiting_channel.mention if recruiting_channel is not None else "*Не установлено*"}\n',
        #     inline=False)

        # if citlist_channel is None:
        #     emoji: Emoji = bot.get_emoji(1038421382477922384)
        # elif citlist_channel is not None:
        #     emoji: Emoji = bot.get_emoji(1038421381085401088)
        # embed.add_field(name=f'Список жителей города {guild.name} {emoji}',
        #                 value=citlist_channel.mention if citlist_channel is not None else '*Не установлено*',
        #                 inline=False)
        embeds = [embed]
        msg = None
        #  TODO: rewrite msg
        if panel_channel is not None:
            async for message in panel_channel.history(limit=100, oldest_first=True):
                if message.author == bot.user:
                    from main_buttons import BotPanelButtons
                    msg = await message.edit(embeds=embeds, view=BotPanelButtons())
            if msg is None:
                from main_buttons import BotPanelButtons
                msg = await panel_channel.send(embeds=embeds, view=BotPanelButtons())
            sql.update_panel(
                guild.id,
                panel_channel.id if panel_channel is not None else None,
                msg.id if msg is not None else None)
            if citizen_role is not None:
                sql.update_citizen_role_id(citizen_role.id)
        return
    except PermissionError as e:
        raise f"Don`t enough permission for send message to system channel! {e}"


async def update_applications_panel(bot: commands.Bot, guild: Guild):
    recruiting_channel = None
    recruiting_message = None
    status = False
    private = False
    sql_requests = sql.get_requests(guild.id)
    sql_guild = sql.get_guild(guild.id)
    await Check(bot, guild).channels_exist()
    if sql_requests is not None:
        recruiting_channel = guild.get_channel(sql_requests['requests_channel_id'])
        status = sql_requests['status']
        private = sql_requests['private']
        recruiting_message = recruiting_channel.get_partial_message(
            sql_requests['requests_message_id']).jump_url if sql_requests['requests_channel_id'] is not None else '**Не установлен**'
    disabled_emoji: Emoji = bot.get_emoji(1038421382477922384)
    enabled_emoji: Emoji = bot.get_emoji(1038421381085401088)
    embed = Embed(title=f'Настройка заявок в город `{guild.name}` {enabled_emoji if status else disabled_emoji}',
                  description=f'**```description```**',
                  color=0x2f3136)
    # todo проверка на валидный инвайт
    embed.add_field(
        name='Канал с кнопкой и описанием города.',
        value=f'{f"{recruiting_message}" if recruiting_message is not None else "*Не установлен*"}')
    embed.add_field(inline=False,
        name='**[НЕ УДАЛЯТЬ]** Ссылка приглашение.',
        value=f'https://discord.gg/{sql_guild["invite"]}\n\n'
              f'**Если удалить инвайт - к вам в город не смогут попасть новые люди!**' if sql_guild["invite"] is not None else "**Не установлено**")
    embed.add_field(inline=False,
        name='Статус набора',
        value=f"{'В процессе' if status is True else 'Приостановлен'}")
    embed.add_field(inline=False,
        name='**[in dev]** Видимость/приватность заявок',
        value=f"{'Открытые' if private is False else 'Закрытые'}")
    embed.set_thumbnail('https://static.wikia.nocookie.net/minecraft_gamepedia/images/4/45/Allay_JE2.gif')
    return embed


async def check_user_pass(user: nextcord.User):
    sql_user = sql.get_user(user.id)
    spapi = SPAPI('6273cba5-add3-44b8-a9a6-d528fcf0f29a', 'hQvWsc9FssggbtNXukG/3XbgNXtyTgos')
    sp_user = spapi.get_user(user.id)
    print(sp_user)
    if sql_user:
        return True
    elif sp_user and sp_user.username != "None":
        print(f"User {user.name}({user.id}) not found in database, adding...")
        sql.add_user(user.id, MojangAPI.get_uuid(sp_user.username))
        return True
    else:
        if sp_user is None:
            print("SPWorlds API is down right now...")
        return False


async def check_permissions(interaction: Interaction, **perms: bool):
    invalid = set(perms) - set(nextcord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")
    permissions = interaction.guild.me.guild_permissions
    missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]
    if not missing:
        return True
    else:
        s = ''
        for x in missing:
            print(x)
            s = s + x + '\n' if s.startswith('') else s + x
        await interaction.send(f'Требуются следующие разрешения:\n\n{s}', ephemeral=True)


async def update_resume_preview(interaction: Interaction, preview_labels: list = None, channel: TextChannel = None):
        embed = Embed(title=f'Заявка №{len(await channel.history().flatten()) if channel is not None else "ПРЕДПРОСМОТР"}',
                      description=f'От - {interaction.user.mention}',
                      color=0x2f3136)
        user = None
        sql_user = sql.get_user(interaction.user.id)
        if sql_user is not None:
            user = sql_user
        embed.set_author(
            name=f'{interaction.user.nick if interaction.user.nick is not None else interaction.user.display_name}',
            url=f'https://namemc.com/profile/{user["minecraft_uid"]}' if user is not None else None,
            icon_url=f'https://visage.surgeplay.com/face/512/{user["minecraft_uid"]}.png' if user is not None else None
        )
        sql_resume_fields = sql.get_resume_fields_order_by_row(interaction.guild.id)
        if sql_resume_fields is not None:
            for index, field in enumerate(sql_resume_fields):
                embed.add_field(
                    name=field['field_name'],
                    value=f'{preview_labels[index] if preview_labels is not None else "*ПРЕДПРОСМОТР*"}',
                    inline=False)
        if interaction.user.avatar is not None:
            embed.set_footer(text=f'{interaction.user.name}#{interaction.user.discriminator}',
                             icon_url=interaction.user.avatar.url)
        return [embed, sql_resume_fields]
