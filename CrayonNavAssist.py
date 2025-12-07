import customtkinter as ctk
import re
import math

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

F3C_REGEX = re.compile(r"execute in minecraft:(\w+) run tp @s ([\-\d\.]+) ([\-\d\.]+) ([\-\d\.]+) ([\-\d\.]+) ([\-\d\.]+)")

def compute_yaw_to_target(px, pz, tx, tz):
    return math.degrees(math.atan2(px - tx, tz - pz))

def compute_distance(px, pz, tx, tz):
    return math.sqrt((tx - px)**2 + (tz - pz)**2)





class CrayonNavAssist(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CrayonNavAssist")
        self.attributes('-topmost', True)

        self.last_clip = ""

        # GLOBAL GRID CONFIG
        self.grid_columnconfigure(0, weight=1)

        #======================================================
        # RESULTS FRAME
        #======================================================
        results = ctk.CTkFrame(self)
        results.grid(row=0, column=0, pady=(10, 0), padx=10, sticky="nwe")
        results.grid_columnconfigure(1, weight=1)

        # Labels
        ctk.CTkLabel(results, text="Distance:", anchor="e", font=("Arial", 16)).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(results, text="Required Yaw:", anchor="e", font=("Arial", 16)).grid(row=1, column=0, padx=5, pady=5)
        ctk.CTkLabel(results, text="Turn Amount:", anchor="e", font=("Arial", 16)).grid(row=2, column=0, padx=5, pady=5)

        # Dynamic values
        self.dist_label = ctk.CTkLabel(results, text="-", font=("Arial", 24))
        self.dist_label.grid(row=0, column=1, sticky="w", padx=5)

        self.req_yaw_label = ctk.CTkLabel(results, text="-", font=("Arial", 24))
        self.req_yaw_label.grid(row=1, column=1, sticky="w", padx=5)

        self.turn_label = ctk.CTkLabel(results, text="-", font=("Arial", 24))
        self.turn_label.grid(row=2, column=1, sticky="w", padx=5)

        #======================================================
        # TARGET FRAME
        #======================================================
        target_frame = ctk.CTkFrame(self)
        target_frame.grid(row=1, column=0, pady=10, padx=10, sticky="nwe")
        target_frame.grid_columnconfigure((1, 3), weight=1)

        # OVERWORLD TARGET
        ctk.CTkLabel(target_frame, text="Overworld Target", font=("Arial", 16)).grid(row=0, column=0, columnspan=5, pady=5)

        ctk.CTkLabel(target_frame, text="X:").grid(row=1, column=0, padx=5, pady=(0, 5))
        self.ow_x_entry = ctk.CTkEntry(target_frame, width=80)
        self.ow_x_entry.grid(row=1, column=1, padx=5, pady=(0, 5))

        ctk.CTkLabel(target_frame, text="Z:").grid(row=1, column=2, padx=5, pady=(0, 5))
        self.ow_z_entry = ctk.CTkEntry(target_frame, width=80)
        self.ow_z_entry.grid(row=1, column=3, padx=5, pady=(0, 5))

        ctk.CTkButton(target_frame, text="SET", width=60, font=("Arial", 16), command=self.set_overworld_target).grid(row=1, column=4, padx=5)

        # NETHER TARGET
        ctk.CTkLabel(target_frame, text="Nether Target", font=("Arial", 16)).grid(row=2, column=0, columnspan=5, pady=5)

        ctk.CTkLabel(target_frame, text="X:").grid(row=3, column=0, padx=5, pady=(0, 5))
        self.nw_x_entry = ctk.CTkEntry(target_frame, width=80)
        self.nw_x_entry.grid(row=3, column=1, padx=5, pady=(0, 5))

        ctk.CTkLabel(target_frame, text="Z:").grid(row=3, column=2, padx=5, pady=(0, 5))
        self.nw_z_entry = ctk.CTkEntry(target_frame, width=80)
        self.nw_z_entry.grid(row=3, column=3, padx=5, pady=(0, 5))

        ctk.CTkButton(target_frame, text="SET", width=60, font=("Arial", 16), command=self.set_nether_target).grid(row=3, column=4, padx=5, pady=(0, 5))

        #======================================================
        # Player Information
        #======================================================
        info_frame = ctk.CTkFrame(self)
        info_frame.grid(row=3, column=0, pady=(0, 10), padx=10, sticky="nwe")

        info_frame.grid_columnconfigure(0, weight=1)

        self.nav_target_info = ctk.CTkLabel(info_frame, text="Set Target Above!", text_color="red", font=("Arial", 16))
        self.nav_target_info.grid(row=0, column=0, columnspan=5, pady=5)

        self.nav_player_info = ctk.CTkLabel(info_frame, text="Press F3 + C!", text_color="red", font=("Arial", 16))
        self.nav_player_info.grid(row=1, column=0, columnspan=5, pady=5)

        self.nav_textbox_info = ctk.CTkTextbox(info_frame, height=32, state="disabled")
        self.nav_textbox_info.grid(row=2, column=0, columnspan=5, padx=5, pady=5, sticky="ew")

        #======================================================
        # Player Incoming Data
        #======================================================
        self.dim = None
        self.px = 0
        self.py = 0
        self.pz = 0
        self.yaw = 0
        self.pitch = 0

        # Active target
        self.target_x = None
        self.target_z = None

        # Clipboard checker
        self.after(300, self.check_clipboard)



    # SET Overworld Target
    def set_overworld_target(self):
        try:
            self.target_x = float(self.ow_x_entry.get())
            self.target_z = float(self.ow_z_entry.get())
        except:
            return

        # auto-convert nether
        self.nw_x_entry.delete(0, "end")
        self.nw_z_entry.delete(0, "end")
        self.nw_x_entry.insert(0, f"{self.target_x/8:.2f}")
        self.nw_z_entry.insert(0, f"{self.target_z/8:.2f}")

        self.nav_target_info.configure(text="Target Set!", text_color="green")

        self.calculate()



    # SET Nether Target
    def set_nether_target(self):
        try:
            nx = float(self.nw_x_entry.get())
            nz = float(self.nw_z_entry.get())
        except:
            return

        self.target_x = nx * 8
        self.target_z = nz * 8

        self.ow_x_entry.delete(0, "end")
        self.ow_z_entry.delete(0, "end")
        self.ow_x_entry.insert(0, f"{self.target_x:.2f}")
        self.ow_z_entry.insert(0, f"{self.target_z:.2f}")

        self.nav_target_info.configure(text="Target Set!", text_color="green")

        self.calculate()



    # CLIPBOARD MONITOR
    def check_clipboard(self):
        try:
            text = self.clipboard_get()
        except:
            text = ""

        if text != self.last_clip:
            self.last_clip = text
            self.parse_f3c(text)
            self.calculate()

        self.after(400, self.check_clipboard)



    # Parse F3+C
    def parse_f3c(self, text):
        match = F3C_REGEX.search(text)
        if not match:
            return

        self.dim = match.group(1)
        self.px = float(match.group(2))
        self.py = float(match.group(3))
        self.pz = float(match.group(4))
        self.yaw = float(match.group(5))
        self.pitch = float(match.group(6))

        # Update User
        self.nav_player_info.configure(text="Loaded F3+C!", text_color="green")

        # Update TextBox
        self.nav_textbox_info.configure(state="normal")
        self.nav_textbox_info.delete("1.0", "end")
        self.nav_textbox_info.insert("1.0", f"{self.dim}  x={self.px:.1f}  z={self.pz:.1f}  yaw={self.yaw:.1f}")
        self.nav_textbox_info.configure(state="disabled")



    # Calculation
    def calculate(self):
        if self.target_x is None or self.target_z is None or self.dim is None:
            return

        # dim-based coordinate picking
        if self.dim == "overworld":
            tx, tz = self.target_x, self.target_z
        else:  # nether
            tx, tz = self.target_x / 8, self.target_z / 8

        needed_yaw = compute_yaw_to_target(self.px, self.pz, tx, tz)
        dist = compute_distance(self.px, self.pz, tx, tz)

        yaw_change = needed_yaw - self.yaw
        while yaw_change > 180:
            yaw_change -= 360
        while yaw_change < -180:
            yaw_change += 360

        # Update labels
        self.dist_label.configure(text=f"{dist:.1f} blocks")
        self.req_yaw_label.configure(text=f"{needed_yaw:.1f}°")
        self.turn_label.configure(text=f"{yaw_change:+.1f}°")


if __name__ == "__main__":
    CrayonNavAssist().mainloop()
