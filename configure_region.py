#!/usr/bin/env python
"""Interactive region configuration tool for multiplier reader"""

import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab, ImageTk
import json
from config import save_config, RegionConfig, load_config

class RegionSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multiplier Reader - Region Configuration")

        # Try to load existing config
        existing_config = load_config()

        # Take screenshot
        self.screenshot = ImageGrab.grab()
        self.width, self.height = self.screenshot.size

        # Scale down for display if too large
        max_display_width = 1200
        max_display_height = 800
        scale_factor = min(max_display_width / self.width, max_display_height / self.height, 1.0)

        display_width = int(self.width * scale_factor)
        display_height = int(self.height * scale_factor)

        self.scale_factor = scale_factor
        self.display_image = self.screenshot.resize((display_width, display_height))

        # Create canvas
        self.canvas = tk.Canvas(self.root, width=display_width, height=display_height)
        self.canvas.pack()

        # Display screenshot
        self.photo = ImageTk.PhotoImage(self.display_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # Selection rectangle
        self.rect = None
        self.start_x = None
        self.start_y = None

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Instructions
        instruction_text = "Click and drag to select the multiplier region"
        if existing_config:
            instruction_text += f"\n\nCurrent region: ({existing_config.x1}, {existing_config.y1}) to ({existing_config.x2}, {existing_config.y2})"

        self.info_label = tk.Label(self.root, text=instruction_text, pady=10)
        self.info_label.pack()

        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.save_button = tk.Button(button_frame, text="Save Configuration", command=self.save_config, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = tk.Button(button_frame, text="Cancel", command=self.root.quit)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Draw existing region if available
        if existing_config:
            self.draw_existing_region(existing_config)

        self.selected_region = None

    def draw_existing_region(self, config):
        """Draw the existing configured region"""
        x1 = int(config.x1 * self.scale_factor)
        y1 = int(config.y1 * self.scale_factor)
        x2 = int(config.x2 * self.scale_factor)
        y2 = int(config.y2 * self.scale_factor)

        self.canvas.create_rectangle(x1, y1, x2, y2, outline="yellow", width=2, dash=(5, 5))
        self.canvas.create_text((x1 + x2) // 2, y1 - 10, text="Current Region", fill="yellow")

    def on_press(self, event):
        """Mouse button pressed"""
        self.start_x = event.x
        self.start_y = event.y

        if self.rect:
            self.canvas.delete(self.rect)

        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )

    def on_drag(self, event):
        """Mouse dragged"""
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        """Mouse button released"""
        if self.start_x is not None:
            # Get coordinates (convert from display to actual screen coordinates)
            x1 = int(min(self.start_x, event.x) / self.scale_factor)
            y1 = int(min(self.start_y, event.y) / self.scale_factor)
            x2 = int(max(self.start_x, event.x) / self.scale_factor)
            y2 = int(max(self.start_y, event.y) / self.scale_factor)

            # Ensure minimum size
            if abs(x2 - x1) < 50 or abs(y2 - y1) < 30:
                messagebox.showwarning("Region Too Small", "Please select a larger region (minimum 50x30 pixels)")
                return

            self.selected_region = RegionConfig(x1=x1, y1=y1, x2=x2, y2=y2)

            # Update info label
            self.info_label.config(
                text=f"Selected region: ({x1}, {y1}) to ({x2}, {y2})\n"
                     f"Size: {x2-x1}x{y2-y1} pixels\n"
                     f"Click 'Save Configuration' to apply"
            )

            self.save_button.config(state=tk.NORMAL)

    def save_config(self):
        """Save the selected region"""
        if self.selected_region:
            save_config(self.selected_region)
            messagebox.showinfo("Success",
                f"Configuration saved!\n\n"
                f"Region: ({self.selected_region.x1}, {self.selected_region.y1}) to "
                f"({self.selected_region.x2}, {self.selected_region.y2})\n\n"
                f"You can now run main.py to start monitoring."
            )
            self.root.quit()

    def run(self):
        """Start the GUI"""
        self.root.mainloop()

def main():
    print("=" * 80)
    print("MULTIPLIER READER - REGION CONFIGURATION")
    print("=" * 80)
    print()
    print("Instructions:")
    print("1. A screenshot of your screen will be displayed")
    print("2. Click and drag to select the region where the multiplier appears")
    print("3. The region should include the multiplier text (e.g., '2.45x')")
    print("4. Click 'Save Configuration' when you're satisfied with the selection")
    print()
    print("Starting configuration tool...")
    print()

    try:
        app = RegionSelector()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have the required dependencies:")
        print("  pip install pillow")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
