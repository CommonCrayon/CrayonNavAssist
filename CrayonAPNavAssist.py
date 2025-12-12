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



class CrayonAPNavAssist(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CrayonAPNavAssist")
        self.geometry("340x460")
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
            self.viewer_window = TargetViewerWindow(self, self.targets, header=self.header_name)
            # center the viewer over this window
            self.viewer_window.update_idletasks()
            x = self.winfo_rootx() + 30
            y = self.winfo_rooty() + 30
            self.viewer_window.geometry(f"+{x}+{y}")
        else:
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
    def __init__(self, parent: CrayonAPNavAssist, targets=None, header=None):
        super().__init__(parent)
        self.parent = parent

        self.title("CrayonNavAssist")
        self.attributes("-topmost", True)


        self.targets = targets
        self.header = header
        self.target_index = 0 if self.targets is not None else -1

        self.grid_columnconfigure(0, weight=1)

        # Main info card
        card = ctk.CTkFrame(self)
        card.grid(row=0, column=0, padx=10, pady=10, sticky="nesw")
        card.grid_columnconfigure(1, weight=1)

        # ID row
        self.id_label = ctk.CTkLabel(card, text="-", font=("Arial", 20))
        self.id_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=6)

        # target coords
        ctk.CTkLabel(card, text="Target:", font=("Arial", 14)).grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.target_label = ctk.CTkLabel(card, text="-", font=("Arial", 20))
        self.target_label.grid(row=1, column=1, sticky="w", padx=8, pady=6)


        # distance
        ctk.CTkLabel(card, text="Distance:", font=("Arial", 14)).grid(row=2, column=0, sticky="e", padx=8, pady=6)
        self.dist_label = ctk.CTkLabel(card, text="-", font=("Arial", 20))
        self.dist_label.grid(row=2, column=1, sticky="w", padx=8, pady=6)

        # required angle
        ctk.CTkLabel(card, text="Required Angle:", font=("Arial", 14)).grid(row=3, column=0, sticky="e", padx=8, pady=6)
        self.required_angle_label = ctk.CTkLabel(card, text="-", font=("Arial", 20))
        self.required_angle_label.grid(row=3, column=1, sticky="w", padx=8, pady=6)

        # turn amount
        ctk.CTkLabel(card, text="Turn Amount:", font=("Arial", 14)).grid(row=4, column=0, sticky="e", padx=8, pady=6)
        self.angle_change_label = ctk.CTkLabel(card, text="-", font=("Arial", 20))
        self.angle_change_label.grid(row=4, column=1, sticky="w", padx=8, pady=6)

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

        # If targets do not just reset everything
        if not self.targets or self.target_index < 0:
            self.id_label.configure(text="-")
            self.target_label.configure(text="-")
            self.dist_label.configure(text="—")
            self.required_angle_label.configure(text="—")
            self.angle_change_label.configure(text="—")
            return
        
        # if player info does not exist, leave it all blank
        if self.parent.player_x is None or self.parent.player_z is None or self.parent.player_yaw is None or self.parent.player_dimension is None:
            self.dist_label.configure(text="—")
            self.required_angle_label.configure(text="—")
            self.angle_change_label.configure(text="—")
            return
        
        target_id = self.targets[self.target_index][0]
        target_x = self.targets[self.target_index][1]
        target_z = self.targets[self.target_index][2]

        player_x = self.parent.player_x
        player_z = self.parent.player_z
        player_yaw = self.parent.player_yaw

        # If player in nether use nether coords as target
        if ("nether" in self.parent.player_dimension):
            target_x = target_x/8
            target_z = target_z/8

        required_angle = compute_yaw_to_target(player_x, player_z, target_x, target_z)            
        angle_change = normalize_angle_delta(required_angle - player_yaw)

        distance_x = player_x - target_x
        distance_z = player_z - target_z

        # Set Labels
        self.id_label.configure(text=f"{target_id}")
        self.target_label.configure(text=f"{target_x:.0f}, {target_z:.0f}")

        self.dist_label.configure(text=f"{distance_x:.0f}, {distance_z:.0f}")
        self.required_angle_label.configure(text=f"{required_angle:.1f}°")
        self.angle_change_label.configure(text=f"{angle_change:+.1f}°")



# Run app
if __name__ == "__main__":
    app = CrayonAPNavAssist()
    app.mainloop()
