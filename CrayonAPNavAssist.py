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

# === Regexes ===
# F3+C regex you provided (captures dimension, px, py, pz, yaw, pitch)
F3C_REGEX = re.compile(r"execute in minecraft:(\w+) run tp @s ([\-\d\.]+) ([\-\d\.]+) ([\-\d\.]+) ([\-\d\.]+) ([\-\d\.]+)")

# target line: [id, x, z] with optional whitespace and optional floats/ints
TARGET_REGEX = re.compile(r"\[\s*([+-]?\d+)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\]")



# === Math helpers ===
def compute_yaw_to_target(px, pz, tx, tz):
    return math.degrees(math.atan2(px - tx, tz - pz))

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
        self.dim = None
        self.px = None
        self.py = None
        self.pz = None
        self.yaw = None
        self.pitch = None

        # parsed targets list: [{'id':int,'x':float,'z':float}]
        self.targets = []
        self.header_name = None

        # viewer window handle
        self.viewer_win = None

        # UI: top instructions
        ctk.CTkLabel(self, text="All Portals Navigator", font=("Arial", 24)).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nesw")
        ctk.CTkLabel(self, text="Paste list below:", font=("Arial", 18)).grid(row=1, column=0, padx=10, pady=(10, 2), sticky="w")

        # Textbox for list
        self.list_text = ctk.CTkTextbox(self, font=("Arial", 18))
        self.list_text.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Controls frame
        cf = ctk.CTkFrame(self)
        cf.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nesw")
        cf.grid_columnconfigure((0), weight=1)

        self.open_viewer_btn = ctk.CTkButton(cf, text="Launch", font=("Arial", 18), command=self.launch)
        self.open_viewer_btn.grid(row=0, column=0, sticky="nesw")

        # Status labels
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(status_frame, text="F3+C Status:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.f3c_status = ctk.CTkLabel(status_frame, text="Not loaded", text_color="red")
        self.f3c_status.grid(row=0, column=1, padx=6, pady=8, sticky="w")

        # Start clipboard polling for F3+C
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

        # parse for id and x, z
        for ln in lines:
            m = TARGET_REGEX.search(ln)
            if m:
                tid = int(m.group(1))
                tx = float(m.group(2))
                tz = float(m.group(3))
                self.targets.append({"id": tid, "x": tx, "z": tz})
            else:
                continue

        # TODO - Replace
        if len(self.targets) == 0:
            messagebox.showwarning("Parse", "No target lines were found. Make sure lines look like: [1,2000,0]")

        # If viewer open, refresh its data. Otherwise Open
        if self.viewer_win is not None and self.viewer_win.winfo_exists():
            self.viewer_win.set_targets(self.targets, header=self.header_name)
        else:
            self.launch_window()


    # Opens Window to be used
    def launch_window(self):

        # TODO - Replace
        if self.targets is None or len(self.targets) == 0:
            if not messagebox.askyesno("No targets", "No targets parsed. Open empty viewer anyway?"):
                return

        if self.viewer_win is None or not self.viewer_win.winfo_exists():
            self.viewer_win = TargetViewerWindow(self, self.targets, header=self.header_name)
            # center the viewer over this window
            self.viewer_win.update_idletasks()
            x = self.winfo_rootx() + 30
            y = self.winfo_rooty() + 30
            self.viewer_win.geometry(f"+{x}+{y}")
        else:
            # bring to front
            self.viewer_win.lift()
            self.viewer_win.focus_force()

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
        if not match:
            # if F3+C not present, clear player state but keep any loaded previously?
            # We'll mark as not loaded but keep recent values (so the viewer can still show)
            self.f3c_status.configure(text="Not loaded", text_color="red")
            # do not clear px/py/pz so that calculations can continue if desired?
            # The user said "When not loaded just don't calculate but move to view" -> so we won't calculate.
            return

        # parse values
        try:
            self.dim = match.group(1)
            self.px = float(match.group(2))
            self.py = float(match.group(3))
            self.pz = float(match.group(4))
            self.yaw = float(match.group(5))
            self.pitch = float(match.group(6))
            self.f3c_status.configure(text=f"Loaded ({self.dim}) at [{self.px}, {self.py}, {self.pz}]", text_color="green")
        except Exception:
            # if parse failed, mark as not loaded
            self.f3c_status.configure(text="Parse failed", text_color="red")

        # If viewer open, trigger recalculation/redraw
        if self.viewer_win is not None and self.viewer_win.winfo_exists():
            self.viewer_win.refresh()


    # helper for viewer to query current player state
    def get_player_state(self):
        if self.px is None or self.pz is None or self.yaw is None or self.dim is None:
            return None
        return {"dim": self.dim, "px": self.px, "py": self.py, "pz": self.pz, "yaw": self.yaw, "pitch": self.pitch}




class TargetViewerWindow(ctk.CTkToplevel):
    def __init__(self, parent: CrayonAPNavAssist, targets=None, header=None):
        super().__init__(parent)
        self.parent = parent

        self.title("CrayonNavAssist")
        self.attributes("-topmost", True)

        # data
        self.targets = targets[:] if targets else []
        self.header = header
        self.index = 0 if self.targets else -1

        # layout
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

        # required yaw
        ctk.CTkLabel(card, text="Required Yaw:", font=("Arial", 14)).grid(row=3, column=0, sticky="e", padx=8, pady=6)
        self.req_yaw_label = ctk.CTkLabel(card, text="-", font=("Arial", 20))
        self.req_yaw_label.grid(row=3, column=1, sticky="w", padx=8, pady=6)

        # turn amount
        ctk.CTkLabel(card, text="Turn Amount:", font=("Arial", 14)).grid(row=4, column=0, sticky="e", padx=8, pady=6)
        self.turn_label = ctk.CTkLabel(card, text="-", font=("Arial", 20))
        self.turn_label.grid(row=4, column=1, sticky="w", padx=8, pady=6)

        # Index / navigation
        nav = ctk.CTkFrame(self)
        nav.grid(row=2, column=0, pady=(0, 10), padx=10, sticky="ew")
        nav.grid_columnconfigure((0, 1, 2), weight=1)

        self.prev_btn = ctk.CTkButton(nav, text="◀ Prev", command=self.prev_item, width=120)
        self.prev_btn.grid(row=0, column=0, padx=6, pady=8, sticky="w")

        self.index_label = ctk.CTkLabel(nav, text=self.index_text(), font=("Arial", 12))
        self.index_label.grid(row=0, column=1, padx=6, pady=8)

        self.next_btn = ctk.CTkButton(nav, text="Next ▶", command=self.next_item, width=120)
        self.next_btn.grid(row=0, column=2, padx=6, pady=8, sticky="e")

        # keyboard bindings
        self.bind("<Left>", lambda e: self.prev_item())
        self.bind("<Right>", lambda e: self.next_item())
        self.focus_force()

        # initial display
        self.refresh()


    #==========================
    # Helper Functions
    #==========================
    def set_targets(self, targets, header=None):
        self.targets = targets[:] if targets else []
        self.header = header
        self.index = 0 if self.targets else -1
        self.refresh()

    def index_text(self):
        if not self.targets:
            return "0 / 0"
        return f"{self.index+1} / {len(self.targets)}"

    def prev_item(self):
        if not self.targets:
            return
        self.index = max(0, self.index - 1)
        self.refresh()

    def next_item(self):
        if not self.targets:
            return
        self.index = min(len(self.targets) - 1, self.index + 1)
        self.refresh()


    #==========================
    # Refresh
    #==========================
    def refresh(self):
        # Update index label
        self.index_label.configure(text=self.index_text())

        # enable/disable nav buttons
        if not self.targets or len(self.targets) <= 1:
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")
        else:
            self.prev_btn.configure(state="normal" if self.index > 0 else "disabled")
            self.next_btn.configure(state="normal" if self.index < len(self.targets) - 1 else "disabled")

        # Update the main fields
        if not self.targets or self.index < 0:
            self.id_label.configure(text="-")
            self.target_label.configure(text="-")
            self.dist_label.configure(text="—")
            self.req_yaw_label.configure(text="—")
            self.turn_label.configure(text="—")
            return

        t = self.targets[self.index]
        self.id_label.configure(text=f"{t.get('id', '-')}")

        # Try to compute values if parent has F3+C loaded
        player = self.parent.get_player_state()
        if not player:
            # not loaded: show placeholder
            self.dist_label.configure(text="—")
            self.req_yaw_label.configure(text="—")
            self.turn_label.configure(text="—")
        else:
            dim = player["dim"]
            px = player["px"]
            pz = player["pz"]
            yaw = player["yaw"]

            tx = t["x"]
            tz = t["z"]

            if ("nether" in dim):
                tx = tx/8
                tz = tz/8

            needed_yaw = compute_yaw_to_target(px, pz, tx, tz)            
            yaw_change = normalize_angle_delta(needed_yaw - yaw)

            distance_x = px - tx
            distance_z = pz - tz

            # Set Labels
            self.target_label.configure(text=f"{tx:.0f}, {tz:.0f}")

            self.dist_label.configure(text=f"{distance_x:.0f}, {distance_z:.0f}")
            self.req_yaw_label.configure(text=f"{needed_yaw:.1f}°")
            self.turn_label.configure(text=f"{yaw_change:+.1f}°")

        # Make sure labels repaint
        self.update_idletasks()


# Run app
if __name__ == "__main__":
    app = CrayonAPNavAssist()
    app.mainloop()
