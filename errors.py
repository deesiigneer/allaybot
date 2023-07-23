__all__ = (
    "AllayBotException",
    "PermsError",
    "DBCompareError"
)

import nextcord

embed = nextcord.Embed

class AllayBotException(Exception):
    pass


class PermsError(AllayBotException):
    def __init__(self, interaction: nextcord.Interaction, perms: nextcord.Permissions) -> None:
        embed.color = 0x12312
        embed.title = 'Ошибка прав доступа!'
        embed.description += 'Необходимы следующие права:\n\n'
        if not perms.send_messages:
            embed.description += '* Отправка сообщений\n'
        if not perms.manage_channels:
            embed.description += '* Управление каналами\n'
        if not perms.view_channel:
            embed.description += '* Просмотр каналов\n'
        if not perms.manage_threads:
            embed.description += '* Управление ветками\n'
        if not perms.create_public_threads:
            embed.description += '* Создание публичных веток\n'
        if not perms.create_private_threads:
            embed.description += '* Создание приватных веток\n'


class DBCompareError(AllayBotException):
    pass
