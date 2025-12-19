
# Usage

1. Download CrayonAllPortals.exe from releases.

2. Run downloaded executable file.

3. You will be presented with the Configuration Page. 

### Main Textbox
In the main textbox the parseable text that you will use to set locations will be pasted.

Example input:
`
[1,200,100]
[4,500,0]
[5,256,444]
[2,-104,174]
[6,-260,444]
`

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
