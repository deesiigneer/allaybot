import nextcord
from nextcord.ui import View, Select, Modal, Button, button, TextInput, Item
from nextcord.utils import find
from nextcord import ButtonStyle, Interaction, Embed, Role, Emoji, PermissionOverwrite, Guild, SelectOption, \
    TextChannel, TextInputStyle, ChannelType
from database import sql
from sys import exc_info


class ButtonRecruiting(View):

    def __init__(self, guild: Guild = None):
        super().__init__(timeout=None)
        sql_recruiting = sql.get_recruiting(guild_id=guild.id) if guild is not None else None
        self.recruiting_to_city.disabled = True
        print('ButtonRecruiting1', sql_recruiting)
        if sql_recruiting:
            print('ButtonRecruiting2', sql_recruiting['status'])
            if sql_recruiting['status'] is True:
                self.recruiting_to_city.disabled = False

    @button(label='Оставить заявку', emoji='👋', style=ButtonStyle.green, row=1, custom_id='recruiting_to_city')
    async def recruiting_to_city(self, button: Button, interaction: Interaction):
        await interaction.response.send_modal(RecruitingModal(guild=interaction.guild,
                                                              preview=False,
                                                              interaction=interaction))


class CreateRecruiting(View):

    def __init__(self, interaction: Interaction = None):
        super().__init__(timeout=None)
        self.interaction = interaction if interaction is not None else None
        self.sql_recruiting = None
        if self.interaction is not None:
            self.sql_recruiting = sql.get_recruiting(self.interaction.guild.id)

    @button(label='Установка модуля [Заявки в город]', style=ButtonStyle.blurple, row=1, custom_id='simplified_installation')
    async def simplified_installation(self, btn: Button, interaction: Interaction):
        # button.disabled = True
        # self.extended_installation.disabled = True
        # await interaction.edit(view=self)
        btn.disabled = True
        # self.extended_installation.disabled = True
        await interaction.edit(view=self)
        sql_guild = sql.get_guild(interaction.guild.id)
        if sql_guild:
            if sql_guild['citizen_role_id'] is not None:
                embed = Embed(title=f'Набор в город {interaction.guild.name}!',
                              description=f'Нажмите кнопку ниже и заполните форму, для подачи заявки в замечательный '
                                          f'город **{interaction.guild.name}**!',
                              color=0x2f3136)
                if interaction.guild.icon is not None:
                    embed.set_thumbnail(url=interaction.guild.icon.url)
                else:
                    embed.set_thumbnail('https://static.wikia.nocookie.net/minecraft_gamepedia/images/4/45/Allay_JE2.gif')
                if interaction.guild.banner is not None:
                    embed.set_image(url=interaction.guild.banner.url)
                embed.set_author(name=f'powered by {interaction.client.user.name}',
                                 icon_url=interaction.client.user.avatar.url,
                                 url='https://discord.gg/VbyHaKRAaN')
                citizen = interaction.guild.get_role(sql_guild['citizen_role_id'])
                application_to_city_category = await interaction.guild.create_category('👷Набор в город')
                recruiting_channel = await application_to_city_category.create_text_channel(
                    name='👋ㆍнабор-в-город',
                    overwrites={interaction.guild.default_role: nextcord.PermissionOverwrite(read_messages=True,
                                                                                             send_messages=False)})
                resume_channel = await application_to_city_category.create_text_channel(
                    name='👷ㆍзаявки-в-город',
                    overwrites={interaction.guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
                                interaction.guild.me: nextcord.PermissionOverwrite(read_messages=True),
                                citizen: nextcord.PermissionOverwrite(
                                    read_messages=True,
                                    read_message_history=True,
                                    send_messages=False,
                                    view_channel=True)})
                recruiting_message = await recruiting_channel.send(embed=embed,
                                                                   view=ButtonRecruiting(interaction.guild))
                sql.add_recruiting(interaction.guild.id, recruiting_channel.id, recruiting_message.id, resume_channel.id,
                                   False)
                sql_resume = sql.get_resume_fields_order_by_row(interaction.guild.id)
                print('sql_resume', sql_resume)
                if not sql_resume:
                    sql.add_resume_field(interaction.guild.id, 'nickname', 'deesiigneer', False, True, 0)
                await recruiting_message.edit(view=ButtonRecruiting(interaction.guild))
                invite = await recruiting_channel.create_invite()
                print(invite.code)
                sql.update_invite(guild_id=interaction.guild.id, invite=invite.code)
                await interaction.send(f'Были созданы каналы:\n'
                                       f'{recruiting_channel.mention} - о городе, где находится кнопка для подачи '
                                       f'заявки в город {interaction.guild.name}\n'
                                       f'{resume_channel.mention} - где будут собираться заявки\n\n'
                                       f'Была создана ссылка для приглашения ||{invite.url}||, пожалуйста '
                                       f'не удаляйте её!\n'
                                       f'Перейдите в "👋 Заявки в город", что бы продолжить редактирование.',
                                       ephemeral=True)
            else:
                await interaction.send(f'Роль жителя не установлена для города {interaction.guild.name}!\n\n'
                                       f'Что бы установить используйте `/citizen`',
                                       ephemeral=True)


