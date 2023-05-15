# warcry_data
A consolidated home for data used by Warcry tools

In this repo you will find json files covering all fighters in Warcry.
data/fighters.json is considered the source of truth for fighter profiles.  
Individual warband json files, arranged by Grand Alliance, are generated from fighters.json and shouldn't be manually edited.  

The repo also contains tools for loading, manipulating and saving the data in data/.  
Currently, this only exists for pythonm but other languages may be added into their own directories.

###   Access
To retrieve data programmatically you can GET https://raw.githubusercontent.com/krisling049/warcry_data/main/data/fighters.json

###  Acknowledgements
Huge thanks to the following for their valuable contributions:
- Baz ([Optimal Game State](https://www.youtube.com/@optimalgamestate), [Warcry Card Creator](https://barrysheppard.github.io/warcry-card-creator/), [github](https://github.com/barrysheppard))
- Servo-Scribe ([Warcrier](https://warcrier.net/), [Necrodamus](https://necrodamus.org/), [Mordheimer](https://mordheimer.net/))
- Hood ([Warcry Tabletop Simulator](https://steamcommunity.com/sharedfiles/filedetails/?id=2923487353))
