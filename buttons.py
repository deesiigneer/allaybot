import nextcord
from nextcord.ui import View, Select, Modal, Button, button, TextInput
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
            print('ButtonRecruiting2', sql_recruiting[3])
            if sql_recruiting[3] is True:
                self.recruiting_to_city.disabled = False

    @button(label='Оставить заявку', emoji='👋', style=ButtonStyle.green, row=1, custom_id='recruiting_to_city')
    async def recruiting_to_city(self, button: Button, interaction: Interaction):
        await interaction.response.send_modal(RecruitingModal(guild=interaction.guild,
                                                              preview=False,
                                                              interaction=interaction))


class BotPanelButtons(View):

    def __init__(self):
        super().__init__(timeout=None)

    @button(label='Набор в город', emoji='👋', style=ButtonStyle.blurple, row=1, custom_id='application_to_city')
    async def application_to_city(self, button: Button, interaction: Interaction):
        from handler import update_applications_panel
        sql_recruiting = sql.get_recruiting(interaction.guild.id)
        embeds = [await update_applications_panel(interaction.client, interaction.guild)]
        if sql_recruiting:
            await interaction.response.send_message(embeds=embeds,
                                                    view=ApplicationToCityButtons(interaction=interaction),
                                                    ephemeral=True)
            #  TODO
        else:
            await interaction.send(content=f'Модуль `Набор в город` для `{interaction.guild.name}` ещё не установлены',
                                   embeds=embeds,
                                   view=CreateReqruiting(interaction),
                                   ephemeral=True)
        # await interaction.response.send_modal(application_to_city_modal(guild=interaction.guild))

    @button(label='[in dev] Список жителей', disabled=True, emoji='👷', style=ButtonStyle.blurple, row=1,
            custom_id='citizens')
    async def citizens(self, interaction: Interaction):
        pass

    @button(label='Обновить', emoji='🔃', style=ButtonStyle.blurple, row=2, custom_id='settings_panel_update')
    async def update(self, button: Button, interaction: Interaction):
        try:
            from handler import update_panel, Check
            channel = interaction.guild.get_channel(interaction.channel.id)
            await Check(interaction.client, interaction.guild).comparison_database_to_guild(interaction, channel,
                                                                                            interaction.message)
            await update_panel(interaction.client, interaction.guild)
            await  interaction.message.edit(view=BotPanelButtons())
            # await interaction.edit(embeds=embeds, view=BotPanelButtons())
        except Exception as e:
            raise f"Update Exception {e}"


