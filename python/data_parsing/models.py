"""
Domain dataclasses for Warcry data processing.

All domain types with from_dict()/to_dict() methods for JSON round-tripping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations_with_replacement
from typing import Dict, Iterator, List, Tuple


@dataclass
class Weapon:
    attacks: int
    dmg_crit: int
    dmg_hit: int
    max_range: int
    min_range: int
    runemark: str
    strength: int

    @classmethod
    def from_dict(cls, d: dict) -> Weapon:
        return cls(
            attacks=d['attacks'],
            dmg_crit=d['dmg_crit'],
            dmg_hit=d['dmg_hit'],
            max_range=d['max_range'],
            min_range=d['min_range'],
            runemark=d['runemark'],
            strength=d['strength'],
        )

    def to_dict(self) -> dict:
        return {
            'attacks': self.attacks,
            'dmg_crit': self.dmg_crit,
            'dmg_hit': self.dmg_hit,
            'max_range': self.max_range,
            'min_range': self.min_range,
            'runemark': self.runemark,
            'strength': self.strength,
        }

    def __repr__(self) -> str:
        return f'{self.runemark.capitalize()}  -  {self.attacks}/{self.strength}/{self.dmg_hit}/{self.dmg_crit}'

    def damage_rolls(self) -> List[Tuple[int, ...]]:
        return [x for x in combinations_with_replacement(range(1, 7), self.attacks)]

    def avg_dmgs(self) -> Iterator[float]:
        dmg_rolls = self.damage_rolls()
        for to_hit in [3, 4, 5]:
            total_rolls = 0
            damages = list()
            for pr in dmg_rolls:
                total_rolls = total_rolls + 1
                damage = 0
                for dice in pr:
                    if dice in range(to_hit, 6):
                        damage = damage + self.dmg_hit
                    if dice >= 6:
                        damage = damage + self.dmg_crit
                damages.append(damage)
            avg = sum(damages) / len(damages)
            yield avg

    def chance_to_kill(
            self,
            target_toughness: int,
            target_wounds: int,
            to_crit: int = 6,
            attack_actions: int = 1
    ) -> float:
        to_hit = 4 if self.strength == target_toughness else 3 if self.strength > target_toughness else 5
        total_rolls = 0
        rolls_over_target_dmg = 0

        for pr in combinations_with_replacement(range(1, 7), self.attacks * attack_actions):
            total_rolls += 1
            wounds_caused = 0
            for dice in pr:
                if dice in range(to_hit, to_crit):
                    wounds_caused += self.dmg_hit
                if dice >= to_crit:
                    wounds_caused += self.dmg_crit
            if wounds_caused >= target_wounds:
                rolls_over_target_dmg += 1
        dmg_chance = round(rolls_over_target_dmg / total_rolls, 3)
        return dmg_chance


@dataclass
class Ability:
    _id: str
    name: str
    warband: str
    cost: str
    description: str
    runemarks: List[str]

    @classmethod
    def from_dict(cls, d: dict) -> Ability:
        return cls(
            _id=d['_id'],
            name=d['name'],
            warband=d['warband'],
            cost=d['cost'],
            description=d['description'],
            runemarks=d['runemarks'],
        )

    def to_dict(self) -> dict:
        return {
            '_id': self._id,
            'name': self.name,
            'warband': self.warband,
            'cost': self.cost,
            'description': self.description,
            'runemarks': self.runemarks,
        }

    def tts_format(self) -> Dict[str, str]:
        return {'_id': self._id}

    def __repr__(self) -> str:
        return self.name


@dataclass(frozen=True)
class SubFaction:
    runemark: str
    bladeborn: bool = False
    heroes_all: bool = False
    singleton: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> SubFaction:
        return cls(
            runemark=d['runemark'],
            bladeborn=d['bladeborn'],
            heroes_all=d['heroes_all'],
            singleton=d.get('singleton', False),
        )

    def to_dict(self) -> dict:
        return {
            'runemark': self.runemark,
            'bladeborn': self.bladeborn,
            'heroes_all': self.heroes_all,
            'singleton': self.singleton,
        }

    def __repr__(self) -> str:
        return self.runemark


@dataclass
class Faction:
    grand_alliance: str
    warband: str
    bladeborn: bool = False
    heroes_all: bool = False
    singleton: bool = False
    subfactions: set[SubFaction] = field(default_factory=set)

    @classmethod
    def from_dict(cls, d: dict) -> Faction:
        faction = cls(
            grand_alliance=d['grand_alliance'],
            warband=d['warband'],
            bladeborn=d['bladeborn'],
            heroes_all=d['heroes_all'],
            singleton=d.get('singleton', False),
        )
        for s in d.get('subfactions', []):
            faction.subfactions.add(SubFaction.from_dict(s))
        return faction

    def to_dict(self) -> dict:
        return {
            'grand_alliance': self.grand_alliance,
            'warband': self.warband,
            'bladeborn': self.bladeborn,
            'heroes_all': self.heroes_all,
            'singleton': self.singleton,
            'subfactions': [s.to_dict() for s in self.subfactions],
        }

    def get_bladeborn(self) -> set[str]:
        return {b.runemark for b in self.subfactions if b.bladeborn}

    def __repr__(self) -> str:
        return self.warband


@dataclass
class Fighter:
    _id: str
    name: str
    warband: str
    _subfaction_str: str
    grand_alliance: str
    movement: int
    toughness: int
    wounds: int
    weapons: List[Weapon]
    runemarks: List[str]
    points: int
    # Enrichment fields (not serialized by to_dict)
    abilities: List[Ability] = field(default_factory=list, repr=False)
    faction: Faction | None = field(default=None, repr=False)
    subfaction: SubFaction | None = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, d: dict) -> Fighter:
        return cls(
            _id=d['_id'],
            name=d['name'],
            warband=d['warband'],
            _subfaction_str=d.get('subfaction', ''),
            grand_alliance=d['grand_alliance'],
            movement=d['movement'],
            toughness=d['toughness'],
            wounds=d['wounds'],
            weapons=[Weapon.from_dict(w) for w in d['weapons']],
            runemarks=d['runemarks'],
            points=d['points'],
        )

    def to_dict(self) -> dict:
        """Serialize to dict matching source JSON format. Excludes enrichment fields."""
        return {
            '_id': self._id,
            'name': self.name,
            'warband': self.warband,
            'subfaction': self._subfaction_str,
            'grand_alliance': self.grand_alliance,
            'movement': self.movement,
            'toughness': self.toughness,
            'wounds': self.wounds,
            'weapons': [w.to_dict() for w in self.weapons],
            'runemarks': self.runemarks,
            'points': self.points,
        }

    def subfaction_runemark(self) -> str | None:
        if self.subfaction:
            return self.subfaction.runemark
        return None

    def is_ally(self, src_fighter: Fighter | None = None) -> bool:
        can_ally = any(['hero' in self.runemarks, 'ally' in self.runemarks])
        if src_fighter:
            return all([can_ally, src_fighter.grand_alliance == self.grand_alliance])
        return can_ally

    def is_bladeborn(self) -> bool:
        if self.faction and self.faction.bladeborn:
            return True
        if self.subfaction and self.subfaction.bladeborn:
            return True
        return False

    def dmg_chance(
            self,
            vs_t: int,
            dmg: int,
            weapon_index: int = 0,
            to_crit: int = 6,
            attack_actions: int = 1
    ) -> List[Tuple[Tuple[int, str], float]]:
        to_check = self.weapons[weapon_index] if weapon_index else self.weapons
        to_ret = list()

        for wep in to_check:
            chance = wep.chance_to_kill(target_toughness=vs_t, target_wounds=dmg, to_crit=to_crit, attack_actions=attack_actions)
            to_ret.append(((weapon_index, wep.runemark), chance))
            if weapon_index == 0:
                weapon_index += 1

        return to_ret

    def has_str(self, s: int) -> bool:
        for wep in self.weapons:
            if wep.strength >= s:
                return True
        return False

    def __repr__(self) -> str:
        return self.name


@dataclass
class WarbandData:
    """Container for typed warband data flowing through the pipeline."""
    fighters: List[Fighter] = field(default_factory=list)
    abilities: List[Ability] = field(default_factory=list)
    factions: List[Faction] = field(default_factory=list)
