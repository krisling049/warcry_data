class Ability:
    def __init__(self, ability_dict: dict):
        self._id: str = ability_dict['_id']
        self.name: str = ability_dict['name']
        self.warband: str = ability_dict['warband']
        self.cost: str = ability_dict['cost']
        self.runemarks: list[str] = ability_dict['runemarks']

    def __repr__(self) -> str:
        return self.name

    def tts_format(self) -> dict[str, str]:
        return {'_id': self._id}