class ExtendedInstallationSelect(Select):

    def __init__(self, interaction: Interaction = None):
        self.interaction = interaction if interaction is not None else None
        select_options = []
        if self.interaction is not None:
            self.sql_recruiting = sql.get_recruiting(self.interaction.guild.id)
        select_options.append(SelectOption(
            label=f'test1',
            value=f'test2'))

        super().__init__(placeholder="Выбери",
                         min_values=1,
                         max_values=1,
                         options=select_options,
                         custom_id='ExtendedInstallationSelect',
                         row=0)

    async def callback(self, interaction: Interaction):
        pass


class ApplicationToCityButtons(View):

    def __init__(self, interaction: Interaction = None):
        self.interaction = interaction
        self.sql_recruiting = sql.get_recruiting(interaction.guild.id) if interaction is not None else None
        super().__init__(timeout=None)
        if self.sql_recruiting is not None and self.sql_recruiting['status'] is True:
            self.recruiting_status.label = 'Остановить прием заявок'
            self.recruiting_status.style = ButtonStyle.red
        elif self.sql_recruiting is not None and self.sql_recruiting['status'] is False:
            self.recruiting_status.label = 'Начать прием заявок'
            self.recruiting_status.style = ButtonStyle.green

    # @button(label='Редактировать канал с описанием города', style=ButtonStyle.blurple, row=1,
    #         custom_id='recruiting_edit')
    # async def recruiting_edit(self, button: Button, interaction: Interaction):
    #     self.stop()
        # await interaction.send(view=CreateReqruiting(interaction), ephemeral=True)
        # await interaction.response.send_modal(application_to_city_modal(guild=interaction.guild))

    @button(label='Редактировать шаблон заявки', style=ButtonStyle.blurple, row=1, custom_id='recruiting_edit_resume')
    async def recruiting_edit_resume(self, button: Button, interaction: Interaction):
        from handler import update_resume_preview
        update_resume_preview = await update_resume_preview(interaction)
        if update_resume_preview == [None, None]:
            # TODO: express installation
            await interaction.send(content='Извини дружище, видимо у тебя нет проходки на СПм '
                                           'или API SPWorlds упал.\n\n'
                                           'Проверить статус API можно тут -'
                                           'https://uptime.deesiigneer.ru/status/spworlds', ephemeral=True)
        elif update_resume_preview[1]:
            await interaction.edit(embed=update_resume_preview[0],
                                   view=ResumeEdit(interaction=interaction,
                                                   sql_recruiting=update_resume_preview[1]))
        # await interaction.response.send_modal(RecruitingModal(guild=interaction.guild))
        # await interaction.response.send_modal(application_to_city_modal(guild=interaction.guild))

    @button(row=2, custom_id='recruiting_status')
    async def recruiting_status(self, button: Button, interaction: Interaction):
        if self.sql_recruiting is None:
            self.sql_recruiting = sql.get_recruiting(interaction.guild.id)
        sql.update_recruiting(guild_id=interaction.guild.id,
                              recruiting_channel_id=self.sql_recruiting['recruiting_channel_id'],
                              recruiting_message_id=self.sql_recruiting['recruiting_message_id'],
                              resume_channel_id=self.sql_recruiting['resume_channel_id'],
                              status=False if bool(self.sql_recruiting['status']) is True else True)
        from handler import update_panel, update_applications_panel
        if self.sql_recruiting is not None and self.sql_recruiting['status'] is True:
            button.label = 'Остановить прием заявок'
            button.style = ButtonStyle.red
        elif self.sql_recruiting is not None and self.sql_recruiting['status'] is False:
            button.label = 'Начать прием заявок'
            button.style = ButtonStyle.green
        message = interaction.guild.get_channel(self.sql_recruiting['recruiting_channel_id']).get_partial_message(self.sql_recruiting['recruiting_message_id'])
        await message.edit(view=ButtonRecruiting(interaction.guild))
        await update_panel(interaction.client, interaction.guild)
        embed = await update_applications_panel(interaction.client, interaction.guild)
        await interaction.edit(view=ApplicationToCityButtons(interaction),
                               embed=embed)


