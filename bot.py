import os
import asyncio
import discord
from discord import app_commands

TOKEN = os.environ["DISCORD_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])            # deine Discord-User-ID
ALLOWED_GUILD_ID = int(os.environ["GUILD_ID"])    # nur dieser Server ist erlaubt

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
guild_obj = discord.Object(id=ALLOWED_GUILD_ID)


class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.confirmed = False

    @discord.ui.button(label="Ja, alle Channel löschen", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("Nicht für dich.", ephemeral=True)
        self.confirmed = True
        await interaction.response.edit_message(content="Starte Löschung…", view=None)
        self.stop()

    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("Nicht für dich.", ephemeral=True)
        await interaction.response.edit_message(content="Abgebrochen.", view=None)
        self.stop()


@tree.command(name="reset_channels", description="Löscht ALLE Channel und Kategorien dieses Servers", guild=guild_obj)
async def reset_channels(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("Keine Berechtigung.", ephemeral=True)
    if interaction.guild_id != ALLOWED_GUILD_ID:
        return await interaction.response.send_message("Server nicht erlaubt.", ephemeral=True)

    view = ConfirmView()
    await interaction.response.send_message(
        "⚠️ Wirklich **alle** Channel und Kategorien löschen? Das kann nicht rückgängig gemacht werden.",
        view=view, ephemeral=True,
    )
    await view.wait()
    if not view.confirmed:
        return

    guild = interaction.guild
    # Neuen Channel zuerst anlegen, damit der Server nicht leer ist
    new_channel = await guild.create_text_channel("neu-gestartet")

    deleted, failed = 0, 0
    for channel in list(guild.channels):
        if channel.id == new_channel.id:
            continue
        try:
            await channel.delete(reason=f"Reset durch {interaction.user}")
            deleted += 1
            await asyncio.sleep(1)  # Rate-Limit schonen
        except discord.HTTPException:
            failed += 1  # z.B. Community-Pflichtchannel (Regeln / Updates)

    await new_channel.send(f"✅ Fertig. Gelöscht: {deleted}, fehlgeschlagen: {failed}.")


@client.event
async def on_ready():
    await tree.sync(guild=guild_obj)
    print(f"Eingeloggt als {client.user}")


client.run(TOKEN)
