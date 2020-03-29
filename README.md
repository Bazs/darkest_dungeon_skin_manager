## Darkest Dungeon Skin Manager

Can import skins and town portraits/other illustrations from .zip archives or folders. Will try to determine if it's a 
hero skin or other illustration on import, and will store the files in a homogenized form insdie its own repository folder.

Can activate/deactivate individual skin mods - when deactivating, it will remove any additional files, and restore the original artwork, if any was overwritten.

### Import compatibility
The tool with be able to import a folder/archive if in it:
* a folder called `<heroname>_<letter>` is found at any level, e.g. `arbalest_N` -> tool will understand that this is a hero skin, will deploy relevant files under "heroes/arbalest/..."
* folders called "heroes" or "campaign" are present at any level -> these will be deployed as-is under the game folder

### How to run
*Python 3.8 is required.* To install dependencies, use `pip install -r requirements.txt`, or use your more sophisticated package manager of choice.

To start the tool, run the `main.py` script, run it with -h for command line arguments.