class CreateReqruiting(View):

    def __init__(self, interaction: Interaction = None):
        super().__init__(timeout=None)
        self.interaction = interaction if interaction is not None else None
        self.sql_recruiting = None
        if self.interaction is not None:
            self.sql_recruiting = sql.get_recruiting(self.interaction.guild.id)
        # self.add_item(ExtendedInstallationSelect())

    # @button(label='Расширенная установка', style=ButtonStyle.blurple, row=1, custom_id='extended_installation')
    # async def extended_installation(self, button: Button, interaction: Interaction):
        # await interaction.response.send_modal(application_to_city_modal(guild=interaction.guild))

    @button(label='Установка модуля [Заявки в город]', style=ButtonStyle.blurple, row=1, custom_id='simplified_installation')
    async def simplified_installation(self, button: Button, interaction: Interaction):
        # button.disabled = True
        # self.extended_installation.disabled = True
        # await interaction.edit(view=self)
        button.disabled = True
        self.extended_installation.disabled = True
        await interaction.edit(view=self)
        sql_guild = sql.get_guild(interaction.guild.id)
        if sql_guild:
            if sql_guild[2] is not None:
                citizen = interaction.guild.get_role(sql_guild[2])
                applcation_to_city_category = await interaction.guild.create_category('👷Набор в город')
                recruiting_channel = await applcation_to_city_category.create_text_channel(name='👋ㆍнабор-в-город')
                resume_channel = await applcation_to_city_category.create_text_channel(name='👷ㆍзаявки-в-город')
                await resume_channel.set_permissions(target=citizen, overwrite=nextcord.PermissionOverwrite(
                    read_messages=True,
                    read_message_history=True,
                    send_messages=False,
                    view_channel=True))
                await recruiting_channel.set_permissions(target=citizen, overwrite=nextcord.PermissionOverwrite(
                    view_channel=False))
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
                recruiting_message = await recruiting_channel.send(embed=embed,
                                                                   view=ButtonRecruiting(interaction.guild))
                sql.add_recruiting(interaction.guild.id, recruiting_channel.id, recruiting_message.id, resume_channel.id,
                                   False)
                sql_resume = sql.get_resume_fields_order_by_row(interaction.guild.id)
                print('sql_resume', sql_resume)
                if not sql_resume:
                    sql.add_resume_field(interaction.guild.id, 'nickname', 'deesiigneer', False, True, 0)
                await recruiting_message.edit(view=ButtonRecruiting(interaction.guild))
                await interaction.send(f'Были созданы каналы:\n'
                                       f'{recruiting_channel.mention} - о городе, где находится кнопка для подачи '
                                       f'заявки в город {interaction.guild.name}\n'
                                       f'{resume_channel.mention} - где будут собираться заявки\n\n'
                                       f'Нажмите кнопку "👋 Набор в город", что бы продолжить редактирование.', ephemeral=True)
            else:
                await interaction.send(f'Роль жителя не установлена для города {interaction.guild.name}!\n\n'
                                       f'Что бы установить используйте `/citizen`',
                                       ephemeral=True)


