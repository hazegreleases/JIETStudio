import tkinter as tk
import tkinter.font as tkfont
from app.core.theme_manager import ThemeManager

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=120, height=40, corner_radius=10, 
                 bg_color=None, hover_color=None, click_color=None, text_color=None, font=None):
        try:
            parent_bg = parent["bg"]
        except:
            # Fallback for ttk widgets
            parent_bg = ThemeManager().get("window_bg_color")

        super().__init__(parent, width=width, height=height, bg=parent_bg, highlightthickness=0)
        
        self.theme = ThemeManager()
        
        self.command = command
        self.text = text
        self.bg_color = bg_color if bg_color else self.theme.get("button_bg_color")
        self.hover_color = hover_color if hover_color else self.theme.get("button_hover_color")
        self.click_color = click_color if click_color else self.theme.get("button_click_color")
        self.text_color = text_color if text_color else self.theme.get("button_text_color")
        self.corner_radius = corner_radius
        
        font_family = self.theme.get("font_family")
        font_size = int(self.theme.get("font_size_normal"))
        self.font = font if font else (font_family, font_size)
        
        self.current_color = self.bg_color
        
        self._draw()
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)

    def _draw(self):
        self.delete("all")
        
        # Draw rounded rectangle
        # A simple way to draw a rounded rect in canvas is using a polygon or arcs+rects
        # Here is a helper to draw it using arcs and rectangles
        
        r = self.corner_radius
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        
        # If widget is not mapped yet, use requested size
        if w <= 1: w = int(self["width"])
        if h <= 1: h = int(self["height"])

        self.create_arc((0, 0, 2*r, 2*r), start=90, extent=90, fill=self.current_color, outline=self.current_color)
        self.create_arc((w-2*r, 0, w, 2*r), start=0, extent=90, fill=self.current_color, outline=self.current_color)
        self.create_arc((w-2*r, h-2*r, w, h), start=270, extent=90, fill=self.current_color, outline=self.current_color)
        self.create_arc((0, h-2*r, 2*r, h), start=180, extent=90, fill=self.current_color, outline=self.current_color)
        
        self.create_rectangle((r, 0, w-r, h), fill=self.current_color, outline=self.current_color)
        self.create_rectangle((0, r, w, h-r), fill=self.current_color, outline=self.current_color)
        
        self.create_text(w/2, h/2, text=self.text, fill=self.text_color, font=self.font)

    def on_enter(self, event):
        self.current_color = self.hover_color
        self._draw()

    def on_leave(self, event):
        self.current_color = self.bg_color
        self._draw()

    def on_click(self, event):
        self.current_color = self.click_color
        self._draw()

    def on_release(self, event):
        self.current_color = self.hover_color # Return to hover state
        self._draw()
        if self.command:
            # Only fire command if mouse is still within the button bounds
            w = int(self["width"])
            h = int(self["height"])
            if 0 <= event.x <= w and 0 <= event.y <= h:
                self.command()
