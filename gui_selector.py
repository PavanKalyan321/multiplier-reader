# Frontend GUI for region selection
import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import threading
from config import RegionConfig, save_config, load_config
from screen_capture import ScreenCapture

class RegionSelector:
    """GUI for selecting multiplier region on screen"""

    def __init__(self, root):
        self.root = root
        self.root.title("Multiplier Reader - Region Selector")
        self.root.geometry("1200x700")

        # Variables
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        self.screen_image = None
        self.photo_image = None

        # Setup UI
        self.setup_ui()
        self.load_screen_preview()

    def setup_ui(self):
        """Setup GUI components"""
        # Title
        title_label = tk.Label(self.root, text="Select Multiplier Region", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Canvas for image
        self.canvas = tk.Canvas(self.root, bg="gray", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Instructions
        instructions = tk.Label(
            self.root,
            text="Click and drag to select the multiplier region (top-left to bottom-right). Press 'Save' when done.",
            font=("Arial", 10)
        )
        instructions.pack(pady=5)

        # Button frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        save_btn = tk.Button(button_frame, text="Save Region", command=self.save_region, bg="green", fg="white", padx=10)
        save_btn.pack(side=tk.LEFT, padx=5)

        load_btn = tk.Button(button_frame, text="Load Last Config", command=self.load_last_config, bg="blue", fg="white", padx=10)
        load_btn.pack(side=tk.LEFT, padx=5)

        test_btn = tk.Button(button_frame, text="Test Region", command=self.test_region, bg="orange", fg="white", padx=10)
        test_btn.pack(side=tk.LEFT, padx=5)

        reset_btn = tk.Button(button_frame, text="Reset", command=self.reset_selection, bg="red", fg="white", padx=10)
        reset_btn.pack(side=tk.LEFT, padx=5)

        # Info label
        self.info_label = tk.Label(self.root, text="", font=("Arial", 10))
        self.info_label.pack(pady=5)

    def load_screen_preview(self):
        """Load and display screen preview"""
        screen_capture = ScreenCapture()
        self.screen_image = screen_capture.capture_full_screen()

        # Convert to RGB for display
        rgb_image = cv2.cvtColor(self.screen_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        # Resize for display if needed
        display_width = 1180
        aspect = pil_image.height / pil_image.width
        display_height = int(display_width * aspect)
        pil_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)

        self.photo_image = ImageTk.PhotoImage(pil_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

        # Store scale factors
        self.scale_x = self.screen_image.shape[1] / display_width
        self.scale_y = self.screen_image.shape[0] / display_height

    def on_canvas_click(self, event):
        """Handle canvas click"""
        self.selection_start = (event.x, event.y)
        self.is_selecting = True
        self.selection_end = None

    def on_canvas_drag(self, event):
        """Handle canvas drag"""
        if self.is_selecting:
            self.selection_end = (event.x, event.y)
            self.draw_selection_rectangle()

    def on_canvas_release(self, event):
        """Handle canvas release"""
        self.selection_end = (event.x, event.y)
        self.is_selecting = False
        self.draw_selection_rectangle()

    def draw_selection_rectangle(self):
        """Draw selection rectangle on canvas"""
        self.canvas.delete("selection_rect")

        if self.selection_start and self.selection_end:
            self.canvas.create_rectangle(
                self.selection_start[0],
                self.selection_start[1],
                self.selection_end[0],
                self.selection_end[1],
                outline="red",
                width=2,
                tags="selection_rect"
            )

            # Update info
            x1 = int(self.selection_start[0] * self.scale_x)
            y1 = int(self.selection_start[1] * self.scale_y)
            x2 = int(self.selection_end[0] * self.scale_x)
            y2 = int(self.selection_end[1] * self.scale_y)

            # Normalize coordinates
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1

            width = x2 - x1
            height = y2 - y1
            self.info_label.config(text=f"Region: ({x1}, {y1}) to ({x2}, {y2}) | Size: {width}x{height}")
            self.current_region = RegionConfig(x1=x1, y1=y1, x2=x2, y2=y2)

    def save_region(self):
        """Save selected region"""
        if not hasattr(self, 'current_region') or not self.current_region.is_valid():
            messagebox.showerror("Error", "Please select a valid region first")
            return

        save_config(self.current_region)
        messagebox.showinfo("Success", f"Region saved: {self.current_region}")

    def load_last_config(self):
        """Load last saved configuration"""
        config = load_config()
        if config:
            self.current_region = config
            # Update canvas display (rough estimate)
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:
                display_x1 = int(config.x1 / self.scale_x)
                display_y1 = int(config.y1 / self.scale_y)
                display_x2 = int(config.x2 / self.scale_x)
                display_y2 = int(config.y2 / self.scale_y)

                self.selection_start = (display_x1, display_y1)
                self.selection_end = (display_x2, display_y2)
                self.draw_selection_rectangle()

            messagebox.showinfo("Success", f"Loaded config: {config}")
        else:
            messagebox.showerror("Error", "No saved configuration found")

    def test_region(self):
        """Test the selected region"""
        if not hasattr(self, 'current_region') or not self.current_region.is_valid():
            messagebox.showerror("Error", "Please select a valid region first")
            return

        # Capture and display the selected region
        screen_capture = ScreenCapture(self.current_region)
        try:
            region_frame = screen_capture.capture_region()
            cv2.imwrite("test_region.png", region_frame)
            messagebox.showinfo("Success", "Region captured and saved as 'test_region.png'")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture region: {e}")

    def reset_selection(self):
        """Reset selection"""
        self.selection_start = None
        self.selection_end = None
        self.canvas.delete("selection_rect")
        self.info_label.config(text="")

def run_gui():
    """Run the GUI selector"""
    root = tk.Tk()
    app = RegionSelector(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