class ResumeEdit(View):

    def __init__(self, interaction: Interaction = None,
                 sql_recruiting: list = None,
                 disable_add: bool = None,
                 disable_edit: bool = None,
                 disable_delete: bool = None):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.sql_resume = sql.get_resume_fields_order_by_row(interaction.guild.id) if interaction is not None else None
        self.edit_or_delete: bool = None
        if disable_add is not None and disable_add is True:
            self.resume_add_fields.disabled = True
        elif disable_edit is not None and disable_edit is True:
            self.resume_edit_fields.disabled = True
            self.edit_or_delete = True
        elif disable_delete is not None and disable_delete is True:
            self.resume_delete_fields.disabled = True
            self.edit_or_delete = False
        self.add_item(ResumeSelect(interaction, sql_recruiting, self.edit_or_delete))
        # if edit_or_delete is not None and edit_or_delete is True:
        #     print('111111111111')
        #     self.add_item(ResumeSelect(interaction=interaction, sql_resume_fields=sql_recruiting, do=edit_or_delete))
        #     self.resume_edit_fields.disabled = True
        # elif edit_or_delete is not None and edit_or_delete is False:
        #     print('222222222222')
        #     self.add_item(ResumeSelect(interaction=interaction, sql_resume_fields=sql_recruiting, do=edit_or_delete))
        #     self.resume_delete_fields.disabled = True

    @button(label='Добавить', style=ButtonStyle.green, row=1, custom_id='resume_add_fields')
    async def resume_add_fields(self, button: Button, interaction: Interaction):
        sql_resume_fields = sql.get_resume_fields_order_by_row(interaction.guild.id)
        if sql_resume_fields is not None:
            if len(sql_resume_fields) >= 5:
                button.disabled = True
                from handler import update_applications_panel
                update_applications_panel = await update_applications_panel(interaction.client, interaction.guild)
                await interaction.edit(view=ResumeEdit(interaction, sql_resume_fields, disable_add=True))
                await interaction.send('Нельзя добавить больше 5 полей.', ephemeral=True)
            else:
                row = None
                rows = []
                nums = [4, 3, 2, 1, 0]
                for field in sql_resume_fields:
                    rows.append(field['field_row'])
                    for num in nums:
                        if num not in rows:
                            row = num
                await interaction.response.send_modal(
                    ResumeModalConstructor(row=row, sql_resume_fields=sql_resume_fields))
        # await interaction.send(view=CreateReqruiting(interaction), ephemeral=True)
        # await interaction.response.send_modal(application_to_city_modal(guild=interaction.guild))

    @button(label='Редактировать', style=ButtonStyle.gray, row=1, custom_id='resume_edit_fields')
    async def resume_edit_fields(self, button: Button, interaction: Interaction):
        if self.sql_resume is None:
            self.sql_resume = sql.get_resume_fields_order_by_row(interaction.guild.id)
        button.disabled = True
        await interaction.edit(view=ResumeEdit(self.interaction, self.sql_resume, disable_edit=True))

    @button(label='Удалить', style=ButtonStyle.red, row=1, custom_id='resume_delete_fields')
    async def resume_delete_fields(self, button: Button, interaction: Interaction):
        if self.sql_resume is not None:
            if len(self.sql_resume) <= 1:
                button.disabled = True
                await interaction.edit(view=self)
                await interaction.send('Нельзя удалить последнее поле!', ephemeral=True)
                button.disabled = True
            else:
                button.disabled = True
        else:
            self.sql_resume = sql.get_resume_fields_order_by_row(interaction.guild.id)
        from handler import update_resume_preview
        update_resume_preview = await update_resume_preview(interaction)
        if update_resume_preview == [None, None]:
            # TODO: express installation
            await interaction.send(content='Извини дружище, видимо у тебя нет проходки на СПм '
                                           'или API SPWorlds упал.\n\n'
                                           'Проверить статус API можно тут -'
                                           'https://uptime.deesiigneer.ru/status/spworlds', ephemeral=True)
        else:
            await interaction.edit(embed=update_resume_preview[0],
                                   view=ResumeEdit(self.interaction, self.sql_resume,
                                                   disable_delete=True))

    @button(label='Предпросмотр', style=ButtonStyle.blurple, row=2, custom_id='preview_resume')
    async def preview_resume(self, button: Button, interaction: Interaction):
        await interaction.response.send_modal(RecruitingModal(guild=interaction.guild, preview=True,
                                                              interaction=self.interaction))

    @button(label='Назад', style=ButtonStyle.blurple, row=2, custom_id='preview_backward')
    async def preview_backward(self, button: Button, interaction: Interaction):
        from handler import update_applications_panel
        update_applications_panel = await update_applications_panel(interaction.client, interaction.guild)
        await interaction.edit(embed=update_applications_panel, view=ApplicationToCityButtons(interaction))

    # TODO: добавить кнопку назад

    # @button(label='Назад', style=ButtonStyle.blurple, row=2, custom_id='recruiting_edit_resume')
    # async def recruiting_edit_resume(self, button: Button, interaction: Interaction):
    #     await interaction.edit(view=ApplicationToCityButtons(interaction, self.sql_recruiting))


