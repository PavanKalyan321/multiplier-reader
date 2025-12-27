# Unified GUI for selecting all game regions and button coordinates
import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
from config import RegionConfig, PointConfig, GameConfig, load_game_config, save_game_config
from screen_capture import ScreenCapture


class UnifiedRegionSelector:
    """Unified GUI for selecting balance region, multiplier region, and bet button coordinates"""

    def __init__(self, root):
        self.root = root
        self.root.title("Aviator Bot - Unified Region Configurator")
        self.root.geometry("1400x800")

        # Variables
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        self.screen_image = None
        self.photo_image = None
        self.current_mode = tk.StringVar(value='balance')
        self.selected_point = None

        # Configuration data
        self.config = load_game_config() or GameConfig(
            balance_region=RegionConfig(x1=0, y1=0, x2=0, y2=0),
            multiplier_region=RegionConfig(x1=117, y1=1014, x2=292, y2=1066),
            bet_button_point=PointConfig(x=0, y=0)
        )

        # Region checkmarks
        self.regions_configured = {
            'balance': self.config.balance_region.is_valid(),
            'multiplier': self.config.multiplier_region.is_valid(),
            'bet_button': self.config.bet_button_point.is_valid()
        }

        # Setup UI
        self.setup_ui()
        self.load_screen_preview()

    def setup_ui(self):
        """Setup GUI components"""
        # Top frame with title
        title_frame = tk.Frame(self.root)
        title_frame.pack(pady=10)

        title_label = tk.Label(title_frame, text="Aviator Bot - Unified Region Configurator", font=("Arial", 16, "bold"))
        title_label.pack()

        # Mode selection frame
        mode_frame = tk.LabelFrame(self.root, text="Select Configuration Mode", padx=10, pady=10)
        mode_frame.pack(fill=tk.X, padx=10, pady=5)

        modes = [
            ('Balance Region', 'balance', 'Select balance amount region'),
            ('Multiplier Region', 'multiplier', 'Select multiplier display region'),
            ('Bet Button', 'bet_button', 'Select bet/cashout button location')
        ]

        for label, value, tooltip in modes:
            rb = tk.Radiobutton(
                mode_frame,
                text=label,
                variable=self.current_mode,
                value=value,
                font=("Arial", 11)
            )
            rb.pack(side=tk.LEFT, padx=10)

            # Add checkmark indicator
            check_frame = tk.Frame(mode_frame)
            check_frame.pack(side=tk.LEFT, padx=5)

            self.status_labels = getattr(self, 'status_labels', {})
            self.status_labels[value] = tk.Label(check_frame, text='○', font=("Arial", 14), fg='red')
            self.status_labels[value].pack()

            self.update_status_label(value)

        # Canvas for image
        canvas_frame = tk.LabelFrame(self.root, text="Screen Preview (Click and drag to select region, or click to set point)", padx=5, pady=5)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg="gray", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Info label
        info_frame = tk.Frame(self.root)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.info_label = tk.Label(info_frame, text="", font=("Arial", 10), justify=tk.LEFT)
        self.info_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Button frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        save_btn = tk.Button(button_frame, text="Save All Regions", command=self.save_all, bg="green", fg="white", padx=15, font=("Arial", 10))
        save_btn.pack(side=tk.LEFT, padx=5)

        load_btn = tk.Button(button_frame, text="Load Config", command=self.load_config, bg="blue", fg="white", padx=15, font=("Arial", 10))
        load_btn.pack(side=tk.LEFT, padx=5)

        test_btn = tk.Button(button_frame, text="Test Selected", command=self.test_region, bg="orange", fg="white", padx=15, font=("Arial", 10))
        test_btn.pack(side=tk.LEFT, padx=5)

        reset_btn = tk.Button(button_frame, text="Reset Current", command=self.reset_selection, bg="red", fg="white", padx=15, font=("Arial", 10))
        reset_btn.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(button_frame, text="Close", command=self.root.quit, bg="gray", fg="white", padx=15, font=("Arial", 10))
        close_btn.pack(side=tk.LEFT, padx=5)

    def load_screen_preview(self):
        """Load and display screen preview"""
        screen_capture = ScreenCapture()
        self.screen_image = screen_capture.capture_full_screen()

        # Convert to RGB for display
        rgb_image = cv2.cvtColor(self.screen_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        # Resize for display if needed
        display_width = 1350
        aspect = pil_image.height / pil_image.width
        display_height = int(display_width * aspect)
        pil_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)

        self.photo_image = ImageTk.PhotoImage(pil_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

        # Store scale factors
        self.scale_x = self.screen_image.shape[1] / display_width
        self.scale_y = self.screen_image.shape[0] / display_height

        # Draw existing regions
        self.draw_existing_regions()

    def draw_existing_regions(self):
        """Draw all configured regions on canvas"""
        self.canvas.delete("existing_regions")

        # Draw balance region if configured
        if self.config.balance_region.is_valid():
            x1 = int(self.config.balance_region.x1 / self.scale_x)
            y1 = int(self.config.balance_region.y1 / self.scale_y)
            x2 = int(self.config.balance_region.x2 / self.scale_x)
            y2 = int(self.config.balance_region.y2 / self.scale_y)

            self.canvas.create_rectangle(x1, y1, x2, y2, outline="blue", width=2, tags="existing_regions")
            self.canvas.create_text(x1 + 5, y1 + 5, text="BALANCE", fill="blue", anchor=tk.NW, font=("Arial", 8), tags="existing_regions")

        # Draw multiplier region if configured
        if self.config.multiplier_region.is_valid():
            x1 = int(self.config.multiplier_region.x1 / self.scale_x)
            y1 = int(self.config.multiplier_region.y1 / self.scale_y)
            x2 = int(self.config.multiplier_region.x2 / self.scale_x)
            y2 = int(self.config.multiplier_region.y2 / self.scale_y)

            self.canvas.create_rectangle(x1, y1, x2, y2, outline="green", width=2, tags="existing_regions")
            self.canvas.create_text(x1 + 5, y1 + 5, text="MULT", fill="green", anchor=tk.NW, font=("Arial", 8), tags="existing_regions")

        # Draw bet button if configured
        if self.config.bet_button_point.is_valid():
            x = int(self.config.bet_button_point.x / self.scale_x)
            y = int(self.config.bet_button_point.y / self.scale_y)
            size = 10

            # Draw crosshair
            self.canvas.create_line(x - size, y, x + size, y, fill="red", width=2, tags="existing_regions")
            self.canvas.create_line(x, y - size, x, y + size, fill="red", width=2, tags="existing_regions")
            self.canvas.create_text(x + 15, y + 5, text="BET", fill="red", anchor=tk.NW, font=("Arial", 8), tags="existing_regions")

    def on_canvas_click(self, event):
        """Handle canvas click"""
        mode = self.current_mode.get()

        if mode == 'bet_button':
            # Point mode - single click to set point
            self.selected_point = (int(event.x * self.scale_x), int(event.y * self.scale_y))
            self.config.bet_button_point = PointConfig(x=self.selected_point[0], y=self.selected_point[1])
            self.regions_configured['bet_button'] = True
            self.draw_existing_regions()
            self.update_status_label('bet_button')
            self.update_info_label()
        else:
            # Rectangle mode - start selection
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

        # Update configuration
        if self.selection_start and self.selection_end:
            self.update_config_from_selection()

    def draw_selection_rectangle(self):
        """Draw selection rectangle on canvas"""
        self.canvas.delete("selection_rect")
        self.draw_existing_regions()

        if self.selection_start and self.selection_end:
            self.canvas.create_rectangle(
                self.selection_start[0],
                self.selection_start[1],
                self.selection_end[0],
                self.selection_end[1],
                outline="yellow",
                width=2,
                tags="selection_rect"
            )

    def update_config_from_selection(self):
        """Update configuration based on current selection"""
        if not self.selection_start or not self.selection_end:
            return

        x1 = int(self.selection_start[0] * self.scale_x)
        y1 = int(self.selection_start[1] * self.scale_y)
        x2 = int(self.selection_end[0] * self.scale_x)
        y2 = int(self.selection_end[1] * self.scale_y)

        # Normalize coordinates
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        # Check minimum size
        if abs(x2 - x1) < 20 or abs(y2 - y1) < 20:
            messagebox.showwarning("Warning", "Region too small. Minimum size: 20x20 pixels")
            return

        mode = self.current_mode.get()
        region = RegionConfig(x1=x1, y1=y1, x2=x2, y2=y2)

        if mode == 'balance':
            self.config.balance_region = region
            self.regions_configured['balance'] = True
        elif mode == 'multiplier':
            self.config.multiplier_region = region
            self.regions_configured['multiplier'] = True

        self.update_status_label(mode)
        self.update_info_label()

    def update_status_label(self, mode):
        """Update status indicator for a mode"""
        is_configured = self.regions_configured.get(mode, False)
        status = '✓' if is_configured else '○'
        color = 'green' if is_configured else 'red'

        if hasattr(self, 'status_labels') and mode in self.status_labels:
            self.status_labels[mode].config(text=status, fg=color)

    def update_info_label(self):
        """Update info label with current configuration"""
        mode = self.current_mode.get()
        info_text = "Configuration Status:\n"

        if mode == 'balance':
            config = self.config.balance_region
            info_text += f"Balance: ({config.x1}, {config.y1}) to ({config.x2}, {config.y2})"
            if config.is_valid():
                info_text += f" | Size: {config.x2 - config.x1}x{config.y2 - config.y1}"
        elif mode == 'multiplier':
            config = self.config.multiplier_region
            info_text += f"Multiplier: ({config.x1}, {config.y1}) to ({config.x2}, {config.y2})"
            if config.is_valid():
                info_text += f" | Size: {config.x2 - config.x1}x{config.y2 - config.y1}"
        elif mode == 'bet_button':
            config = self.config.bet_button_point
            info_text += f"Bet Button: ({config.x}, {config.y})"

        self.info_label.config(text=info_text)

    def save_all(self):
        """Save all configurations"""
        if not self.config.balance_region.is_valid():
            messagebox.showerror("Error", "Balance region not configured")
            return

        if not self.config.multiplier_region.is_valid():
            messagebox.showerror("Error", "Multiplier region not configured")
            return

        if not self.config.bet_button_point.is_valid():
            messagebox.showerror("Error", "Bet button not configured")
            return

        if save_game_config(self.config):
            messagebox.showinfo("Success", f"""
Configuration saved successfully!

Balance Region: ({self.config.balance_region.x1}, {self.config.balance_region.y1}) to ({self.config.balance_region.x2}, {self.config.balance_region.y2})
Multiplier Region: ({self.config.multiplier_region.x1}, {self.config.multiplier_region.y1}) to ({self.config.multiplier_region.x2}, {self.config.multiplier_region.y2})
Bet Button: ({self.config.bet_button_point.x}, {self.config.bet_button_point.y})
            """)
        else:
            messagebox.showerror("Error", "Failed to save configuration")

    def load_config(self):
        """Load configuration from file"""
        loaded_config = load_game_config()
        if loaded_config:
            self.config = loaded_config
            self.regions_configured = {
                'balance': self.config.balance_region.is_valid(),
                'multiplier': self.config.multiplier_region.is_valid(),
                'bet_button': self.config.bet_button_point.is_valid()
            }
            self.draw_existing_regions()

            for mode in ['balance', 'multiplier', 'bet_button']:
                self.update_status_label(mode)

            messagebox.showinfo("Success", "Configuration loaded successfully")
        else:
            messagebox.showerror("Error", "No saved configuration found")

    def test_region(self):
        """Test the selected region"""
        mode = self.current_mode.get()

        try:
            screen_capture = ScreenCapture()

            if mode == 'balance':
                if not self.config.balance_region.is_valid():
                    messagebox.showerror("Error", "Balance region not configured")
                    return
                screen_capture.region = self.config.balance_region
                filename = "test_balance.png"
            elif mode == 'multiplier':
                if not self.config.multiplier_region.is_valid():
                    messagebox.showerror("Error", "Multiplier region not configured")
                    return
                screen_capture.region = self.config.multiplier_region
                filename = "test_multiplier.png"
            elif mode == 'bet_button':
                if not self.config.bet_button_point.is_valid():
                    messagebox.showerror("Error", "Bet button not configured")
                    return
                messagebox.showinfo("Info", f"Bet button configured at ({self.config.bet_button_point.x}, {self.config.bet_button_point.y})")
                return

            region_frame = screen_capture.capture_region()
            cv2.imwrite(filename, region_frame)
            messagebox.showinfo("Success", f"Region captured and saved as '{filename}'")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture region: {e}")

    def reset_selection(self):
        """Reset current selection"""
        mode = self.current_mode.get()

        if mode == 'balance':
            self.config.balance_region = RegionConfig(x1=0, y1=0, x2=0, y2=0)
            self.regions_configured['balance'] = False
        elif mode == 'multiplier':
            self.config.multiplier_region = RegionConfig(x1=0, y1=0, x2=0, y2=0)
            self.regions_configured['multiplier'] = False
        elif mode == 'bet_button':
            self.config.bet_button_point = PointConfig(x=0, y=0)
            self.regions_configured['bet_button'] = False

        self.selection_start = None
        self.selection_end = None
        self.selected_point = None
        self.draw_existing_regions()
        self.update_status_label(mode)
        self.update_info_label()


def run_unified_gui():
    """Run the unified region selector GUI"""
    root = tk.Tk()
    app = UnifiedRegionSelector(root)
    root.mainloop()


if __name__ == "__main__":
    run_unified_gui()
