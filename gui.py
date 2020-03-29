from distutils.dir_util import copy_tree
import os
from pathlib import Path
import patoolib
import re
import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.simpledialog
import tempfile
from typing import Dict, List
import shutil
from master_manifest import load_master_manifest, persist_master_manifest


def start_gui(configuration: Dict, mod_manager_folder: str, game_folder: str):
    model = MainWindowModel(configuration, mod_manager_folder, game_folder)
    root = tkinter.Tk()
    MainWindow(model=model, master=root)
    root.mainloop()


class MainWindowModel:
    MOD_CONTENT_SUBFOLDER_NAME = "_mod_contents"

    def __init__(self, configuration: Dict, mod_manager_folder: str, game_folder: str):
        self.mod_manager_folder = Path(mod_manager_folder)
        self.managed_mods_folder = self.mod_manager_folder / "managed_mods"
        self.mod_staging_folder = self.mod_manager_folder / "mod_staging"
        self.original_data_backup_folder = self.mod_manager_folder / "original_data_backup"

        self._ensure_directory_exists(self.managed_mods_folder)
        self._ensure_directory_exists(self.mod_staging_folder)
        self._ensure_directory_exists(self.original_data_backup_folder)

        self.game_folder = Path(game_folder)
        self.configuration = configuration
        self.master_manifest = load_master_manifest(self.mod_manager_folder)

    @staticmethod
    def _ensure_directory_exists(directory: Path):
        if not directory.is_dir():
            directory.mkdir()

    def get_managed_mod_names(self):
        return [content.name for content in self.managed_mods_folder.iterdir() if content.is_dir()]

    def get_active_mod_names(self):
        return self.master_manifest.active_mods

    def add_mod(self, mod_name: str, mod_content_folder: Path):
        new_mod_folder = self.managed_mods_folder / mod_name
        if new_mod_folder.is_file() or new_mod_folder.is_dir():
            raise RuntimeError("There is a managed mod called '{}' already".format(mod_name))

        new_mod_content_folder = new_mod_folder / self.MOD_CONTENT_SUBFOLDER_NAME / mod_content_folder.name
        shutil.copytree(str(mod_content_folder), str(new_mod_content_folder), dirs_exist_ok=True)

    def activate_mod(self, mod_name: str):
        assert mod_name not in self.get_active_mod_names(), "Mod already active"
        mod_folder = self.managed_mods_folder / mod_name
        assert mod_folder.is_dir(), "Mod is not managed"

        self.master_manifest.active_mods.append(mod_name)
        self._deploy_mods()
        persist_master_manifest(self.mod_manager_folder, self.master_manifest)

    def deactivate_mod(self, mod_name: str):
        assert mod_name in self.get_active_mod_names(), "Mod not active"
        mod_folder = self.managed_mods_folder / mod_name
        assert mod_folder.is_dir(), "Mod is not managed"

        self.master_manifest.active_mods.remove(mod_name)
        self._deploy_mods()
        persist_master_manifest(self.mod_manager_folder, self.master_manifest)

    def _deploy_mods(self):
        self._restore_untouched_game_folder()

        for active_mod_name in self.get_active_mod_names():
            active_mod_content_folder = self.managed_mods_folder / active_mod_name / self.MOD_CONTENT_SUBFOLDER_NAME
            try:
                shutil.copytree(str(active_mod_content_folder), str(self.mod_staging_folder), dirs_exist_ok=True)
            except Exception as e:
                raise RuntimeError(e)

        files_to_copy = copy_tree(str(self.mod_staging_folder), str(self.game_folder), dry_run=True)
        try:
            self._create_backup(files_to_copy)
            copy_tree(str(self.mod_staging_folder), str(self.game_folder))
        except Exception as e:
            shutil.rmtree(str(self.mod_staging_folder))
            self._ensure_directory_exists(self.mod_staging_folder)
            raise RuntimeError(e)

    def _create_backup(self, files_to_be_deployed: List[str]):
        files_to_backup = [Path(file) for file in files_to_be_deployed if Path(file).is_file()]
        for file_to_backup in files_to_backup:
            relative_path_of_file_to_backup = file_to_backup.relative_to(self.game_folder)
            backup_destination = self.original_data_backup_folder / relative_path_of_file_to_backup
            backup_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(file_to_backup), str(backup_destination))

    def _restore_untouched_game_folder(self):
        all_deployed_contents = [*self.mod_staging_folder.rglob("*")]
        for deployed_content in all_deployed_contents:
            deployed_target_path = self.game_folder / deployed_content.relative_to(self.mod_staging_folder)
            if deployed_target_path.is_file():
                os.remove(str(deployed_target_path))

        all_backup_contents = [*self.original_data_backup_folder.rglob("*")]
        for backup_content in all_backup_contents:
            if backup_content.is_file():
                restore_destination = self.game_folder / backup_content.relative_to(self.original_data_backup_folder)
                shutil.copy(str(backup_content), str(restore_destination))

        shutil.rmtree(str(self.mod_staging_folder))
        shutil.rmtree(str(self.original_data_backup_folder))
        self._ensure_directory_exists(self.mod_staging_folder)
        self._ensure_directory_exists(self.original_data_backup_folder)

    def find_or_create_mod_content_folder(self, mod_archive_contents_folder: str) -> Path:
        mod_archive_contents_folder_path = Path(mod_archive_contents_folder)
        all_contents = [*mod_archive_contents_folder_path.glob("**/*")]
        moddable_folders = self.configuration["moddable_folders"]

        mod_content_folders = [content for content in all_contents if
                               content.is_dir() and content.name in moddable_folders]
        if len(mod_content_folders) == 1:
            return mod_content_folders[0]
        else:
            # Not a top level moddable folder, try if it's a hero skin
            for content in all_contents:
                if content.is_dir():
                    match = re.fullmatch(r"([\w_]+)_[a-zA-Z]", content.name)
                    if match:
                        hero_name = match.group(1)
                        content_folder_path = mod_archive_contents_folder_path / "heroes" / hero_name
                        heroes_contents = [*content.parent.rglob("*")]
                        for heroes_content in heroes_contents:
                            if heroes_content.is_file():
                                mod_content_destination = content_folder_path / heroes_content.relative_to(
                                    content.parent)
                                try:
                                    mod_content_destination.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.copyfile(str(heroes_content), str(mod_content_destination))
                                except Exception as e:
                                    raise RuntimeError(e)
                        mod_content_folder = content_folder_path.parent
                        break
            else:
                raise RuntimeError("Could not find mod content in archive")

        return mod_content_folder