class ResumeSelect(Select):
    def __init__(self, interaction: Interaction = None, sql_resume_fields: list = None, do: bool = None):
        self.interaction = interaction if interaction is not None else None
        self.do = do if do is not None else None
        self.sql_resume_fields = sql_resume_fields if sql_resume_fields is not None else None
        select_options = []
        if sql_resume_fields is not None:
            for field in sql_resume_fields:
                print(field)
                select_options.append(SelectOption(label=str(field['field_name']),
                                                   description=str(field['field_placeholder']),
                                                   value=str(field['field_row'])))
        else:
            select_options.append(SelectOption(label='how do u see this?',
                                               value='hmm...'))
        print('do and sql', do, sql_resume_fields)
        super().__init__(placeholder=f"Выберите что нужно "
                                     f"{'редактировать' if do is True else 'удалить'}."
                                     f"" if do is not None else "",
                         disabled=True if do is None else False,
                         min_values=1,
                         max_values=1,
                         options=select_options,
                         custom_id='ResumeSelect_edit' if do is True else 'ResumeSelect_delete',
                         row=0)

    async def callback(self, interaction: Interaction):
        if self.do is not None and self.do is True:  # edit
            if self.sql_resume_fields is not None:
                for field in self.sql_resume_fields:
                    if int(field['field_row']) == int(self.values[0]):
                        print(3)
                        await interaction.response.send_modal(
                            ResumeModalConstructor(field['field_name'], field['field_row'], self.sql_resume_fields))
                        from handler import update_resume_preview
                        update_resume_preview = await update_resume_preview(interaction)
                        if update_resume_preview == [None, None]:
                            # TODO: express installation
                            await interaction.send(content='Извини дружище, видимо у тебя нет проходки на СПм '
                                                           'или API SPWorlds упал.\n\n'
                                                           'Проверить статус API можно тут -'
                                                           'https://uptime.deesiigneer.ru/status/spworlds', ephemeral=True)
                        else:
                            await interaction.edit_original_message(embed=update_resume_preview[0],
                                                                    view=ResumeEdit(interaction, update_resume_preview[1]))
        elif self.do is not None and self.do is False:  # delete
            sql.delete_resume_field(interaction.guild.id, int(self.values[0]))
            from handler import update_resume_preview
            update_resume_preview = await update_resume_preview(interaction)
            if update_resume_preview == [None, None]:
                # TODO: express installation
                await interaction.send(content='Извини дружище, видимо у тебя нет проходки на СПм '
                                               'или API SPWorlds упал.\n\n'
                                               'Проверить статус API можно тут -'
                                               'https://uptime.deesiigneer.ru/status/spworlds', ephemeral=True)
            else:
                await interaction.edit(embed=update_resume_preview[0],
                                       view=ResumeEdit(interaction, update_resume_preview[1]))


