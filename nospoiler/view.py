"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging

import discord

log = logging.getLogger("red.maxcogs.nospoiler.view")


class BanViewModal(discord.ui.Modal, title="Enter Ban Reason"):
    def __init__(self):
        super().__init__()
        self.reason = discord.ui.TextInput(
            label="Add Ban Reason",
            placeholder="Example: n word bait",
            min_length=3,
            max_length=4000,
            required=True,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        self.reason_value = self.reason.value  # Store the reason value


class BanView(discord.ui.View):
    def __init__(self, guild, author, target_user):
        super().__init__(timeout=900)
        self.guild = guild
        self.author = author
        self.target_user = target_user

    async def on_timeout(self) -> None:
        for item in self.children:
            item: discord.ui.Item
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.NotFound as e:
            log.error(e)

    @discord.ui.button(label="Ban User", style=discord.ButtonStyle.red, emoji="🔨")
    async def on_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the user has ban_members permission
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "You do not have permission `ban_members` to ban a user.", ephemeral=True
            )
            return

        # Check if the target user is a mod, admin, or owner; they cannot be banned if they have these permissions
        if (
            self.target_user.guild_permissions.administrator
            or self.target_user.guild_permissions.manage_roles
            or self.target_user.guild_permissions.manage_guild
            or self.target_user.guild_permissions.ban_members
        ):
            await interaction.response.send_message(
                "You cannot ban moderators, administrators, or the owner of the server.",
                ephemeral=True,
            )
            return

        modal = BanViewModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        # Check if the modal was submitted
        reason = modal.reason_value
        try:
            await self.guild.ban(self.target_user, reason=reason)
            button.disabled = True
            await interaction.followup.send(
                f"{self.target_user} has been banned for: {reason}", ephemeral=True
            )
            # Update the view to disable the button
            await interaction.message.edit(view=self)
        except discord.Forbidden:
            await interaction.followup.send(
                "I do not have permission to ban this user.", ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.followup.send(f"Failed to ban user: {e}", ephemeral=True)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        await interaction.followup.send(f"An error occured: {error}", ephemeral=True)
        log.error(f"An error occured: {error}")
