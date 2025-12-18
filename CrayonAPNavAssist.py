"""
Example input:

"0:Crayon"
[1,200,100]
[4,500,0]
[5,256,444]
[2,-104,174]
[6,-260,444]
"""

import re
import math
import customtkinter as ctk
from tkinter import messagebox
import keyboard

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# === Regex CONSTANTS ===
# F3+C regex captures [player_dimension, player_x, player_y, player_z, player_yaw, player_pitch]
F3C_REGEX = re.compile(r"execute in minecraft:(\w+) run tp @s ([\-\d\.]+) ([\-\d\.]+) ([\-\d\.]+) ([\-\d\.]+) ([\-\d\.]+)")

# target coordinates. eg: [id, x, z]
TARGET_REGEX = re.compile(r"\[\s*([+-]?\d+)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\]")



# === Math helpers ===
def compute_yaw_to_target(player_x, player_z, target_x, target_z):
    return math.degrees(math.atan2(player_x - target_x, target_z - player_z))

def normalize_angle_delta(angle):
    # normalize to (-180, 180) because minecraft...
    a = angle
    while a > 180:
        a -= 360
    while a <= -180:
        a += 360
    return a

def value_to_color(value, green_range, red_range):
    value = abs(value)

    if value <= green_range:
        return "#00ff00"
    if value >= red_range:
        return "#ff0000"

    # normalise
    t = (value - green_range) / (red_range - green_range)

    # green to red gradient
    r = int(255 * t)
    g = int(255 * (1 - t))
    return f"#{r:02x}{g:02x}00"



