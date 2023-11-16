from pathlib import Path
from .models import JSONDataPayload
from .fighters import Fighter
import json
import jsonschema


class WarbandDataPayload(JSONDataPayload):
    def __init__(
            self,
            warband_file: Path,
            warband_schema: Path = Path(Path(__file__).parent.parent.parent, 'data', 'schemas', 'warband_schema.json')
    ):
        super().__init__(src_file=warband_file, schema=warband_schema)
        self._id = self.data['_id']
        self.name = self.data['name']
        self.grand_alliance = self.data['grand_alliance']
        self.warband_runemark = self.data['warband_runemark']
        self.fighters = self.get_fighters()

    def get_fighters(self):
        return [Fighter(x) for x in self.data['fighters']]

    def validate_data(self):
        errors = list()
        for fighter in self.data['fighters']:
            if fighter['warband'] != self.data['warband_runemark']:
                errors.append(f'{fighter["name"]}: warband ({fighter["warband"]}) does not match warband name ({self.data["name"]})')
            if fighter['grand_alliance'] != self.data['grand_alliance']:
                errors.append(f'{fighter["name"]}: grand_alliance ({fighter["warband"]}) does not match warband grand_alliance ({self.data["grand_alliance"]})')
        if any(errors):
            for e in errors:
                print(f'ERROR: {e}')
            raise RuntimeError('warband data errors')
        with open(self.schema, 'r') as f:
            schema_data = json.load(f)
        jsonschema.validate(self.data, schema_data)
