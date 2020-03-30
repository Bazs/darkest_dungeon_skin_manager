from pathlib import Path
import unittest
import tempfile
from typing import List

from gui import MainWindowModel
from master_manifest import load_master_manifest, MasterManfiest


class TestModel(unittest.TestCase):
    MANAGED_MODS_SUBFOLDER_NAME = "managed_mods"
    MOD_CONTENTS_SUBFOLDER_NAME = "_mod_contents"
    BACKUP_FOLDER_NAME = "original_data_backup"

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temporary_directory_path = Path(self.temporary_directory.name)

        self.mod_manager_folder = self.temporary_directory_path / "manager"
        self.mod_manager_folder.mkdir()
        self.game_folder = self.temporary_directory_path / "game"
        self.game_folder.mkdir()
        self.input_mod_content_folder = self.temporary_directory_path / "mod_content"
        self.input_mod_content_folder.mkdir()

        configuration = {"moddable_folders": ["heroes"]}

        self.model = MainWindowModel(configuration, mod_manager_folder=str(self.mod_manager_folder),
                                     game_folder=str(self.game_folder))

    @staticmethod
    def _create_empty_file(target_folder: Path, filename: str) -> Path:
        target_folder.mkdir(parents=True, exist_ok=True)
        target_file = target_folder / filename
        with open(str(target_file), "wb"):
            pass
        return target_file

    @staticmethod
    def _create_non_empty_file(target_folder: Path, filename: str) -> Path:
        target_folder.mkdir(parents=True, exist_ok=True)
        target_file = target_folder / filename
        with open(str(target_file), "wt") as open_file:
            open_file.write("a")
        return target_file

    def _create_hero_skin_mod_content(self) -> Path:
        heroes_folder = self.input_mod_content_folder / "SkinMod9000" / "some_dir" / "heroes"
        hero_file = self._create_empty_file(heroes_folder, "icon.png")
        hero_file_relative_to_heroes_folder = hero_file.relative_to(heroes_folder)
        return hero_file_relative_to_heroes_folder

    def _create_hero_skin_type_mod_content(self) -> (List[Path], str):
        hero_type = "arbalest"
        hero_type_folder = self.input_mod_content_folder / "SkinMod42" / "some_dir" / "some_other_dir" / \
                           (hero_type + "_X")
        hero_files = [self._create_empty_file(hero_type_folder, "icon.png"),
                      self._create_empty_file(hero_type_folder.parent, "fx.png")]
        hero_files_relative_to_heroes_folder = [filepath.relative_to(hero_type_folder.parent) for filepath in
                                                hero_files]
        return hero_files_relative_to_heroes_folder, hero_type

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_add_hero_mod(self):
        hero_file = self._create_hero_skin_mod_content()
        expected_mod_name = "SuperMod"

        mod_content_folder = self.model.find_or_create_mod_content_folder(str(self.input_mod_content_folder))
        self.model.add_mod(expected_mod_name, mod_content_folder)
        expected_hero_file = self.mod_manager_folder / self.MANAGED_MODS_SUBFOLDER_NAME / expected_mod_name / \
                             self.MOD_CONTENTS_SUBFOLDER_NAME / "heroes" / hero_file

        self.assertTrue(expected_hero_file.is_file())

    def test_add_hero_type_mod(self):
        hero_files, hero_type = self._create_hero_skin_type_mod_content()
        expected_mod_name = "WickedSick"

        mod_content_folder = self.model.find_or_create_mod_content_folder(str(self.input_mod_content_folder))
        self.model.add_mod(expected_mod_name, mod_content_folder)

        expected_hero_files = [
            self.mod_manager_folder / self.MANAGED_MODS_SUBFOLDER_NAME / expected_mod_name /
            self.MOD_CONTENTS_SUBFOLDER_NAME / "heroes" / hero_type / hero_file
            for hero_file in hero_files]
        for expected_hero_file in expected_hero_files:
            self.assertTrue(expected_hero_file.is_file())

    def test_activate_deactivate_mod_with_deployment(self):
        hero_file = self._create_hero_skin_mod_content()

        # create file with different content in the game folder which needs to be backed up
        self._create_non_empty_file(self.game_folder / "heroes" / hero_file.parent, hero_file.name)

        mod_name = "AA"
        mod_content_folder = self.model.find_or_create_mod_content_folder(str(self.input_mod_content_folder))
        self.model.add_mod(mod_name, mod_content_folder)
        self.model.activate_mod(mod_name)

        master_manifest = load_master_manifest(self.mod_manager_folder)
        self.assertTrue(mod_name in master_manifest.active_mods)
        self.assertTrue(mod_name in self.model.get_active_mod_names())

        self.model.deploy_mods()
        deployed_file = self.game_folder / "heroes" / hero_file
        backup_file = self.mod_manager_folder / self.BACKUP_FOLDER_NAME / "heroes" / hero_file

        master_manifest = load_master_manifest(self.mod_manager_folder)
        self.assertTrue(mod_name in master_manifest.deployed_mods)
        self.assertTrue(mod_name in self.model.get_deployed_mod_names())
        self.assertTrue(deployed_file.is_file())
        self.assertEqual(0, deployed_file.stat().st_size)
        self.assertTrue(backup_file.is_file())
        self.assertNotEqual(0, backup_file.stat().st_size)

        self.model.deactivate_mod(mod_name)
        master_manifest = load_master_manifest(self.mod_manager_folder)
        self.assertFalse(mod_name in master_manifest.active_mods)
        self.assertFalse(mod_name in self.model.get_active_mod_names())

        self.model.deploy_mods()

        master_manifest = load_master_manifest(self.mod_manager_folder)
        self.assertFalse(mod_name in master_manifest.deployed_mods)
        self.assertFalse(mod_name in self.model.get_deployed_mod_names())
        self.assertNotEqual(0, deployed_file.stat().st_size)
        self.assertFalse(backup_file.is_file())


if __name__ == "__main__":
    unittest.main()