class CrayonAPNavAssist(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CrayonAPNavAssist")
        self.geometry("340x520")
        self.grid_columnconfigure(0, weight=1)

        # Player / F3+C state
        self.player_dimension = None
        self.player_x = None
        self.player_y = None
        self.player_z = None
        self.player_yaw = None
        self.player_pitch = None

        self.targets = []
        self.header_name = None

        self.viewer_window = None

        ctk.CTkLabel(self, text="All Portals Navigator", font=("Arial", 24)).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nesw")
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

        # Status labels
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(status_frame, text="F3+C Status:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.f3c_status = ctk.CTkLabel(status_frame, text="Not loaded", text_color="red")
        self.f3c_status.grid(row=0, column=1, padx=6, pady=8, sticky="w")

        # Rebind Frame
        rebind_frame = ctk.CTkFrame(self)
        rebind_frame.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="ew")
        rebind_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(rebind_frame, text="Rebind Controls:", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="nesw")

        ctk.CTkLabel(rebind_frame, text="Prev Item:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.prev_item_bind_var = ctk.StringVar(value="ctrl+left")
        self.prev_item_entry = ctk.CTkEntry(rebind_frame, textvariable=self.prev_item_bind_var, font=("Arial", 14))
        self.prev_item_entry.grid(row=1, column=1, sticky="nesw", padx=10, pady=4)

        ctk.CTkLabel(rebind_frame, text="Next Item:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.next_item_bind_var = ctk.StringVar(value="ctrl+right")
        self.next_item_entry = ctk.CTkEntry(rebind_frame, textvariable=self.next_item_bind_var, font=("Arial", 14))
        self.next_item_entry.grid(row=2, column=1, sticky="nesw", padx=10, pady=4)

        # Start clipboard updates for F3+C
        self._last_clip = ""
        self.after(250, self.clipboard_update)


    def launch(self):
        # PARSE STRING FIRST THEN LAUNCH WINDOW

        text = self.list_text.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Parse", "Textbox is empty.")
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

        # TODO - Replace MessageBox
        if len(self.targets) == 0:
            messagebox.showwarning("Parse", "No target lines were found. Make sure lines look like: [1,2000,0]")

        # If viewer open, refresh its data. Otherwise Open
        if self.viewer_window is not None and self.viewer_window.winfo_exists():
            self.viewer_window.set_targets(self.targets, header=self.header_name)
        else:
            self.launch_window()


    # Opens Window to be used
    def launch_window(self):

        # TODO - Replace Message Box
        if self.targets is None or len(self.targets) == 0:
            if not messagebox.askyesno("No targets", "No targets parsed. Open empty viewer anyway?"):
                return

        if self.viewer_window is None or not self.viewer_window.winfo_exists():
            self.viewer_window = TargetViewerWindow(self, self.targets, header=self.header_name, prev_item_bind=self.prev_item_bind_var.get(), next_item_bind=self.next_item_bind_var.get())
            # center the viewer over this window
            self.viewer_window.update_idletasks()
            x = self.winfo_rootx() + 30
            y = self.winfo_rooty() + 30
            self.viewer_window.geometry(f"+{x}+{y}")
        else:
            # Set binds, in case new ones
            self.viewer_window.prev_item_bind = self.prev_item_bind_var.get()
            self.viewer_window.next_item_bind = self.next_item_bind_var.get()

            # bring to front
            self.viewer_window.lift()
            self.viewer_window.focus_force()

        # ensure viewer knows current F3+C state
        if self._last_clip and F3C_REGEX.search(self._last_clip):
            self.parse_f3c(self._last_clip)



    #==========================================================================================================================
    # Clipboard / F3+C handling
    #==========================================================================================================================
    def clipboard_update(self):
        try:
            text = self.clipboard_get()
        except Exception:
            text = ""

        if text != self._last_clip:
            self._last_clip = text
            self.parse_f3c(text)

        # update again
        self.after(250, self.clipboard_update)

    def parse_f3c(self, text):
        match = F3C_REGEX.search(text)

        # Checks if clipboard contains minecraft f3+c info
        if not match:
            self.f3c_status.configure(text="Not loaded", text_color="red")
            return

        # Parses minecraft f3+c values if it contains information
        try:
            self.player_dimension = match.group(1)
            self.player_x = float(match.group(2))
            self.player_y = float(match.group(3))
            self.player_z = float(match.group(4))
            self.player_yaw = float(match.group(5))
            self.player_pitch = float(match.group(6))
            self.f3c_status.configure(text=f"Loaded ({self.player_dimension}) at [{self.player_x}, {self.player_y}, {self.player_z}]", text_color="green")
        except Exception:
            # if parse failed, mark as not loaded
            self.f3c_status.configure(text="Parse failed", text_color="red")

        # If viewer open, trigger recalculation/redraw
        if self.viewer_window is not None and self.viewer_window.winfo_exists():
            self.viewer_window.refresh()


class TargetViewerWindow(ctk.CTkToplevel):
    def __init__(self, parent: CrayonAPNavAssist, targets=None, header=None, prev_item_bind=None, next_item_bind=None):
        super().__init__(parent)
        self.parent = parent

        # Binds to go to next stronghold and previous stronghold
        self.prev_item_bind = prev_item_bind
        self.next_item_bind = next_item_bind

        self.title("CrayonNavAssist")
        self.attributes("-topmost", True)



        self.targets = targets
        self.header = header
        self.target_index = 0 if self.targets is not None else -1

        self.grid_columnconfigure(0, weight=1)

        # Main info card
        card = ctk.CTkFrame(self)
        card.grid(row=0, column=0, padx=10, pady=10, sticky="nesw")

        # text_width = ctk.CTkFont(family="Arial", size=14).measure("+180.0°")  # text width in pixels
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=1)

        # ID row
        self.id_label = ctk.CTkLabel(card, text="-", font=("Arial", 20))
        self.id_label.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=6)

        # target coords
        ctk.CTkLabel(card, text="Target (X, Z):", font=("Arial", 14)).grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.target_x_label = ctk.CTkLabel(card, width=100, text="-", font=("Arial", 20))
        self.target_x_label.grid(row=1, column=1, sticky="we", padx=0, pady=6)
        self.target_z_label = ctk.CTkLabel(card, width=100, text="-", font=("Arial", 20))
        self.target_z_label.grid(row=1, column=2, sticky="we", padx=0, pady=6)

        # distance
        ctk.CTkLabel(card, text="Distance (X, Z):", font=("Arial", 14)).grid(row=2, column=0, sticky="e", padx=8, pady=6)
        self.distance_x_label = ctk.CTkLabel(card, width=100, text="-", font=("Arial", 20))
        self.distance_x_label.grid(row=2, column=1, sticky="we", padx=0, pady=6)
        self.distance_z_label = ctk.CTkLabel(card, width=100, text="-", font=("Arial", 20))
        self.distance_z_label.grid(row=2, column=2, sticky="we", padx=0, pady=6)

        # required angle
        ctk.CTkLabel(card, text="Required Angle:", font=("Arial", 14)).grid(row=3, column=0, sticky="e", padx=8, pady=6)
        self.required_angle_label = ctk.CTkLabel(card, text="-", font=("Arial", 20))
        self.required_angle_label.grid(row=3, column=1, columnspan=2, sticky="we", padx=0, pady=6)

        # turn amount
        ctk.CTkLabel(card, text="Turn Amount:", font=("Arial", 14)).grid(row=4, column=0, sticky="e", padx=8, pady=6)
        self.angle_change_label = ctk.CTkLabel(card, text="-", font=("Arial", 20))
        self.angle_change_label.grid(row=4, column=1, columnspan=2, sticky="we", padx=0, pady=6)

        # Next and Previous Stronghold buttons
        nav = ctk.CTkFrame(self)
        nav.grid(row=2, column=0, pady=(0, 10), padx=10, sticky="ew")
        nav.grid_columnconfigure((0, 1, 2), weight=1)

        self.prev_btn = ctk.CTkButton(nav, text="◀ Prev", command=self.prev_item, width=120)
        self.prev_btn.grid(row=0, column=0, padx=6, pady=8, sticky="w")

        self.target_title_label = ctk.CTkLabel(nav, text=self.target_index_text(), font=("Arial", 12))
        self.target_title_label.grid(row=0, column=1, padx=6, pady=8)

        self.next_btn = ctk.CTkButton(nav, text="Next ▶", command=self.next_item, width=120)
        self.next_btn.grid(row=0, column=2, padx=6, pady=8, sticky="e")

        # Bind next stronghold and prev stronghold
        keyboard.add_hotkey(self.prev_item_bind.lower(), self.prev_item)
        keyboard.add_hotkey(self.next_item_bind.lower(), self.next_item)

        # start refresh
        self.refresh()


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

            self.target_x_label.configure(text="—")
            self.target_z_label.configure(text="—")

            self.distance_x_label.configure(text="—")
            self.distance_z_label.configure(text="—")

            self.required_angle_label.configure(text="—")
            self.angle_change_label.configure(text="—")
            return
        
        # Target variables
        target_id = self.targets[self.target_index][0]
        target_x = self.targets[self.target_index][1]
        target_z = self.targets[self.target_index][2]

        #======================================================
        # F3+C Variables Handling
        #======================================================

        # if player info does not exist, leave it all blank
        if self.parent.player_x is None or self.parent.player_z is None or self.parent.player_yaw is None or self.parent.player_dimension is None:
            self.distance_x_label.configure(text="—")
            self.distance_z_label.configure(text="—")

            self.required_angle_label.configure(text="—")
            self.angle_change_label.configure(text="—")
        
        else:
            # When player info exists
            player_x = self.parent.player_x
            player_z = self.parent.player_z
            player_yaw = self.parent.player_yaw

            # If player in nether use nether coords as target
            if ("nether" in self.parent.player_dimension):
                target_x = target_x/8
                target_z = target_z/8

            required_angle = compute_yaw_to_target(player_x, player_z, target_x, target_z)    

            angle_change = normalize_angle_delta(required_angle - player_yaw)
            angle_color = value_to_color(abs(angle_change), 5, 180)

            distance_x = int(player_x - target_x)
            distance_z = int(player_z - target_z)

            distance_x_color = value_to_color(distance_x, 5, 100)
            distance_z_color = value_to_color(distance_z, 5, 100)

            self.distance_x_label.configure(text=f"{distance_x}", text_color=distance_x_color)
            self.distance_z_label.configure(text=f"{distance_z}", text_color=distance_z_color)
            
            self.required_angle_label.configure(text=f"{required_angle:.1f}°")


            self.angle_change_label.configure(text=f"{angle_change:+.1f}°", text_color=angle_color)

        # Set Labels for non reliant F3+C variables 
        self.id_label.configure(text=f"{target_id}")
        self.target_x_label.configure(text=f"{int(target_x)}")
        self.target_z_label.configure(text=f"{int(target_z)}")



# Run app
if __name__ == "__main__":
    app = CrayonAPNavAssist()
    app.mainloop()