# class ExtendedInstallation(View):
#
#     def __init__(self, interaction: Interaction = None):
#         super().__init__(timeout=None)
#         self.interaction = interaction if interaction is not None else None
#
#     @button(label='Сохранить', style=ButtonStyle.green, row=1, custom_id='extended_installation')
#     async def extended_installation(self, button: Button, interaction: Interaction):
#         await self.interaction.edit_original_message(view=self.interaction)
#         self.stop()
#         # await interaction.response.send_modal(application_to_city_modal(guild=interaction.guild))
#
#     @button(label='Назад', style=ButtonStyle.blurple, row=1, custom_id='simplified_installation')
#     async def simplified_installation(self, button: Button, interaction: Interaction):
#         await self.interaction.edit_original_message(view=CreateReqruiting(self.interaction))
        # await interaction.response.send_modal(application_to_city_modal(guild=interaction.guild))
        # await interaction.response.send_modal(application_to_city_modal(guild=interaction.guild))


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
        if self.sql_recruiting is not None and self.sql_recruiting[3] is True:
            self.recruiting_status.label = 'Остановить прием заявок'
            self.recruiting_status.style = ButtonStyle.red
        elif self.sql_recruiting is not None and self.sql_recruiting[3] is False:
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
                              recruiting_channel_id=self.sql_recruiting[1],
                              recruiting_message_id=self.sql_recruiting[4],
                              resume_channel_id=self.sql_recruiting[2],
                              status=False if bool(self.sql_recruiting[3]) is True else True)
        from handler import update_panel, update_applications_panel
        if self.sql_recruiting is not None and self.sql_recruiting[3] is True:
            button.label = 'Остановить прием заявок'
            button.style = ButtonStyle.red
        elif self.sql_recruiting is not None and self.sql_recruiting[3] is False:
            button.label = 'Начать прием заявок'
            button.style = ButtonStyle.green
        await update_panel(interaction.client, interaction.guild)
        embed = await update_applications_panel(interaction.client, interaction.guild)
        await interaction.edit(view=ApplicationToCityButtons(interaction),
                               embed=embed)
        message = interaction.guild.get_channel(self.sql_recruiting[1]).get_partial_message(self.sql_recruiting[4])
        await message.edit(view=ButtonRecruiting(interaction.guild))


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
                    rows.append(field[5])
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
                select_options.append(SelectOption(label=str(field[1]),
                                                   description=str(field[2]),
                                                   value=str(field[5])))
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
                    if int(field[5]) == int(self.values[0]):
                        print(3)
                        await interaction.response.send_modal(
                            ResumeModalConstructor(field[1], field[5], self.sql_resume_fields))
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
            label='Имя',
            placeholder='Имя поля (Как текст выше)',
            style=TextInputStyle.paragraph,
            custom_id='ResumeModalConstructor_name',
            min_length=1,
            max_length=45,
            required=True)
        self.add_item(self.name)
        self.placeholder = TextInput(
            label='Заполнитель',
            placeholder='Заполняет поле если пустое (как сейчас).\nМожно оставить пустым',
            style=TextInputStyle.paragraph,
            custom_id='ResumeModalConstructor_placeholder',
            min_length=0,
            max_length=100,
            required=False)
        self.add_item(self.placeholder)
        self.style = TextInput(
            label='Стиль',
            placeholder='Если оставить пустым, будет как поле ниже.\n'
                        'Можете написать тут, что бы стиль был как это поле.',
            style=TextInputStyle.paragraph,
            custom_id='ResumeModalConstructor_style',
            min_length=0,
            max_length=1,
            required=False)
        self.add_item(self.style)
        self.requierd = TextInput(
            label='Обязателен?',
            placeholder='Если оставить пустым, будет необязательным.\n'
                        'Или написать что-то, что бы стало обязательным.',
            style=TextInputStyle.short,
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
                self.labels.append(TextInput(label=field[1],
                                        placeholder=field[2],
                                        style=TextInputStyle.paragraph if bool(
                                            field[3]) is True else TextInputStyle.short,
                                        required=True if bool(field[4]) is True else False,
                                        row=field[5],
                                        custom_id=f'RecruitingModal_{field[1]}_{field[5]}',
                                        max_length=1024))
            for label in self.labels:
                self.add_item(label)

    async def callback(self, interaction: Interaction):
        if self.preview is True:
            from handler import update_resume_preview
            preview_labels = []
            for label in self.labels:
                preview_labels.append(label.value)
            update_resume_preview = await update_resume_preview(interaction, preview_labels=preview_labels)
            if update_resume_preview == [None, None]:
                # TODO: express installation
                await interaction.send(content='Извини дружище, видимо у тебя нет проходки на СПм '
                                               'или API SPWorlds упал.\n\n'
                                               'Проверить статус API можно тут -'
                                               'https://uptime.deesiigneer.ru/status/spworlds', ephemeral=True)
            else:
                await self.interaction.edit_original_message(embed=update_resume_preview[0],
                                            view=ResumeEdit(interaction, update_resume_preview[1])) if self.interaction is not None else None
        elif self.preview is False:
            sql_recruiting = sql.get_recruiting(interaction.guild.id)
            channel = interaction.guild.get_channel(sql_recruiting[2])
            from handler import update_resume_preview
            preview_labels = []
            for label in self.labels:
                preview_labels.append(label.value)
            update_resume_preview = await update_resume_preview(interaction, preview_labels, channel)
            if update_resume_preview == [None, None]:
                # TODO: express installation
                await interaction.send(content='Извини дружище, видимо у тебя нет проходки на СПм '
                                               'или API SPWorlds упал.\n\n'
                                               'Проверить статус API можно тут -'
                                               'https://uptime.deesiigneer.ru/status/spworlds', ephemeral=True)
            else:
                thread = await interaction.channel.create_thread(name=f'Заявка-{interaction.user.display_name}',
                                                        type=ChannelType.private_thread)
                await thread.add_user(interaction.user)
                await interaction.send(f'{interaction.user.mention}, ваша заявка была отправлена!\n'
                                       f'Все действия по вашей заявке вы всегда можете посмотреть тут -> {thread.jump_url}', ephemeral=True)
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