class MainWindow(tkinter.Frame):
    def __init__(self, model: MainWindowModel, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Darkest Dungeon Mod Manager")
        self.model = model

        self.selected_managed_mod = None
        self.selected_activated_mod = None

        self._create_widgets()
        self.pack()

        self._refresh()

    def _refresh(self):
        self.managed_mods_listvar.set(self.model.get_managed_mod_names())
        self.active_mods_listvar.set(self.model.get_active_mod_names())

        activate_mod_button_state = "disabled"
        if self.selected_managed_mod is not None and self.selected_managed_mod not in self.model.get_active_mod_names():
            activate_mod_button_state = "normal"
        self.activate_mod_button.config(state=activate_mod_button_state)

        deactivate_mod_button_state = "disabled"
        if self.selected_activated_mod is not None:
            deactivate_mod_button_state = "normal"
        self.deactivate_mod_button.config(state=deactivate_mod_button_state)

    def _on_managed_mod_selected(self, evt):
        selected_listbox = evt.widget
        self.selected_managed_mod = self._get_selected_value_from_listbox(selected_listbox)
        self._refresh()

    def _on_activated_mod_selected(self, evt):
        selected_listbox = evt.widget
        self.selected_activated_mod = self._get_selected_value_from_listbox(selected_listbox)
        self._refresh()

    @staticmethod
    def _get_selected_value_from_listbox(listbox):
        current_selection = listbox.curselection()
        if current_selection:
            index = int(listbox.curselection()[0])
            return listbox.get(index)
        return None

    def _create_widgets(self):
        self.managed_mods_frame = tkinter.Frame(self)
        self.managed_mods_title = tkinter.Label(self.managed_mods_frame, text="Managed mods")
        self.managed_mods_title.pack(side=tkinter.TOP)
        self.managed_mods_listvar = tkinter.StringVar(self.managed_mods_frame)
        self.managed_mods_listbox = tkinter.Listbox(self.managed_mods_frame, listvariable=self.managed_mods_listvar,
                                                    selectmode=tkinter.SINGLE)
        self.managed_mods_listbox.bind('<<ListboxSelect>>', self._on_managed_mod_selected)
        self.managed_mods_listbox.pack(side=tkinter.LEFT)
        self.managed_mods_scrollbar = tkinter.Scrollbar(self.managed_mods_frame, orient="vertical")
        self.managed_mods_scrollbar.config(command=self.managed_mods_listbox.yview)
        self.managed_mods_scrollbar.pack(side=tkinter.RIGHT, fill="y")
        self.managed_mods_listbox.config(yscrollcommand=self.managed_mods_scrollbar.set)
        self.managed_mods_frame.pack(side=tkinter.LEFT)

        self.active_mods_frame = tkinter.Frame(self)
        self.active_mods_title = tkinter.Label(self.active_mods_frame, text="Active mods")
        self.active_mods_title.pack(side=tkinter.TOP)
        self.active_mods_listvar = tkinter.StringVar(self.active_mods_frame)
        self.active_mods_listbox = tkinter.Listbox(self.active_mods_frame, listvariable=self.active_mods_listvar,
                                                   selectmode=tkinter.SINGLE)
        self.active_mods_listbox.bind('<<ListboxSelect>>', self._on_activated_mod_selected)
        self.active_mods_listbox.pack(side=tkinter.LEFT)
        self.active_mods_scrollbar = tkinter.Scrollbar(self.active_mods_frame, orient="vertical")
        self.active_mods_scrollbar.config(command=self.active_mods_listbox.yview)
        self.active_mods_scrollbar.pack(side=tkinter.RIGHT, fill="y")
        self.active_mods_listbox.config(yscrollcommand=self.active_mods_scrollbar.set)
        self.active_mods_frame.pack(side=tkinter.RIGHT)

        self.buttons_frame = tkinter.Frame(self)
        self.add_mod_from_archive_button = tkinter.Button(self.buttons_frame, text="Add Mod from Archive",
                                                          command=self._add_mod_from_archive)
        self.add_mod_from_archive_button.pack()
        self.add_mod_from_folder_button = tkinter.Button(self.buttons_frame, text="Add Mod from Folder",
                                                         command=self._add_mod_from_folder)
        self.add_mod_from_folder_button.pack()
        self.activate_mod_button = tkinter.Button(self.buttons_frame, text="Activate mod", command=self._activate_mod)
        self.activate_mod_button.pack()
        self.deactivate_mod_button = tkinter.Button(self.buttons_frame, text="Dectivate mod",
                                                    command=self._deactivate_mod)
        self.deactivate_mod_button.pack()
        self.quit_button = tkinter.Button(self.buttons_frame, text="Quit", command=self.master.destroy)
        self.quit_button.pack()
        self.buttons_frame.pack(side=tkinter.BOTTOM)

    def _add_mod_from_archive(self):
        file = tkinter.filedialog.askopenfilename(title="Open the archive containing the mod files",
                                                  filetypes=[("Archives (*.zip, *rar)", ".zip .rar")])
        if not file:
            return

        if not Path(file).is_file():
            tkinter.messagebox.showwarning(title="File not found")
            return

        with tempfile.TemporaryDirectory() as temp_dir:
            patoolib.extract_archive(file, outdir=temp_dir)
            try:
                mod_content_folder = self.model.find_or_create_mod_content_folder(temp_dir)
            except RuntimeError as e:
                tkinter.messagebox.showerror("Error", "Could not determine mod content in archive, {}".format(e))
                return
            mod_name = tkinter.simpledialog.askstring("Input the name of the mod", "Mod name",
                                                      initialvalue=Path(file).stem)
            try:
                self.model.add_mod(mod_name, mod_content_folder)
            except RuntimeError as e:
                tkinter.messagebox.showerror("Error", str(e))
                return

        self._refresh()

    def _add_mod_from_folder(self):
        folder = tkinter.filedialog.askdirectory(title="Select the folder containing the mod files")
        if not folder:
            return

        if not Path(folder).is_dir():
            tkinter.messagebox.showwarning(title="Folder not found")
            return

        try:
            mod_content_folder = self.model.find_or_create_mod_content_folder(folder)
        except RuntimeError as e:
            tkinter.messagebox.showerror("Error", "Could not determine mod content in archive, {}".format(e))
            return
        mod_name = tkinter.simpledialog.askstring("Input the name of the mod", "Mod name",
                                                  initialvalue=Path(folder).name)
        try:
            self.model.add_mod(mod_name, mod_content_folder)
        except RuntimeError as e:
            tkinter.messagebox.showerror("Error", str(e))
            return

        self._refresh()

    def _activate_mod(self):
        assert self.selected_managed_mod, "No managed mod selected"
        try:
            self.model.activate_mod(self.selected_managed_mod)
        except RuntimeError as e:
            tkinter.messagebox.showerror("Error",
                                         "Could not activate mod {}, {}".format(self.selected_managed_mod, str(e)))
        self._refresh()

    def _deactivate_mod(self):
        assert self.selected_activated_mod, "No activated mod selected"
        try:
            self.model.deactivate_mod(self.selected_activated_mod)
        except RuntimeError as e:
            tkinter.messagebox.showerror("Error",
                                         "Could not activate mod {}, {}".format(self.selected_managed_mod, str(e)))
        self._refresh()
