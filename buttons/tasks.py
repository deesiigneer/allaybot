import nextcord
from nextcord.ui import View, Select, Modal, Button, button, TextInput, Item
from nextcord.utils import find
from nextcord import ButtonStyle, Interaction, Embed, Role, Emoji, PermissionOverwrite, Guild, SelectOption, \
    TextChannel, TextInputStyle, ChannelType, ForumTag, SortOrderType, Client, ForumChannel, Thread
from database import sql
from nextcord.ext import menus
from sys import exc_info


async def tasks_embed(bot: Client, guild: Guild, tasks_guild, current_page=None, max_pages=None, edit: bool = None, delete: bool = None):
    embed = Embed(color=0x2f3136)
    if guild is None:
        embed.title = 'Error'
    else:
        embed.title = 'Задания созданные мной:'
        embed.description = ''
        embed.set_author(name=guild.name,
                         url=f'https://discord.gg/{tasks_guild["invite"]}',
                         icon_url=guild.icon.url if guild.icon is not None else None)
        embed.set_footer(text=guild.id)
        embed.add_field(name='Кол-во жителей:', value=len(guild.get_role(tasks_guild['citizen_role_id']).members))
        embed.add_field(name='Ссылка на дискорд сервер города:', value=f'https://discord.gg/{tasks_guild["invite"]}')
        if guild.banner is not None:
            embed.image.url = guild.banner.url
    return embed


