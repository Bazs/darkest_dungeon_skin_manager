import json
from pathlib import Path
from typing import List, NamedTuple

MasterManfiest = NamedTuple("MasterManfiest", [("active_mods", List)])

MASTER_MANIFEST_FILENAME = "master_manifest.json"


def load_master_manifest(folder: Path) -> MasterManfiest:
    master_manifest_path = folder / MASTER_MANIFEST_FILENAME
    if not master_manifest_path.is_file():
        master_manifest = MasterManfiest(active_mods=[])
        persist_master_manifest(folder, master_manifest)
    else:
        with open(str(master_manifest_path), "r") as manifest_in_file:
            manifest_dict = json.load(manifest_in_file)
            master_manifest = MasterManfiest(**manifest_dict)
    return master_manifest


def persist_master_manifest(folder: Path, master_manifest: MasterManfiest):
    master_manifest_path = folder / MASTER_MANIFEST_FILENAME
    with open(str(master_manifest_path), "w") as manifest_out_file:
        json.dump(master_manifest._asdict(), manifest_out_file)
