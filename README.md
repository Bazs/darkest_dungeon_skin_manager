## Darkest Dungeon Skin Manager [![Build Status](https://travis-ci.org/Bazs/darkest_dungeon_skin_manager.svg?branch=master)](https://travis-ci.org/github/Bazs/darkest_dungeon_skin_manager)

Can import skins and town portraits/other illustrations from .zip archives or folders. Will try to determine if it's a 
hero skin or other illustration on import, and will store the files in a homogenized form insdie its own repository folder.

Can activate/deactivate individual skin mods - when deactivating, it will remove any additional files, and restore the original artwork, if any was overwritten.

### Import compatibility
The tool with be able to import a folder/archive if in it:
* a folder called `<heroname>_<letter>` is found at any level, e.g. `arbalest_N` -> tool will understand that this is a hero skin, will deploy relevant files under "heroes/arbalest/..."
* folders called "heroes" or "campaign" are present at any level -> these will be deployed as-is under the game folder

### How to start the GUI
*Python 3.8 is required.* To install dependencies, use `pip install -r requirements.txt`, or use your more sophisticated package manager of choice.

To start the tool, run the `main.py` script, run it with -h for command line arguments.

### Usage
Add mods from folders or archives with the corresponding buttons. Then they'll appear in the Managed Mods list.
Select a managed mods and click Activate mod to activate it. It'll appear in the Active mods list. This does not deploy
anything to the game folder yet.

Managed mods, which are not currently active have a white background. Active managed mods have a green background.

To deploy the currently selected list of active mods, click Deploy mods. Deploy mods will also remove mods, which were
deployed before, but are no longer in the active mods list, e.g. if all active mods are deactivated, then Deploy mods
will restore the game folder to its original state.

The Deploy mods button will have a bold font, if the currently active list of mods is different from the list of 
deployed mods, i.e. when you have to deploy to apply your changes. Active but not yet deployed mods have a blue
background in the Active mods list.
