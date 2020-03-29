import json
import os
from pathlib import Path
import patoolib
import re
import tkinter as tk
import tempfile
from tkinter import filedialog, messagebox, simpledialog
from typing import Dict
import shutil

from master_manifest import MasterManfiest


def start_gui(configuration: Dict, mod_manager_folder: str, game_folder: str):
    model = MainWindowModel(configuration, mod_manager_folder, game_folder)
    root = tk.Tk()
    main_window = MainWindow(model=model, master=root)
    main_window.mainloop()


class MainWindowModel:
    def __init__(self, configuration: Dict, mod_manager_folder: str, game_folder: str):
        self.mod_manager_folder = Path(mod_manager_folder)
        self.game_folder = Path(game_folder)
        self.configuration = configuration
        self.master_manifest = self._load_master_manifest()

    def _load_master_manifest(self):
        master_manifest_filename = "master_manifest.json"
        master_manifest_path = self.mod_manager_folder / master_manifest_filename
        if not master_manifest_path.is_file():
            master_manifest = MasterManfiest(active_mods=[])
            with open(str(master_manifest_path), "w") as manifest_out_file:
                json.dump(master_manifest._asdict(), manifest_out_file)
        else:
            with open(str(master_manifest_path), "r") as manifest_in_file:
                manifest_dict = json.load(manifest_in_file)
                master_manifest = MasterManfiest(**manifest_dict)
        return master_manifest

    def get_managed_mod_names(self):
        return [content.name for content in self.mod_manager_folder.iterdir() if content.is_dir()]

    def add_mod(self, mod_name: str, mod_content_folder: Path):
        new_mod_folder = self.mod_manager_folder / mod_name
        if new_mod_folder.is_file() or new_mod_folder.is_dir():
            raise RuntimeError("There is a managed mod called '{}' already".format(mod_name))

        new_mod_content_folder = new_mod_folder / "_mod_contents" / mod_content_folder.name
        shutil.copytree(str(mod_content_folder), str(new_mod_content_folder))

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
                        shutil.copytree(str(content.parent), str(content_folder_path))
                        mod_content_folder = mod_archive_contents_folder_path / "heroes"
                        break
            else:
                raise RuntimeError("Could not find mod content in archive")

        return mod_content_folder


class MainWindow(tk.Frame):
    def __init__(self, model: MainWindowModel, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Darkest Dungeon Mod Manager")
        self.model = model
        self._create_widgets()
        self.pack()
        self._refresh()

    def _refresh(self):
        self.managed_mods_listvar.set(self.model.get_managed_mod_names())

    def _create_widgets(self):
        self.managed_mods_frame = tk.Frame(self)
        self.managed_mods_title = tk.Label(self.managed_mods_frame, text="Managed mods")
        self.managed_mods_title.pack()
        self.managed_mods_listvar = tk.StringVar(self.managed_mods_frame)
        self.managed_mods_listview = tk.Listbox(self.managed_mods_frame, listvariable=self.managed_mods_listvar)
        self.managed_mods_listview.pack(side=tk.LEFT)
        self.managed_mods_scrollbar = tk.Scrollbar(self.managed_mods_frame, orient="vertical")
        self.managed_mods_scrollbar.config(command=self.managed_mods_listview.yview)
        self.managed_mods_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.managed_mods_listview.config(yscrollcommand=self.managed_mods_scrollbar.set)
        self.managed_mods_frame.pack()

        self.add_mod_button = tk.Button(self, text="Add Mod from Directory or Archive",
                                        command=self._add_mod_via_gui)
        self.add_mod_button.pack()

        self.quit_button = tk.Button(self, text="Quit", command=self.master.destroy)
        self.quit_button.pack()

    def _add_mod_via_gui(self):
        file = filedialog.askopenfile(title="Open the archive containing the mod files", mode="r",
                                      filetypes=[("Archives (*.zip, *rar)", ".zip .rar")])
        if not file:
            return

        if not Path(file.name).is_file():
            tk.messagebox.showwarning(title="File not found")
            return

        with tempfile.TemporaryDirectory() as temp_dir:
            patoolib.extract_archive(file.name, outdir=temp_dir)
            try:
                mod_content_folder = self.model.find_or_create_mod_content_folder(temp_dir)
            except RuntimeError as e:
                tk.messagebox.showerror("Error", "Could not determine mod content in archive, {}".format(e))
                return
            mod_name = simpledialog.askstring("Input the name of the mod", "Mod name",
                                              initialvalue=Path(file.name).stem)
            try:
                self.model.add_mod(mod_name, mod_content_folder)
            except RuntimeError as e:
                tk.messagebox.showerror("Error", str(e))
                return

        self._refresh()


