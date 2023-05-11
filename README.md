# warcry_data
A consolidated home for data used by Warcry tools

In this repo you will find json files covering all fighters in Warcry.
data/fighters.json is considered the source of truth for fighter profiles.  
Individual warband json files, arranged by Grand Alliance, are generated from fighters.json and shouldn't be manually edited.  

The repo also contains tools for loading, manipulating and saving the data in data/.  
Currently, this only exists for pythonm but other languages may be added into their own directories.

## Acknowledgements
Huge thanks to Baz for collating the fighter data and putting it into a nice, friendly json.
