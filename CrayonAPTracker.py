import re
import customtkinter as ctk
from  CustomTkinterMessagebox  import *
import keyboard

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# === Regex CONSTANTS ===
# target coordinates. eg: [id, x, z]
TARGET_REGEX = re.compile(r"\[\s*([+-]?\d+)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\]")



class CrayonAPTracker(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CrayonAPTracker")
        self.geometry("340x475")
        self.grid_columnconfigure(0, weight=1)

        # Target
        self.targets = []
        self.header_name = None

        self.viewer_window = None

        ctk.CTkLabel(self, text="All Portals Tracker", font=("Arial", 24)).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nesw")
        ctk.CTkLabel(self, text="Paste list below:", font=("Arial", 18)).grid(row=1, column=0, padx=10, pady=(10, 2), sticky="w")

        # Textbox for list
        self.list_text = ctk.CTkTextbox(self, font=("Arial", 18))
        self.list_text.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Add temp blind coordinates on start up
        self.list_text.insert("1.0", "[1, 2048, 0]\n[2, 5120, 0]\n[3, 8192, 0]\n[4, 11264, 0]\n[5, 14336, 0]\n[6, 17408, 0]\n[7, 20480, 0]\n[8, 23552, 0]")

        # Button frame
        launch_frame = ctk.CTkFrame(self)
        launch_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nesw")
        launch_frame.grid_columnconfigure((0), weight=1)

        ctk.CTkButton(launch_frame, text="Launch", font=("Arial", 18), command=self.launch).grid(row=0, column=0, sticky="nesw")

        # Rebind Frame
        rebind_frame = ctk.CTkFrame(self)
        rebind_frame.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
        rebind_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(rebind_frame, text="Rebind Controls", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="nesw")

        ctk.CTkLabel(rebind_frame, text="Prev Item:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.prev_item_bind_var = ctk.StringVar(value="ctrl+left")
        self.prev_item_entry = ctk.CTkEntry(rebind_frame, textvariable=self.prev_item_bind_var, font=("Arial", 14))
        self.prev_item_entry.grid(row=1, column=1, sticky="nesw", padx=10, pady=4)

        ctk.CTkLabel(rebind_frame, text="Next Item:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.next_item_bind_var = ctk.StringVar(value="ctrl+right")
        self.next_item_entry = ctk.CTkEntry(rebind_frame, textvariable=self.next_item_bind_var, font=("Arial", 14))
        self.next_item_entry.grid(row=2, column=1, sticky="nesw", padx=10, pady=4)



    def launch(self):
        # PARSE STRING FIRST THEN LAUNCH WINDOW

        text = self.list_text.get("1.0", "end").strip()
        if not text:
            CTkMessagebox.messagebox("Error", "Textbox is empty.")
            return

        # reset
        self.targets = []
        self.header_name = None

        # Parse text
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() != ""]
        if lines and re.match(r'^\s*"?\d+:.*"?\s*$', lines[0]):
            # player name and id
            self.header_name = lines[0].strip().strip('"')
            
            # Exclude header
            lines = lines[1:]

        # Get target coordinates
        for ln in lines:
            m = TARGET_REGEX.search(ln)
            if m:
                self.targets.append([int(m.group(1)), int(m.group(2)), int(m.group(3))])
            else:
                continue
        
        # When no targets found
        if self.targets is None or len(self.targets) == 0:
            CTkMessagebox.messagebox("Error", "No target lines were found.\nMake sure lines look like: [1,2000,0]")
            return


        # If viewer open, refresh its data. Otherwise Open
        if self.viewer_window is not None and self.viewer_window.winfo_exists():
            # Set binds, in case new ones
            self.viewer_window.update_item_hotkeys(self.prev_item_bind_var.get(),  self.next_item_bind_var.get())

            self.viewer_window.set_targets(self.targets, header=self.header_name)
        else:
            self.launch_window()


    # Opens Window to be used
    def launch_window(self):

        if self.viewer_window is None or not self.viewer_window.winfo_exists():
            self.viewer_window = TargetViewerWindow(self, self.targets, header=self.header_name, prev_item_bind=self.prev_item_bind_var.get(), next_item_bind=self.next_item_bind_var.get())
            # center the viewer over this window
            self.viewer_window.update_idletasks()
            x = self.winfo_rootx() + 30
            y = self.winfo_rooty() + 30
            self.viewer_window.geometry(f"+{x}+{y}")
        else:
            # bring to front
            self.viewer_window.lift()
            self.viewer_window.focus_force()




class TargetViewerWindow(ctk.CTkToplevel):
    def __init__(self, parent: CrayonAPTracker, targets=None, header=None, prev_item_bind=None, next_item_bind=None):
        super().__init__(parent)
        self.parent = parent

        self.title("CrayonAPTracker")
        self.attributes("-topmost", True)

        self.prev_hotkey_id = None
        self.next_hotkey_id = None

        self.targets = targets
        self.header = header
        self.target_index = 0 if self.targets is not None else -1

        self.grid_columnconfigure(0, weight=1)

        # Main info card
        card = ctk.CTkFrame(self)
        card.grid(row=0, column=0, padx=10, pady=10, sticky="nesw")

        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=1)

        # ID row
        self.id_label = ctk.CTkLabel(card, text=f"{self.targets[0][0]}", font=("Arial", 22))
        self.id_label.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=6)

        ctk.CTkLabel(card, text="X", font=("Arial", 14, "bold")).grid(row=1, column=1, sticky="nesw", padx=8, pady=6)
        ctk.CTkLabel(card, text="Z", font=("Arial", 14, "bold")).grid(row=1, column=2, sticky="nesw", padx=8, pady=6)

        # Overworld coords
        ctk.CTkLabel(card, text="Overworld", font=("Arial", 14, "bold")).grid(row=2, column=0, sticky="nse", padx=8, pady=6)
        self.overworld_x_label = ctk.CTkLabel(card, width=100, text=f"{int(self.targets[0][1])}", font=("Arial", 20))
        self.overworld_x_label.grid(row=2, column=1, sticky="nswe", padx=0, pady=6)
        self.overworld_z_label = ctk.CTkLabel(card, width=100, text=f"{int(self.targets[0][2])}", font=("Arial", 20))
        self.overworld_z_label.grid(row=2, column=2, sticky="nswe", padx=0, pady=6)

        # Nether coords
        ctk.CTkLabel(card, text="Nether", font=("Arial", 14, "bold")).grid(row=3, column=0, sticky="nse", padx=8, pady=6)
        self.nether_x_label = ctk.CTkLabel(card, width=100, text=f"{int(self.targets[0][1]/8)}", font=("Arial", 20))
        self.nether_x_label.grid(row=3, column=1, sticky="nswe", padx=0, pady=6)
        self.nether_z_label = ctk.CTkLabel(card, width=100, text=f"{int(self.targets[0][2]/8)}", font=("Arial", 20))
        self.nether_z_label.grid(row=3, column=2, sticky="nswe", padx=0, pady=6)

        # Next and Previous Stronghold buttons
        nav = ctk.CTkFrame(self)
        nav.grid(row=4, column=0, pady=(0, 10), padx=10, sticky="ew")
        nav.grid_columnconfigure((0, 1, 2), weight=1)

        self.prev_btn = ctk.CTkButton(nav, text="◀ Prev", command=self.prev_item, width=120)
        self.prev_btn.grid(row=0, column=0, padx=6, pady=8, sticky="w")

        self.target_title_label = ctk.CTkLabel(nav, text=self.target_index_text(), font=("Arial", 12))
        self.target_title_label.grid(row=0, column=1, padx=6, pady=8)

        self.next_btn = ctk.CTkButton(nav, text="Next ▶", command=self.next_item, width=120)
        self.next_btn.grid(row=0, column=2, padx=6, pady=8, sticky="e")

        # Bind next stronghold and prev stronghold
        self.update_item_hotkeys(prev_item_bind.lower(), next_item_bind.lower())



    #==========================
    # Helper Functions
    #==========================
    def set_targets(self, targets, header=None):
        self.targets = targets[:] if targets else []
        self.header = header
        self.target_index = 0 if self.targets else -1
        self.refresh()

    def target_index_text(self):
        if not self.targets:
            return "0 / 0"
        return f"{self.target_index+1} / {len(self.targets)}"

    def update_item_hotkeys(self, prev_item_bind, next_item_bind):
        # Remove old bindings if they exist
        if self.prev_hotkey_id is not None:
            keyboard.remove_hotkey(self.prev_hotkey_id)
            self.prev_hotkey_id = None

        if self.next_hotkey_id is not None:
            keyboard.remove_hotkey(self.next_hotkey_id)
            self.next_hotkey_id = None

        # Add new bindings
        self.prev_hotkey_id = keyboard.add_hotkey(prev_item_bind, self.prev_item)
        self.next_hotkey_id = keyboard.add_hotkey(next_item_bind, self.next_item)

    def prev_item(self):
        if not self.targets:
            return
        self.target_index = max(0, self.target_index - 1)
        self.refresh()

    def next_item(self):
        if not self.targets:
            return
        self.target_index = min(len(self.targets) - 1, self.target_index + 1)
        self.refresh()


    #==========================
    # Refresh
    #==========================
    def refresh(self):
        # Update index label
        self.target_title_label.configure(text=self.target_index_text())

        # enable/disable nav buttons
        if not self.targets or len(self.targets) <= 1:
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")
        else:
            self.prev_btn.configure(state="normal" if self.target_index > 0 else "disabled")
            self.next_btn.configure(state="normal" if self.target_index < len(self.targets) - 1 else "disabled")

        #======================================================
        # Target Handling
        #======================================================
        # If targets do not just reset everything
        if not self.targets or self.target_index < 0:
            self.id_label.configure(text="—")

            self.overworld_x_label.configure(text="—")
            self.overworld_z_label.configure(text="—")

            self.nether_x_label.configure(text="—")
            self.nether_z_label.configure(text="—")
            return
        
        # Target variables
        target_id = self.targets[self.target_index][0]
        target_x = self.targets[self.target_index][1]
        target_z = self.targets[self.target_index][2]

        # Set Labels
        self.id_label.configure(text=f"{target_id}")
        self.overworld_x_label.configure(text=f"{int(target_x)}")
        self.overworld_z_label.configure(text=f"{int(target_z)}")

        self.nether_x_label.configure(text=f"{int(target_x/8)}")
        self.nether_z_label.configure(text=f"{int(target_z/8)}")



# Run app
if __name__ == "__main__":
    app = CrayonAPTracker()
    app.mainloop()
