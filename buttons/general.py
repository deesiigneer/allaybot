import nextcord
from nextcord.ui import View, Select, Modal, Button, button, TextInput, Item
from nextcord.utils import find
from nextcord import ButtonStyle, Interaction, Embed, Role, Emoji, PermissionOverwrite, Guild, SelectOption, \
    TextChannel, TextInputStyle, ChannelType
from database import sql
from sys import exc_info


class BotPanelButtons(View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ModuleChoice())

    # @button(label='Набор в город', emoji='👋', style=ButtonStyle.blurple, row=1, custom_id='application_to_city')
    # async def application_to_city(self, button: Button, interaction: Interaction):
    #     from handler import update_applications_panel
    #     sql_recruiting = sql.get_recruiting(interaction.guild.id)
    #     embeds = [await update_applications_panel(interaction.client, interaction.guild)]
    #     if sql_recruiting:
    #         await interaction.response.send_message(embeds=embeds,
    #                                                 view=ApplicationToCityButtons(interaction=interaction),
    #                                                 ephemeral=True)
    #         #  TODO
    #     else:
    #         await interaction.send(content=f'Модуль `Набор в город` для `{interaction.guild.name}` ещё не установлены',
    #                                embeds=embeds,
    #                                view=CreateRecruiting(interaction),
    #                                ephemeral=True)
        # await interaction.response.send_modal(application_to_city_modal(guild=interaction.guild))

    @button(label='Обновить', emoji='🔃', style=ButtonStyle.blurple, row=2, custom_id='settings_panel_update')
    async def update(self, button: Button, interaction: Interaction):
        try:
            from handler import update_panel, Check
            channel = interaction.guild.get_channel(interaction.channel.id)
            await Check(interaction.client, interaction.guild).comparison_database_to_guild(interaction, channel,
                                                                                            interaction.message)
            await update_panel(interaction.client, interaction.guild)
            await interaction.message.edit(view=BotPanelButtons())
            # await interaction.edit(embeds=embeds, view=BotPanelButtons())
        except Exception as e:
            raise f"Update Exception {e}"


class ModuleChoice(Select):

    def __init__(self):
        select_options = [
            SelectOption(
                label=f'Заявки в город',
                description=f'Модуль заявок в город',  # TODO
                emoji='👋',
                value=f'applications'),
            SelectOption(
                label=f'Задания',
                description=f'IN DEV',  # TODO
                emoji='📌',
                value=f'tasks'),
            SelectOption(
                label=f'Список жителей',
                description=f'IN DEV',  # TODO
                emoji='😇',
                value=f'citizens')]

        super().__init__(placeholder="Выбери модуль",
                         min_values=1,
                         max_values=1,
                         options=select_options,
                         custom_id='ModuleChoice',
                         row=0)

    async def callback(self, interaction: Interaction):
        from handler import Check
        if self.values[0] == 'applications':
            from handler import update_applications_panel
            sql_recruiting = sql.get_recruiting(interaction.guild.id)
            embeds = [await update_applications_panel(interaction.client, interaction.guild)]
            from buttons.requests_to_city import ApplicationToCityButtons, CreateRecruiting
            if sql_recruiting:
                await interaction.response.send_message(embeds=embeds,
                                                        view=ApplicationToCityButtons(interaction=interaction),
                                                        ephemeral=True)
                #  TODO
            else:
                await interaction.send(content=f'Модуль `Набор в город` для `{interaction.guild.name}` ещё не установлены',
                                       embeds=embeds,
                                       view=CreateRecruiting(interaction),
                                       ephemeral=True)
        elif self.values[0] == 'tasks':
            from buttons.tasks import TasksModule
            await interaction.send(content=f'Модуль `Заданий` для {interaction.guild.name}!',
                                   view=TasksModule(),
                                   ephemeral=True)
        elif self.values[0] == 'citizens':
            await interaction.send(content=f'Модуль `Список жителей` ещё в разработке!',
                                   ephemeral=True)
        await interaction.message.edit(view=BotPanelButtons())
