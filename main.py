import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw


class LayeredDrawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Layered Map & Drawing App")
        self.root.geometry("900x650")

        # Canvas Dimensions
        self.width = 800
        self.height = 550

        # --- Data Model (The Layers) ---
        # Layer 1: Simulated Map Background data
        self.map_layer_objects = [
            {"type": "grid", "color": "#e0e0e0"},
            {"type": "road", "coords": [100, 400, 700, 400], "color": "#9de291", "width": 20}
        ]
        # Layer 2: User Drawings
        self.drawing_layer_objects = []

        # App States
        self.current_tool = "line"
        self.start_x = None
        self.start_y = None
        self.preview_obj = None

        # --- UI Layout ---
        toolbar = tk.Frame(root, bg="#eaeaea", bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Tools
        tk.Label(toolbar, text="Tools:", bg="#eaeaea").pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Line", command=lambda: self.set_tool("line")).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Rect", command=lambda: self.set_tool("rectangle")).pack(side=tk.LEFT, padx=2)

        # Action Buttons
        tk.Button(toolbar, text="Export Drawing Only", command=self.export_drawing_layer, fg="blue").pack(side=tk.RIGHT,
                                                                                                          padx=5,
                                                                                                          pady=5)
        tk.Button(toolbar, text="Export Merged Map", command=self.export_merged, fg="green").pack(side=tk.RIGHT, padx=5,
                                                                                                  pady=5)

        # Canvas
        self.canvas = tk.Canvas(root, bg="white", width=self.width, height=self.height, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Initial Render
        self.draw_all_layers()

    def set_tool(self, tool):
        self.current_tool = tool

    def draw_all_layers(self):
        """Clears the screen and builds the visual stack from bottom to top."""
        self.canvas.delete("all")

        # 1. Draw Map Background Layer (Bottom)
        for obj in self.map_layer_objects:
            if obj["type"] == "grid":
                for i in range(0, self.width, 40):
                    self.canvas.create_line(i, 0, i, self.height, fill=obj["color"])
                    self.canvas.create_line(0, i, self.width, i, fill=obj["color"])
            elif obj["type"] == "road":
                self.canvas.create_line(*obj["coords"], fill=obj["color"], width=obj["width"])

        # 2. Draw User Vector Layer (Top)
        for obj in self.drawing_layer_objects:
            if obj["type"] == "line":
                self.canvas.create_line(*obj["coords"], fill=obj["color"], width=3)
            elif obj["type"] == "rectangle":
                self.canvas.create_rectangle(*obj["coords"], outline=obj["color"], width=3)

    # --- Mouse Control Handling ---
    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y

    def on_drag(self, event):
        if self.preview_obj:
            self.canvas.delete(self.preview_obj)

        if self.current_tool == "line":
            self.preview_obj = self.canvas.create_line(self.start_x, self.start_y, event.x, event.y, fill="red",
                                                       width=2)
        elif self.current_tool == "rectangle":
            self.preview_obj = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="red",
                                                            width=2)

    def on_release(self, event):
        if self.preview_obj:
            self.canvas.delete(self.preview_obj)

        # Save data structurally to the drawing layer data array
        new_shape = {
            "type": self.current_tool,
            "coords": [self.start_x, self.start_y, event.x, event.y],
            "color": "blue"
        }
        self.drawing_layer_objects.append(new_shape)
        self.draw_all_layers()

    # --- Extraction & Merging Logic ---
    def export_drawing_layer(self):
        """Extracts ONLY the drawing layer as a transparent PNG asset."""
        img = Image.new("RGBA", (self.width, self.height), (255, 255, 255, 0))  # Alpha = 0 (Transparent)
        draw = ImageDraw.Draw(img)

        for obj in self.drawing_layer_objects:
            if obj["type"] == "line":
                draw.line(obj["coords"], fill="blue", width=3)
            elif obj["type"] == "rectangle":
                draw.rectangle(obj["coords"], outline="blue", width=3)

        img.save("extracted_drawing_layer.png")
        messagebox.showinfo("Success", "Exported standalone drawing layer to 'extracted_drawing_layer.png'!")

    def export_merged(self):
        """Bakes both layers down together into one flat JPEG image."""
        img = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(img)

        # 1. Rasterize Map Layer
        for obj in self.map_layer_objects:
            if obj["type"] == "grid":
                for i in range(0, self.width, 40):
                    draw.line([i, 0, i, self.height], fill="#e0e0e0")
                    draw.line([0, i, self.width, i], fill="#e0e0e0")
            elif obj["type"] == "road":
                draw.line(obj["coords"], fill="#9de291", width=20)

        # 2. Rasterize Drawing Layer right over it
        for obj in self.drawing_layer_objects:
            if obj["type"] == "line":
                draw.line(obj["coords"], fill="blue", width=3)
            elif obj["type"] == "rectangle":
                draw.rectangle(obj["coords"], outline="blue", width=3)

        img.save("merged_map_output.jpg")
        messagebox.showinfo("Success", "Exported fully merged composition to 'merged_map_output.jpg'!")


if __name__ == "__main__":
    root = tk.Tk()
    app = LayeredDrawApp(root)
    root.mainloop()