class ResumeModalConstructor(Modal):
    def __init__(self, edit: str = None, row: int = None, sql_resume_fields: list = None):
        self.row = row
        self.edit = edit
        self.sql_resume_fields = sql_resume_fields
        title = f'Создание нового поля'
        if edit is not None:
            title = f'Редактирование поля {edit}'
        if len(title) > 45:
            title = f'{title[:42]}...'
        super().__init__(title=title, timeout=None)
        self.name = TextInput(
            label='Название поля',
            placeholder='Введите название создаваемого поля',
            style=TextInputStyle.paragraph,
            custom_id='ResumeModalConstructor_name',
            min_length=1,
            max_length=45,
            required=True)
        self.add_item(self.name)
        self.placeholder = TextInput(
            label='Плейсхолдер поля',
            placeholder='Введите текст подсказки, который будет находиться внутри поля',
            style=TextInputStyle.paragraph,
            custom_id='ResumeModalConstructor_placeholder',
            min_length=0,
            max_length=100,
            required=False)
        self.add_item(self.placeholder)
        self.style = TextInput(
            label='Отображать как многострочное поле <textarea>',
            placeholder='Введите любой символ для применения возможности ввода '
                        'нескольких строк текста в создаваемое поле',
            style=TextInputStyle.paragraph,
            custom_id='ResumeModalConstructor_style',
            min_length=0,
            max_length=1,
            required=False)
        self.add_item(self.style)
        self.requierd = TextInput(
            label='Обязательность поля',
            placeholder='Введите любой символ, если поле должно быть обязательным',
            style=TextInputStyle.paragraph,
            custom_id='ResumeModalConstructor_required',
            min_length=0,
            max_length=1,
            required=False)
        self.add_item(self.requierd)

    async def callback(self, interaction: Interaction):
        if self.edit is None:
            sql.add_resume_field(interaction.guild.id,
                                 field_name=self.name.value,
                                 field_placeholder=self.placeholder.value if self.placeholder.value != "" else None,
                                 field_style=True if self.style.value != "" else False,
                                 field_required=True if self.requierd.value != "" else False,
                                 field_row=self.row)
        elif self.edit is not None:
            sql.update_resume_field_row(interaction.guild.id,
                                        field_name=self.name.value,
                                        field_placeholder=self.placeholder.value if self.placeholder.value != "" else None,
                                        field_style=True if self.style.value != "" else False,
                                        field_required=True if self.requierd.value != "" else False,
                                        field_row=self.row)
        from handler import update_resume_preview
        update_resume_preview = await update_resume_preview(interaction)
        if update_resume_preview == [None, None]:
            # TODO: express installation
            await interaction.send(content='Извини дружище, видимо у тебя нет проходки на СПм '
                                           'или API SPWorlds упал.\n\n'
                                           'Проверить статус API можно тут -'
                                           'https://uptime.deesiigneer.ru/status/spworlds', ephemeral=True)
        else:
            await interaction.edit(embed=update_resume_preview[0],
                                   view=ResumeEdit(interaction, self.sql_resume_fields))


