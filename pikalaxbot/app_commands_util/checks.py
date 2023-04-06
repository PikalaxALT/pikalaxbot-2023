from discord.app_commands import check, CheckFailure
from discord import Permissions, Interaction
from collections.abc import Callable
from typing import Any, List, TypeVar

T = TypeVar('T')


async def is_bot_owner(interaction: Interaction):
    return await interaction.client.is_owner(interaction.user)


class MissingAnyPermissions(CheckFailure):
    def __init__(self, missing_permissions: List[str], *args: Any) -> None:
        self.missing_permissions: List[str] = missing_permissions

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_permissions]

        if len(missing) > 2:
            fmt = '{}, or {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' or '.join(missing)
        message = f'You are missing at least one of {fmt} permission(s) to run this command.'
        super().__init__(message, *args)


def has_any_permissions(**perms: bool) -> Callable[[T], T]:
    invalid = perms.keys() - Permissions.VALID_FLAGS.keys()
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(interaction: Interaction) -> bool:
        permissions = interaction.permissions

        possess = [perm for perm, value in perms.items() if getattr(permissions, perm) == value]

        if possess:
            return True

        raise MissingAnyPermissions(list(perms))

    return check(predicate)
