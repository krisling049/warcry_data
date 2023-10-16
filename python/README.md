# warcry_data Python

## General notes
Each of these scripts is intended to be run in python 3.10+, with requirements.txt installed.  
The scripts should run without any additional arguments or editing - though in some places the option  
is available to customise parameters this way.  

DataPayloads, Fighters, Weapons and Abilities all have convenience classes in data_parsing.  
Loading the data as a DataPayload (or one of its subclasses) is the only supported way to write data  
files to disk (to ensure ordering and formatting are correct).

Example: With `warcry_data\python\` as the cwd, run `python assign_abilities.py` to add missing _ids to  
any fighters or abilities.

## Python quick setup guide
- These steps assume that you do not have python installed and have never used it before;
- Download [Python 3.10.11](https://www.python.org/downloads/release/python-31011/) for your OS;
- Say Yes to any options for adding python to PATH and installing PIP;
- Open a terminal (cmd prompt, powershell, bash etc.) in warcry_data/python;
- run `python -m pip install -r ./requirements.txt`;
- run `python validation.py`.

If you are in the `main` branch, the script should run without error and end by outputting 'validation passed.'
You should now be set up to run any other warcry_data python scripts.

If you're planning to contribute to warcry_data/Python, you should look at setting up your environment properly.  
Either [manually](https://realpython.com/effective-python-environment/#python-version-management), or by using a helpful IDE such as [PyCharm Community Edition](https://www.jetbrains.com/pycharm/).
### assign_tts_format_abilities.py
Assigns abilities to each fighter per their runemarks, in a format used by Tabletop Simulator.

### assign_ids.py
Iterates through all fighters and abilities.  
For any which do not have an _id, or have a placeholder _id, it will assign a new _id.

### validation.py
Used in the git CI pipeline to ensure fighters.json and abilities.json are correctly formatted.

### export_data.py
Parses ablities.json and fighters.json, then writes them to disk.  
Also writes supplemental data files such as the individual warband .jsons, or .xlsx worksheets.