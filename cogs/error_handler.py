from nextcord.ext import commands
from nextcord import Interaction


class ErrorHandler(commands.Cog):
    """A cog for global error handling."""

    def __init__(self, bot):
        self.bot = bot

    async def on_application_command_error(interaction: Interaction, error):
        """A global error handler cog."""
        if (isinstance(error, commands.MissingRequiredArgument)
            or isinstance(error, commands.BadArgument)
            or isinstance(error, commands.BadUnionArgument)
            or isinstance(error, commands.MissingPermissions)
            or isinstance(error, commands.BotMissingPermissions)
            or isinstance(error, commands.MaxConcurrencyReached)
                or isinstance(error, commands.NoPrivateMessage)):
            await interaction.send(f"**A fatal error occured.**\n{error}", ephemeral=True)
        else:
            await interaction.send(f"**A fatal error occured.**\n{error}", ephemeral=True)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