class RecruitingModal(Modal):
    def __init__(self, guild: Guild = None, preview: bool = None, interaction: Interaction = None):
        self.interaction = interaction if interaction is not None else None
        title = f'Заявка в город {guild.name if guild is not None else None}'
        self.preview = preview if preview is not None else None
        self.sql_resume_fields = sql.get_resume_fields_order_by_row(guild.id)

        if len(title) > 45:
            title = f'{title[:42]}...'
        super().__init__(title=title, timeout=None)
        # self.add_item(TextInput(
        #
        # ))

        if self.sql_resume_fields is not None:
            self.labels = []
            for field in self.sql_resume_fields:
                self.labels.append(TextInput(label=field['field_name'],
                                        placeholder=field['field_placeholder'],
                                        style=TextInputStyle.paragraph if bool(
                                            field['field_style']) is True else TextInputStyle.short,
                                        required=True if bool(field['field_required']) is True else False,
                                        row=field['field_row'],
                                        custom_id=f'RecruitingModal_{field["field_name"]}_{field["field_row"]}',
                                        max_length=1024))
            for label in self.labels:
                self.add_item(label)

    async def callback(self, interaction: Interaction):
        message = await interaction.send('Нужно подождать...', ephemeral=True)
        if self.preview is True:
            from handler import update_resume_preview
            preview_labels = []
            for label in self.labels:
                preview_labels.append(label.value)
            update_resume_preview = await update_resume_preview(interaction, preview_labels=preview_labels)
            if update_resume_preview == [None, None]:
                # TODO: express installation
                await message.edit(content='Извини дружище, видимо у тебя нет проходки на СПм '
                                               'или API SPWorlds упал.\n\n'
                                               'Проверить статус API можно тут -'
                                               'https://uptime.deesiigneer.ru/status/spworlds')
            else:
                await self.interaction.edit_original_message(embed=update_resume_preview[0],
                                            view=ResumeEdit(interaction, update_resume_preview[1])) if self.interaction is not None else None
                await message.delete()
        elif self.preview is False:
            sql_recruiting = sql.get_recruiting(interaction.guild.id)
            channel = interaction.guild.get_channel(sql_recruiting['resume_channel_id'])
            from handler import update_resume_preview
            preview_labels = []
            for label in self.labels:
                preview_labels.append(label.value)
            update_resume_preview = await update_resume_preview(interaction, preview_labels, channel)
            if update_resume_preview == [None, None]:
                # TODO: express installation
                await message.edit(content='Извини дружище, видимо у тебя нет проходки на СПм '
                                               'или API SPWorlds упал.\n\n'
                                               'Проверить статус API можно тут -'
                                               'https://uptime.deesiigneer.ru/status/spworlds')
            else:
                thread = await interaction.channel.create_thread(name=f'Заявка-{interaction.user.display_name}',
                                                        type=ChannelType.private_thread)
                await thread.add_user(interaction.user)
                await message.edit(f'{interaction.user.mention}, ваша заявка была отправлена!\n'
                                       f'Все действия по вашей заявке вы всегда можете посмотреть тут -> {thread.jump_url}')
                message = await channel.send(embed=update_resume_preview[0])
                await message.add_reaction(interaction.client.get_emoji(1102183935762497546))
                await message.add_reaction(interaction.client.get_emoji(1102183934101553222))
                await thread.send(embed=update_resume_preview[0])


# class application_to_city_modal2(Modal):
#     def __init__(self, guild: Guild, field: int):
#         self.field = field
#         super().__init__(title=f'Заявка в город {guild.name} (поле {field})', timeout=None, custom_id=f'atcm_{self.field}')
#         self.field_name = TextInput(label='Заголовок',required=True,min_length=1,max_length=256)
#         self.add_item(self.field_name)
#
#         self.field_value = TextInput(label='Описание',required=True,min_length=1,max_length=1024)
#         self.add_item(self.field_value)
#
#     async def callback(self, interaction: Interaction):
#         channel_id = sql.one(f"SELECT application_channel_id "
#                              f"FROM application_to_city "
#                              f"WHERE guild_id = '{interaction.guild.id}'")
#         if channel_id is not None:
#             sql.commit(f"UPDATE application_to_city SET "
#                        f"field_{self.field}_name = '{self.field_name.value}',"
#                        f"field_{self.field}_value = '{self.field_value.value}' "
#                        f"WHERE guild_id = '{interaction.guild.id}'")
#         else:
#             channel = await interaction.guild.create_text_channel(name='👋ㆍзаявки-в-город', overwrites={
#                 interaction.guild.default_role: PermissionOverwrite(read_messages=False)})
#             sql.commit(f"INSERT INTO application_to_city "
#                        f"(guild_id, application_channel_id, field_{self.field}_name, field_{self.field}_value)"
#                        f"VALUES('{interaction.guild.id}',"
#                        f" {channel.id if channel is not None else None},"
#                        f" {self.field_name.value},"
#                        f" {self.field_value.value})")
#         if self.field >= 5:
#             await interaction.response.send_message('yes')
#         else:
#             print(True)
#             print(self.field)
#             print(self.field+1)
#             await interaction.response.defer()
#             await interaction.response.send_modal(modal=application_to_city_modal2(guild=interaction.guild,field=4))
