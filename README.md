
# Information

This is a tool designed for Minecraft Speedrunning in the All Portals category.
Ideally each player should download this tool and it allows for easier stronghold tracking and navigation.

## Configuration Page
![](images/tracker_config.png?raw=true)

### Main Textbox
In the main textbox the parseable text that you will use to set locations will be pasted.

Each line indicates a separate item and non-readble lines will simply be skipped.
In each line, the first index indicates the id, the second index is the X coordinate and the third index is the Z coordinate.


### Launch Button
Click the button to launch CrayonAPTracker. 
Note: Settings on the configuration page may also be set and clicking the launch button will set binds and new coordinate data.

### Rebind Controls
This section allows the user to rebind keys to go to previous and next coordinates.
Just enter the key within the entry box you'd like to use.
Note: Other key/s must not be held. It can only be this combination.

## CrayonNavAssist
- The first row is the Stronghold Number.
- The second row contains the Target X and Z labels.
- The third row contains the Overworld X and Z targets.
- The fourth row contains the Nether X and Z targets.

- The bottom frame allows to switch between tracking items and updates the target.

![](images/navassist.png?raw=true)

# Usage
1. Download CrayonAllPortals.exe from releases.
2. Run downloaded executable file.
3. You will be presented with the Configuration Page.

4. In the Configuration Page, you are already provided the best coordinates for measuring each Stronghold Ring. Thus, the first step is to find the location of each ring and note the coordinates down of each starter room.
5. After getting all 8 rings, you should input your data into the [CrayonAllPortals](https://github.com/CommonCrayon/CrayonAllPortals) tool.
6. The tool will provide you parseable text back, like below:   
```text
"0:Steve"
[3,2024,310]
[21,10085,5017]
[37,12618,6806]
[36,14063,2784]
[57,16504,5538]
[85,20213,3297]
[86,19333,6757]
[121,20924,10810]
```
7. This can be entered within the Main Textbox and launched to complete each stronghold 1 by 1 to complete a whole path. Thus allowing for easy tracking of strongholds, their order and achieving the best path for the fastest All Portals Speedrun.

# BUILD

### Install Packages
`
python -m pip install -r requirements.txt
python -m pip install pyinstaller
`


### Build with PowerShell:
`
python -m PyInstaller --onefile --windowed --icon=icon.ico --name CrayonAPNavAssist_v0_4 .\CrayonAPNavAssist.py
python -m PyInstaller --onefile --windowed --icon=icon.ico --name CrayonAPTracker_v1_0 .\CrayonAPTracker.py
`
