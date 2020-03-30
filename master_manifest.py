import json
import os
from pathlib import Path
from typing import List, NamedTuple

MasterManfiest = NamedTuple("MasterManfiest", [("active_mods", List[str]), ("deployed_mods", List[str])])

MASTER_MANIFEST_FILENAME = "master_manifest.json"


def load_master_manifest(folder: Path) -> MasterManfiest:
    master_manifest_path = folder / MASTER_MANIFEST_FILENAME
    if not master_manifest_path.is_file():
        master_manifest = MasterManfiest(active_mods=[], deployed_mods=[])
        persist_master_manifest(folder, master_manifest)
    else:
        try:
            with open(str(master_manifest_path), "r") as manifest_in_file:
                manifest_dict = json.load(manifest_in_file)
                master_manifest = MasterManfiest(**manifest_dict)
        except TypeError as e:
            print("Error, corrupt master manifest. Removing and creating a new one.")
            os.remove(str(master_manifest_path))
            master_manifest = MasterManfiest(active_mods=[], deployed_mods=[])
            persist_master_manifest(folder, master_manifest)

    return master_manifest


def persist_master_manifest(folder: Path, master_manifest: MasterManfiest):
    master_manifest_path = folder / MASTER_MANIFEST_FILENAME
    with open(str(master_manifest_path), "w") as manifest_out_file:
        json.dump(master_manifest._asdict(), manifest_out_file)