class TasksModuleSetup(View):
    def __init__(self, interaction: Interaction = None):
        super().__init__(timeout=None)
        self.interaction = interaction if interaction is not None else None
        self.sql_recruiting = None
        if self.interaction is not None:
            self.sql_recruiting = sql.get_recruiting(self.interaction.guild.id)

    @button(label='Установка модуля [Задания]', style=ButtonStyle.blurple, row=1, custom_id='tasks_installation')
    async def tasks_installation(self, btn: Button, interaction: Interaction):
        if 'COMMUNITY' in interaction.guild.features:
            # button.disabled = True
            # self.extended_installation.disabled = True
            # await interaction.edit(view=self)
            btn.disabled = True
            # self.extended_installation.disabled = True
            await interaction.edit(view=self)
            sql_guild = sql.get_guild(interaction.guild.id)
            if sql_guild:
                if sql_guild['citizen_role_id'] is not None:
                    embed = Embed(title=f'Задания города {interaction.guild.name}!',
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
                    overwrites = {interaction.guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
                                  interaction.guild.me: nextcord.PermissionOverwrite(read_messages=True),
                                  citizen: nextcord.PermissionOverwrite(
                                        read_messages=True,
                                        read_message_history=True,
                                        send_messages=False,
                                        view_channel=True)}
                    tasks_category = await interaction.guild.create_category('🔨Задания')
                    forum_tags = [ForumTag(name='Глобальные заказы', moderated=True, emoji='🌐'),
                                  ForumTag(name='Ожидают', moderated=True, emoji='⏳'),
                                  ForumTag(name='В процессе', moderated=True, emoji='💪'),
                                  ForumTag(name='Выполненные', moderated=True, emoji='✔')]
                    tasks_channel = await tasks_category.create_forum_channel(
                        name='🧱Задания',
                        topic=f'**Пожалуйста, не создавайте/удаляйте/редактируйте публикации! Бот сам всё сделает.**',
                        overwrites=overwrites,
                        available_tags=forum_tags,
                        default_reaction='🔨',
                        default_sort_order=SortOrderType.creation_date)
                    embed = Embed(title='test title', description='test description') # TODO
                    thread = await tasks_channel.create_thread(name='🖌️Оформление заданий', embed=embed,
                                                               view=TasksChoice())
                    flgs = nextcord.ChannelFlags()
                    flgs.pinned = True
                    await thread.edit(flags=flgs)
                    global_tag = None
                    waiting_tag = None
                    in_progress_tag = None
                    done_tag = None
                    webhook = await tasks_channel.create_webhook(name=f'{interaction.client.user.display_name}',
                                                       avatar=interaction.client.user.avatar,
                                                       reason='Создание модуля "Задания"')
                    for tag in tasks_channel.available_tags:
                        if tag.name == 'Глобальные заказы':
                            global_tag = tag.id
                        elif tag.name == 'Ожидают':
                            waiting_tag = tag.id
                        elif tag.name == 'В процессе':
                            in_progress_tag = tag.id
                        elif tag.name == 'Выполненные':
                            done_tag = tag.id
                    sql.update_guild_task(guild_id=interaction.guild.id,
                                          task_channel_id=tasks_channel.id,
                                          task_issue_thread_id=thread.id,
                                          task_tag_global_id=global_tag if global_tag is not None else None,
                                          task_tag_waiting_id=waiting_tag if waiting_tag is not None else None,
                                          task_tag_in_progress_id=in_progress_tag if in_progress_tag is not None else None,
                                          task_tag_complete_id=done_tag if done_tag is not None else None,
                                          task_webhook_url=webhook.url)
                    # check if help
                    # recruiting_message = await tasks_channel.send(embed=embed,
                    #                                                    view=ButtonRecruiting(interaction.guild))
                    # sql.add_recruiting(interaction.guild.id, recruiting_channel.id, recruiting_message.id, resume_channel.id,
                    #                    False)
                    # sql_resume = sql.get_resume_fields_order_by_row(interaction.guild.id)
                    # print('sql_resume', sql_resume)
                    # if not sql_resume:
                    #     sql.add_resume_field(interaction.guild.id, 'nickname', 'deesiigneer', False, True, 0)
                    # await recruiting_message.edit(view=ButtonRecruiting(interaction.guild))
                    # await interaction.send(f'Были созданы каналы:\n'
                    #                        f'{recruiting_channel.mention} - о городе, где находится кнопка для подачи '
                    #                        f'заявки в город {interaction.guild.name}\n'
                    #                        f'{resume_channel.mention} - где будут собираться заявки\n\n'
                    #                        f'Нажмите кнопку "👋 Набор в город", что бы продолжить редактирование.', ephemeral=True)
                else:
                    await interaction.send(f'Роль жителя не установлена для города {interaction.guild.name}!\n\n'
                                           f'Что бы установить используйте `/citizen`',
                                           ephemeral=True)
        else:
            await interaction.send(f'На вашем сервере не включен режим `Сообщество`', ephemeral=True)


class TasksConfig(View):

    def __init__(self):
        super().__init__(timeout=None)

    @button(label='Настройка глобальных заказов', emoji='👋', style=ButtonStyle.green, row=1, custom_id='task_accept')
    async def task_accept(self, button: Button, interaction: Interaction):
        pass


class TasksAccept(View):

    def __init__(self, thread: int = None):
        thread_id = thread
        super().__init__(timeout=None)

    @button(label='Принять', emoji='👋', style=ButtonStyle.green, row=1, custom_id=f'task_accept')
    async def task_accept(self, button: Button, interaction: Interaction):
        task_id = None
        embed = None
        for embed in interaction.message.embeds:
            task_id = f'{interaction.channel.name.split("#")[1].split(" ")[0]}'
        sql_task = sql.get_task_by_task_id(int(task_id)+1)
        print(sql_task)
        if sql_task:
            customer_guild = interaction.client.get_guild(sql_task['customer_guild_id'])
            print(customer_guild, sql_task['customer_guild_id'])
            customer_thread = await interaction.client.fetch_channel(sql_task['customer_thread_id'])
            print('123321', customer_thread, sql_task['customer_thread_id'])
            customer = await interaction.client.fetch_user(sql_task['customer_id'])
            _embed = None
            for _embed in interaction.message.embeds:
                _embed: Embed = _embed
            user = interaction.user
            await interaction.send(f'{user.mention}, ты принял заказ #{task_id}!', ephemeral=True)
            user = sql.get_user(interaction.user.id)
            from pyspapi import SPAPI, MojangAPI
            if user:
                username = MojangAPI.get_username(user["minecraft_uid"])
                await customer_thread.send(content=f'{customer.mention}, '
                                                   f'{interaction.user.mention} (`'
                                                   f'{username}`) '
                                                   f'принял Ваш заказ!\n\n'
                                                   f'Вы можете вести диалог прямо в этом канале!',
                                           embed=embed)
                footer_text = f"Принял - {username}"
                avatar_url = f'https://visage.surgeplay.com/face/512/{user["minecraft_uid"]}.png'
            else:
                spapi = SPAPI('6273cba5-add3-44b8-a9a6-d528fcf0f29a',
                              'hQvWsc9FssggbtNXukG/3XbgNXtyTgos')
                try:
                    user = spapi.get_user(interaction.user.id)
                except:
                    user = None
                m_user = MojangAPI.get_uuid(user.username)
                if user:
                    sql.add_user(interaction.user.id, MojangAPI.get_uuid(user.username))
                    await customer_thread.send(content=f'{customer.mention}, '
                                                       f'{interaction.user.mention} (`{user.username}`) '
                                                       f'принял Ваш заказ!\n\n'
                                                       f'Вы можете вести диалог прямо в этом канале!',
                                               embed=embed)
                avatar_url = f'https://visage.surgeplay.com/face/512/{m_user}.png' if user is not None else None
                footer_text = f"Принял - {user.username}"
            _embed.set_footer(text=footer_text, icon_url=avatar_url)
            print('3333', _embed.footer.text)
            self.disabled = True
            sql_guilds: dict = sql.get_guilds()
            print("guilds", type(sql_guilds), sql_guilds)
            for sql_guild in sql_guilds:
                guild = interaction.client.get_guild(sql_guild['guild_id'])
                for thread in guild.threads:
                    # TODO: check solo task
                    if thread.name.startswith(f"🌐 #{task_id} {sql_task['item']}"):
                        print('th name',thread.name)
                        forum_tags = [ForumTag(name='Глобальный', id=sql_guild['task_tag_global_id']),
                            ForumTag(name='Ожидают', id=sql_guild['task_tag_in_progress_id'])]
                        await thread.edit(applied_tags=forum_tags)
                        async for message in thread.history(limit=10, oldest_first=True):
                            if message.author == interaction.client.user and message.content == '':
                                print('yes')
                                print(_embed.footer.text)
                                print(button.disabled)
                                print(self.disabled)
                                button.disabled = True
                                print(button.disabled)
                                await message.edit(embed=_embed, view=self)
                    elif thread.name.startswith(f"#{task_id} {sql_task['item']}"):
                        thread = interaction.channel
                        print('solo')
                        forum_tags = [ForumTag(name='Ожидают', id=sql_guild['task_tag_in_progress_id'])]
                        await thread.edit(applied_tags=forum_tags)
                        button.disabled = True
                        await interaction.edit(embed=_embed, view=self)

            sql.update_task_accept(interaction.user.id,
                                   interaction.channel.id,
                                   interaction.guild.id,
                                   interaction.message.id,
                                   sql_task['customer_thread_id'])
        else:
            await interaction.send('something wrong...', ephemeral=True)


class TasksDone(View):

    def __init__(self, thread: int = None):
        thread_id = thread
        super().__init__(timeout=None)

    @button(label='Завершить', emoji='👋', style=ButtonStyle.green, row=1, custom_id=f'task_accept')
    async def task_accept(self, button: Button, interaction: Interaction):
        task_id = None
        embed = None
        for embed in interaction.message.embeds:
            task_id = f'{interaction.channel.name.split("#")[1].split(" ")[0]}'
        sql_task = sql.get_task_by_task_id(int(task_id)+1)
        print(sql_task)
        if sql_task:
            customer_guild = interaction.client.get_guild(sql_task['customer_guild_id'])
            print(customer_guild, sql_task['customer_guild_id'])
            customer_thread = await interaction.client.fetch_channel(sql_task['customer_thread_id'])
            print('123321', customer_thread, sql_task['customer_thread_id'])
            customer = await interaction.client.fetch_user(sql_task['customer_id'])
            _embed = None
            for _embed in interaction.message.embeds:
                _embed: Embed = _embed
            user = interaction.user
            await interaction.send(f'{user.mention}, ты принял заказ #{task_id}!', ephemeral=True)
            user = sql.get_user(interaction.user.id)
            from pyspapi import SPAPI, MojangAPI
            if user:
                username = MojangAPI.get_username(user["minecraft_uid"])
                await customer_thread.send(content=f'{customer.mention}, '
                                                   f'{interaction.user.mention} (`'
                                                   f'{username}`) '
                                                   f'принял Ваш заказ!\n\n'
                                                   f'Вы можете вести диалог прямо в этом канале!',
                                           embed=embed)
                footer_text = f"Принял - {username}"
                avatar_url = f'https://visage.surgeplay.com/face/512/{user["minecraft_uid"]}.png'
            else:
                spapi = SPAPI('6273cba5-add3-44b8-a9a6-d528fcf0f29a',
                              'hQvWsc9FssggbtNXukG/3XbgNXtyTgos')
                try:
                    user = spapi.get_user(interaction.user.id)
                except:
                    user = None
                m_user = MojangAPI.get_uuid(user.username)
                if user:
                    sql.add_user(interaction.user.id, MojangAPI.get_uuid(user.username))
                    await customer_thread.send(content=f'{customer.mention}, '
                                                       f'{interaction.user.mention} (`{user.username}`) '
                                                       f'принял Ваш заказ!\n\n'
                                                       f'Вы можете вести диалог прямо в этом канале!',
                                               embed=embed)
                avatar_url = f'https://visage.surgeplay.com/face/512/{m_user}.png' if user is not None else None
                footer_text = f"Принял - {user.username}"
            _embed.set_footer(text=footer_text, icon_url=avatar_url)
            print('3333', _embed.footer.text)
            self.disabled = True
            sql_guilds: dict = sql.get_guilds()
            print("guilds", type(sql_guilds), sql_guilds)
            for sql_guild in sql_guilds:
                guild = interaction.client.get_guild(sql_guild['guild_id'])
                for thread in guild.threads:
                    # TODO: check solo task
                    if thread.name.startswith(f"🌐 #{task_id+1} {sql_task['item']}"):
                        print('some checks:', interaction.channel_id, thread.id)
                        forum_tags = [ForumTag(name='Глобальный', id=sql_guild['task_tag_global_id']),
                            ForumTag(name='Ожидают', id=sql_guild['task_tag_in_progress_id'])]
                        await thread.edit(applied_tags=forum_tags)
                        async for message in thread.history(limit=10, oldest_first=True):
                            if message.author == interaction.client.user and message.content == '':
                                print(message.channel.id, interaction.channel_id)
                                if thread.id == interaction.channel_id:
                                    await interaction.send("test")
                                else:
                                    button.disabled = True
                                    await message.edit(embed=_embed, view=self)
                                print('yes')
                                print(_embed.footer.text)
                                print(button.disabled)
                                print(self.disabled)
                                print(button.disabled)
                    elif thread.name.startswith(f"#{task_id} {sql_task['item']}"):
                        thread = interaction.channel
                        print('solo')
                        forum_tags = [ForumTag(name='Ожидают', id=sql_guild['task_tag_in_progress_id'])]
                        await thread.edit(applied_tags=forum_tags)
                        button.disabled = True
                        await interaction.edit(embed=_embed, view=self)

            sql.update_task_accept(interaction.user.id,
                                   interaction.channel.id,
                                   interaction.guild.id,
                                   interaction.message.id,
                                   sql_task['customer_thread_id'])
        else:
            await interaction.send('something wrong...', ephemeral=True)


class TasksChoice(View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TaskChoiceSelect())


class TaskInProgress(View):

    def __init__(self):
        super().__init__(timeout=None)
        # self.add_item(TaskChoiceSelect())


class TaskInProgressSelect(Select):
    def __init__(self):
        select_options = [
            SelectOption(
                label=f'Выполнено.',
                description='.',
                emoji='🆕',
                value=f'task_done'
            ),
            SelectOption(
                label='Смена исполнителя.',
                description='Расторгает задание с исполнителем.',
                emoji='✏️',
                value='change_contactor'
            )
        ]

        super().__init__(placeholder='Выберите действие',
                         options=select_options,
                         custom_id='TaskInProgressSelect',
                         row=0,
                         disabled=False)


class TaskChoiceSelect(Select):
    def __init__(self):
        select_options = [
            SelectOption(
                label=f'Новая задача.',
                description='Создание новой задачи.',
                emoji='🆕',
                value=f'new_task'
            ),
            SelectOption(
                label='Мои задачи.',
                description='Редактирование задач, созданные вами.',
                emoji='💪',
                value='my_tasks'
            ),
            SelectOption(
                label='Я выполняю.',
                description='Удаление задач, созданные вами. ',
                emoji='🔨',
                value='im_doing'
            )
        ]

        super().__init__(placeholder='Выберите действие',
                         options=select_options,
                         custom_id='TaskChoiceSelect',
                         row=0,
                         disabled=False)

    async def callback(self, interaction: Interaction):  # TODO: check available list of roles from db to interaction
        if self.values[0] == 'new_task':
            if interaction.user.guild_permissions.administrator is True:
                await interaction.edit(view=TasksChoice())
                embed = Embed(title='Новая задача', description='Описание')
                embed.set_footer(text='Заказ ещё не принят...',
                                 icon_url='https://static.wikia.nocookie.net/'
                                          'minecraft_gamepedia/images/4/45/Allay_JE2.gif')
                embed.add_field(name='Цена:', value='*Не указано...*', inline=False)
                from pyspapi import SPAPI, MojangAPI
                user = sql.get_user(interaction.user.id)
                minercaft_uid = None
                username = None
                avatar_url = None
                if user is None:
                    message = await interaction.send(content='ожидание ответа от spworlds...', ephemeral=True)
                    spapi = SPAPI('6273cba5-add3-44b8-a9a6-d528fcf0f29a', 'hQvWsc9FssggbtNXukG/3XbgNXtyTgos')
                    try:
                        spuser = spapi.get_user(interaction.user.id)
                    except:
                        username = f'[{interaction.client.user.display_name}] - {interaction.user.name}'
                        avatar_url = interaction.client.user.avatar.url
                    else:
                        minercaft_uid = MojangAPI.get_uuid(spuser.username) if spuser is not None else None
                        sql.add_user(interaction.user.id, minercaft_uid)
                        username = MojangAPI.get_username(minercaft_uid)
                        avatar_url = f'https://visage.surgeplay.com/face/512/{minercaft_uid}.png'
                    finally:
                        embed.set_author(name=f'{username}',
                                         icon_url=avatar_url)
                        await message.edit(content=None, embed=embed, view=NewTask())
                else:
                    avatar_url = f"https://visage.surgeplay.com/face/512/{user['minecraft_uid']}.png"
                    embed.set_author(name=f"{interaction.client.get_user(user['discord_uid']).name}",
                                     icon_url=avatar_url)
                    await interaction.send(ephemeral=True, embed=embed, view=NewTask())
            else:
                await interaction.send(content='У вас нету прав :(', ephemeral=True)
        elif self.values[0] == 'my_tasks':
            data: dict = sql.get_tasks_()
            for index, d in enumerate(data):
                if not interaction.client.get_guild(d['guild_id']):
                    del data[index]
            pages = TasksListPages(source=TasksPages(list(data)))
            await pages.start(interaction=interaction, ephemeral=True)
        elif self.values[0] == 'im_doing':
            tasks = sql.get_tasks_by_customer_id(interaction.user.id)
            embed = Embed(title='Удаление задачи', description='Описание')
            await interaction.send(embed=embed, ephemeral=True)


class NewTask(View):

    def __init__(self):
        super().__init__(timeout=None)

    @button(label='Отправить', custom_id='new_task_send', style=ButtonStyle.green, emoji='🟩', row=1)
    async def new_task_send(self, button: Button, interaction: Interaction):
        item = None
        description = None
        price = None
        embed = None
        thread = None
        message = None
        for embed in interaction.message.embeds:
            item = embed.title.split(' 🌐')[0] if embed.title.endswith('🌐') else embed.title
            is_global = '🌐' if embed.title.endswith('🌐') else ''
            description = embed.description
            for field in embed.fields:
                if field.name == 'Цена:':
                    if field.value == '*Не указано...*':
                        await interaction.send(ephemeral=True, content='Цена должна быть в цифрах.')
                    elif int(field.value) < 0:
                        await interaction.send(ephemeral=True, content='Цена должна быть больше чем 0')
                    else:
                        price = field.value
                        self.new_task_send.disabled = True
                        self.new_task_edit.disabled = True
                        self.new_task_global_status.disabled = True
                        self.new_task_back.disabled = True
                        await interaction.edit(view=self)
                        waiting = await interaction.send(ephemeral=True, content='Необходимо подождать...')
                        sql_guilds = sql.get_guilds_where_tasks_enabled()
                        sql_count_tasks = sql.get_tasks_count()
                        print(sql_count_tasks)
                        if is_global != '':
                            # TODO где какой канал?
                            for sql_guild in sql_guilds:
                                print('guild',sql_guild)
                                guild: Guild = interaction.client.get_guild(sql_guild['guild_id'])
                                print('guild is', guild)
                                channel = guild.get_channel(sql_guild['task_channel_id'])
                                thread_ = await channel.create_thread(name=f'{is_global+" "}#{sql_count_tasks["max"]}'
                                                                          f' {item} - {interaction.user.display_name}',
                                                                     embed=embed)
                                forum_tags = [ForumTag(name='Глобальные заказы', id=sql_guild['task_tag_global_id']),
                                              ForumTag(name='Ожидают', id=sql_guild['task_tag_waiting_id'])]
                                await thread_.edit(applied_tags=forum_tags)
                                message_ = None
                                async for message_ in thread_.history(limit=100, oldest_first=True):
                                    if message_.author == interaction.client.user:
                                        await message_.edit(view=TasksAccept())
                                print(thread, message)
                                if thread is None and message is None and message_ is not None and interaction.guild.id == thread_.guild.id:
                                    print(0000000000000)
                                    thread = thread_
                                    message = message_
                        else:
                            print('1')
                            sql_guild = sql.get_guild(interaction.guild.id)
                            channel = interaction.guild.get_channel(sql_guild['task_channel_id'])
                            thread = await channel.create_thread(name=f'{is_global+" "}#{sql_count_tasks["max"]}'
                                                                      f' {item} - {interaction.user.display_name}',
                                                                 embed=embed)
                            forum_tags = [ForumTag(name='Ожидают', id=sql_guild['task_tag_waiting_id'])]
                            await thread.edit(applied_tags=forum_tags)
                            async for message in thread.history(limit=100, oldest_first=True):
                                if message.author == interaction.client.user:
                                    await message.edit(view=TasksAccept())
                        try:
                            print(thread.id)
                            print(message.channel.id)
                            sql.add_task(guild_id=interaction.guild.id,
                                         customer_id=interaction.user.id,
                                         customer_thread_id=thread.id,
                                         item=item,
                                         description=description,
                                         price=price,
                                         customer_thread_message_id=message.id,
                                         global_status=True if is_global == '🌐' else False)
                            await waiting.edit('Ваше задание было опубликовано!')
                        except Exception as e:
                            print('Error', e)
                            await interaction.send('Что-то пошло не так и ваше задание не было опубликовано...\n'
                                                   'Попробуйте ещё раз.', ephemeral=True)
        # TODO: публикация на других серверах

    @button(label='Отредактировать', custom_id='edit_new_task', style=ButtonStyle.gray, emoji='✏️', row=1)
    async def new_task_edit(self, button: Button, interaction: Interaction):
        await interaction.response.send_modal(NewTaskModal(interaction))

    @button(label='Глобальное задание', custom_id='new_task_global_status', style=ButtonStyle.gray, emoji='🌐', row=1)
    async def new_task_global_status(self, button: Button, interaction: Interaction):
        for embed in interaction.message.embeds:
            if embed.title.endswith('🌐'):
                embed.title = embed.title.split(' 🌐', 1)[0]
            else:
                embed.title = f'{embed.title} 🌐'
            await interaction.edit(embed=embed)

    @button(label='Назад', custom_id='new_task_back', style=ButtonStyle.blurple, emoji='⬅️', row=2)
    async def new_task_back(self, button: Button, interaction: Interaction):
        pass


class TasksSortBy(Select):

    def __init__(self):
        select_options = [
            SelectOption(
                label=f'Ожидают.',
                description='Создание новой задачи.',
                emoji='🆕',
                value=f'sort_by_waiting'
            ),
            SelectOption(
                label='В процессе.',
                description='Редактирование задач, созданные вами.',
                emoji='💪',
                value='sort_by_in_progress'
            ),
            SelectOption(
                label='Выполнены.',
                description='Удаление задач, созданные вами. ',
                emoji='🔨',
                value='sort_by_done'
            )
        ]

        super().__init__(placeholder='Сортировать по...',
                         options=select_options,
                         custom_id='TasksSortBy',
                         row=0,
                         disabled=False)

    async def callback(self, interaction: Interaction):
        pass


class TasksListPages(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, page):
        embed = nextcord.Embed(title="Entries")
        for entry in page:
            embed.add_field(name=entry[0], value=entry[1], inline=True)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class TasksPages(menus.ButtonMenuPages, inherit_buttons=False):
    def __init__(self, source, timeout=300):
        super().__init__(source, timeout=timeout, disable_buttons_after=True)
        self.add_item(TasksSortBy())
        self.add_item(menus.MenuPaginationButton(emoji=self.FIRST_PAGE))
        self.add_item(menus.MenuPaginationButton(emoji=self.PREVIOUS_PAGE))
        self.add_item(menus.MenuPaginationButton(emoji=self.NEXT_PAGE))
        self.add_item(menus.MenuPaginationButton(emoji=self.LAST_PAGE))
        # self.add_item(Button(label='Перейти на сервер', emoji='➡️', style=ButtonStyle.url, row=0,
        #                      url=f'{}'))
        self._disable_unavailable_buttons()

    @button(label='Выполнено', custom_id='my_task_done', style=ButtonStyle.green, emoji='🟩', row=2)
    async def my_task_done(self, button: Button, interaction: Interaction):
        pass

    @button(label='Редактировать', custom_id='my_task_edit', style=ButtonStyle.gray, emoji='✏️', row=3)
    async def new_task_edit(self, button: Button, interaction: Interaction):
        pass

    @button(label='Удалить', custom_id='my_task_delete', style=ButtonStyle.gray, emoji='🌐', row=3)
    async def new_task_global_status(self, button: Button, interaction: Interaction):
        pass

    @button(label='Отказаться от исполнителя', custom_id='my_task_cancel_contactor', style=ButtonStyle.blurple, emoji='⬅️', row=4)
    async def new_task_back(self, button: Button, interaction: Interaction):
        pass


class ImDoing(View):

    def __init__(self):
        super().__init__(timeout=None)

    @button(label='Отправить', custom_id='new_task_send', style=ButtonStyle.green, emoji='🟩', row=1)
    async def new_task_send(self, button: Button, interaction: Interaction):
        item = None
        description = None
        price = None
        embed = None
        thread = None
        message = None
        for embed in interaction.message.embeds:
            item = embed.title.split(' 🌐')[0] if embed.title.endswith('🌐') else embed.title
            is_global = '🌐' if embed.title.endswith('🌐') else ''
            description = embed.description
            for field in embed.fields:
                if field.name == 'Цена:':
                    if field.value == '*Не указано...*':
                        await interaction.send(ephemeral=True, content='Цена должна быть в цифрах.')
                    elif int(field.value) < 0:
                        await interaction.send(ephemeral=True, content='Цена должна быть больше чем 0')
                    else:
                        price = field.value
                        self.new_task_send.disabled = True
                        self.new_task_edit.disabled = True
                        self.new_task_global_status.disabled = True
                        self.new_task_back.disabled = True
                        await interaction.edit(view=self)
                        waiting = await interaction.send(ephemeral=True, content='Необходимо подождать...')
                        sql_guilds = sql.get_guilds_where_tasks_enabled()
                        sql_count_tasks = sql.get_tasks_count()
                        print(sql_count_tasks)
                        if is_global != '':
                            # TODO где какой канал?
                            for sql_guild in sql_guilds:
                                print('guild',sql_guild)
                                guild: Guild = interaction.client.get_guild(sql_guild['guild_id'])
                                print('guild is', guild)
                                channel = guild.get_channel(sql_guild['task_channel_id'])
                                thread_ = await channel.create_thread(name=f'{is_global+" "}#{sql_count_tasks["max"]}'
                                                                          f' {item} - {interaction.user.display_name}',
                                                                     embed=embed)
                                forum_tags = [ForumTag(name='Глобальные заказы', id=sql_guild['task_tag_global_id']),
                                              ForumTag(name='Ожидают', id=sql_guild['task_tag_waiting_id'])]
                                await thread_.edit(applied_tags=forum_tags)
                                message_ = None
                                async for message_ in thread_.history(limit=100, oldest_first=True):
                                    if message_.author == interaction.client.user:
                                        await message_.edit(view=TasksAccept())
                                print(thread, message)
                                if thread is None and message is None and message_ is not None and interaction.guild.id == thread_.guild.id:
                                    print(0000000000000)
                                    thread = thread_
                                    message = message_
                        else:
                            print('1')
                            sql_guild = sql.get_guild(interaction.guild.id)
                            channel = interaction.guild.get_channel(sql_guild['task_channel_id'])
                            thread = await channel.create_thread(name=f'{is_global+" "}#{sql_count_tasks["max"]}'
                                                                      f' {item} - {interaction.user.display_name}',
                                                                 embed=embed)
                            forum_tags = [ForumTag(name='Ожидают', id=sql_guild['task_tag_waiting_id'])]
                            await thread.edit(applied_tags=forum_tags)
                            async for message in thread.history(limit=100, oldest_first=True):
                                if message.author == interaction.client.user:
                                    await message.edit(view=TasksAccept())
                        try:
                            print(thread.id)
                            print(message.channel.id)
                            sql.add_task(guild_id=interaction.guild.id,
                                         customer_id=interaction.user.id,
                                         customer_thread_id=thread.id,
                                         item=item,
                                         description=description,
                                         price=price,
                                         customer_thread_message_id=message.id,
                                         global_status=True if is_global == '🌐' else False)
                            await waiting.edit('Ваше задание было опубликовано!')
                        except Exception as e:
                            print('Error', e)
                            await interaction.send('Что-то пошло не так и ваше задание не было опубликовано...\n'
                                                   'Попробуйте ещё раз.', ephemeral=True)
        # TODO: публикация на других серверах

    @button(label='Отредактировать', custom_id='edit_new_task', style=ButtonStyle.gray, emoji='✏️', row=1)
    async def new_task_edit(self, button: Button, interaction: Interaction):
        await interaction.response.send_modal(NewTaskModal(interaction))

    @button(label='Глобальное задание', custom_id='new_task_global_status', style=ButtonStyle.gray, emoji='🌐', row=1)
    async def new_task_global_status(self, button: Button, interaction: Interaction):
        for embed in interaction.message.embeds:
            if embed.title.endswith('🌐'):
                embed.title = embed.title.split(' 🌐', 1)[0]
            else:
                embed.title = f'{embed.title} 🌐'
            await interaction.edit(embed=embed)

    @button(label='Назад', custom_id='new_task_back', style=ButtonStyle.blurple, emoji='⬅️', row=2)
    async def new_task_back(self, button: Button, interaction: Interaction):
        pass


class NewTaskModal(Modal):
    def __init__(self, interaction: Interaction):
        title = f'Редактирование нового задания.'
        self.interaction = interaction
        super().__init__(title=title, timeout=None)
        # self.add_item(TextInput(
        #
        # ))
        self.item = TextInput(label='Название:',
                          style=TextInputStyle.short,
                          required=True,
                          max_length=256)
        self.add_item(self.item)
        self.desc = TextInput(label='Описание:',
                         placeholder='Где оставить?',
                         style=TextInputStyle.paragraph,
                         required=True,
                         max_length=1024)
        self.add_item(self.desc)
        self.price = TextInput(label='Цена:',
                          style=TextInputStyle.short,
                          required=True,
                          max_length=4)
        self.add_item(self.price)

    async def callback(self, interaction: Interaction):
        try:
            price = int(self.price.value)
        except:
            await interaction.send(ephemeral=True, content='Цена должна быть в цифрах!')
        else:
            old_embed = None
            embed = Embed(description=self.desc.value)
            for old_embed in self.interaction.message.embeds:
                old_embed = old_embed
            if old_embed.title.endswith('🌐'):
                embed.title = f'{self.item.value} 🌐'
            else:
                embed.title = self.item.value
            embed.set_author(name=old_embed.author.name,
                             icon_url=old_embed.author.icon_url)
            embed.set_footer(text=old_embed.footer.text,
                             icon_url=old_embed.footer.icon_url)
            embed.add_field(name='Цена:',
                            value=price, inline=False)
            await self.interaction.edit_original_message(embed=embed)


class NewTaskChoice(Select):

    def __init__(self):

        select_options = []
        super().__init__(placeholder='Выберите действие',
                         options=select_options,
                         custom_id='TaskConfigChoice',
                         row=0)


class TaskConfigChoice(Select):
    def __init__(self):
        sql_tasks = sql.get_tasks

        select_options = []
        global_tasks = True # TODO
        select_options.append(
            SelectOption(
                label=f'Глобальные задания.',
                description='Включение глобальных заданий.' if global_tasks is True else 'Выключение глобальных заданий',
                emoji='🌐', # switch
                value=f'global_tasks'
            )),
        select_options.append(
            SelectOption(
                label='Роли и создание заданий.',
                description='Пользователи с ролью, которые могут управлять заданиями.',
                emoji='✏️',
                value='role_add_tasks'
            ))
        super().__init__(placeholder='Выберите действие',
                         options=select_options,
                         custom_id='TaskConfigChoice',
                         row=0)

    async def callback(self, interaction: Interaction):
        if self.values[0] == 'global_tasks': # TODO
            pass
        elif self.values[0] == 'role_add_tasks':
            await interaction.edit(view=RoleAddTasks(interaction.guild)) # TOOD: роли которые могут редактировать, добавить в БД


class RoleAddTasks(View):
    def __init__(self, guild: Guild = None):
        super().__init__(timeout=None)
        if guild is not None:
            self.add_item(RoleAddTasksSelect(guild))

        @button(label='Назад',  emoji='⬅️', style=ButtonStyle.gray, custom_id='role_add_tasks_backward')
        async def role_add_tasks_backward(self, button: Button, interaction: Interaction):
            await interaction.edit(view=TasksConfig())


class RoleAddTasksSelect(Select):

    def __init__(self, guild: Guild):
        self.guild = guild
        select_options = []
        roles = guild.roles
        count = 0
        for role in roles:
            if not role.is_bot_managed():
                if count == 25:
                    select_options.append(
                        SelectOption(
                            label=f'{role.name}',
                            description=f'{len(role.members)} пользователей. ',
                            value=f'{role.id}'
                        )
                    )
                    count += 1

        super().__init__(placeholder='Роли с доступом к созданию заказов',
                         min_values=1,
                         max_values=25,
                         options=select_options,
                         custom_id='roles_add_task_select',
                         row=0)

    async def callback(self, interaction: Interaction):
        for value in self.values:
            pass
            # TODO: sql add roles_access_list
