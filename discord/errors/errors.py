from discord.ext import commands


async def add_new_channel_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("У вас недостаточно прав для выполнения этой команды.")
    else:
        print(error)


async def remove_new_channel_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("У вас недостаточно прав для выполнения этой команды.")
    else:
        print(error)
