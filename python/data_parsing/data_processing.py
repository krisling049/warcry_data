import logging
from collections import defaultdict

from .abilities import Ability
from .constants import UNIVERSAL
from .fighters import Fighter

logger = logging.getLogger(__name__)


def assign_subfactions(fighters: list[Fighter], factions: list[dict]) -> None:
    subfactions_by_warband = {f['warband']: [s['runemark'] for s in f['subfactions']] for f in factions}
    for fighter in fighters:
        candidates = {*fighter.runemarks, fighter.declared_subfaction}
        for runemark in subfactions_by_warband.get(fighter.warband, []):
            if runemark in candidates:
                fighter.subfaction = runemark
                break


def assign_abilities(fighters: list[Fighter], abilities: list[Ability]) -> None:
    """Give each fighter every ability of its warband, subfaction or universal whose runemarks it has."""
    fighters_by_group: dict[str, list[Fighter]] = defaultdict(list)
    for fighter in fighters:
        fighters_by_group[fighter.warband].append(fighter)
        if fighter.subfaction:
            fighters_by_group[fighter.subfaction].append(fighter)

    assignments = 0
    for ability in abilities:
        targets = fighters if ability.warband == UNIVERSAL else fighters_by_group.get(ability.warband, [])
        for fighter in targets:
            if set(ability.runemarks).issubset(fighter.runemarks):
                fighter.abilities.append(ability)
                assignments += 1
    logger.info(f'Assigned {assignments} abilities to fighters')
