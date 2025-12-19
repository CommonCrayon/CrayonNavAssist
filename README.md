
# Usage

1. Download CrayonAllPortals.exe from releases.

2. Run downloaded executable file.

3. You will be presented with the Configuration Page. 

## Configuration Page
![](images/config_page.png?raw=true)

### Main Textbox
In the main textbox the parseable text that you will use to set locations will be pasted.

Each line indicates a separate item and non-readble lines will simply be skipped.
In each line, the first index indicates the id, the second index is the X coordinate and the third index is the Z coordinate.


### Launch Button
Click the button to launch NavAssist. 
Note: Settings on the configuration page may also be set and clicking the launch button will set binds and new textbox data.

### F3+C Status
This showcases information retrieved from F3+C. Such as dimension and coordinates.

### Rebind Controls
This section allows the user to rebind keys to go to previous and next coordinates.
Just enter the key within the entry box you'd like to use.
Note: Other key/s must not be held. It can only be this combination.

## CrayonNavAssist
- The first row is the ID.
- The second row contains the Target X and Z coordinate which dynamically updates in the nether.
- The third row contains the Distance X and Z coordinate which dynamically updates in the nether.
- The fourth row contains the required angle. Which can be lined up with the Yaw angle in the F3 menu.
- The fifth row contains the turn amount. Negative being the amount to turn left and postive being the amount to turn right by in degrees.

![](images/navassist.png?raw=true)


# BUILD

### Install Packages
`
python -m pip install -r requirements.txt
python -m pip install pyinstaller
`


### Build with PowerShell:
`
python -m PyInstaller --onefile --windowed --icon=icon.ico --name CrayonAPNavAssist_v0_4 .\CrayonAPNavAssist.py
`
