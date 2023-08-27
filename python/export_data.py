from data_parsing import FighterJSONPayload, AbilityJSONPayload

if __name__ == '__main__':

    fighter_data_payload = FighterJSONPayload()

    ability_data_payload = AbilityJSONPayload()

    fighter_data_payload.write_to_disk()
    ability_data_payload.write_to_disk()
