import tkinter as tk
from tkinter import filedialog, colorchooser, ttk, messagebox
import csv
from PIL import Image, ImageDraw


class DotGridApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Dot Grid Generator")

        # Internal data: 10x20 empty grid by default
        self.data = [[0 for _ in range(20)] for _ in range(10)]

        # Config state
        self.dot_radius = tk.DoubleVar(value=6.0)
        self.spacing = tk.DoubleVar(value=18.0)

        self.bg_color = "#111111"
        self.inactive_color = "#555555"
        self.active_color = "#00ff55"

        # Export format
        self.export_format = tk.StringVar(value="PNG")  # PNG, JPEG, SVG

        self._build_ui()
        self.draw_grid()

    # ---------- UI LAYOUT ----------

    def _build_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: controls
        controls = ttk.Frame(main)
        controls.pack(side="left", fill="y")

        # File controls
        file_frame = ttk.LabelFrame(controls, text="Data")
        file_frame.pack(fill="x", pady=(0, 10))

        load_btn = ttk.Button(file_frame, text="Load CSV…", command=self.load_csv)
        load_btn.pack(fill="x", pady=5)

        reset_btn = ttk.Button(file_frame, text="Reset Grid", command=self.reset_grid)
        reset_btn.pack(fill="x", pady=5)

        # Dot controls
        dot_frame = ttk.LabelFrame(controls, text="Dots")
        dot_frame.pack(fill="x", pady=(0, 10))

        # Dot radius
        ttk.Label(dot_frame, text="Radius").pack(anchor="w")
        radius_scale = ttk.Scale(
            dot_frame,
            from_=2.0,
            to=30.0,
            variable=self.dot_radius,
            command=lambda _v: self.draw_grid(),
        )
        radius_scale.pack(fill="x", padx=2, pady=(0, 6))

        # Spacing
        ttk.Label(dot_frame, text="Spacing").pack(anchor="w")
        spacing_scale = ttk.Scale(
            dot_frame,
            from_=8.0,
            to=60.0,
            variable=self.spacing,
            command=lambda _v: self.draw_grid(),
        )
        spacing_scale.pack(fill="x", padx=2, pady=(0, 6))

        # Color controls
        color_frame = ttk.LabelFrame(controls, text="Colors")
        color_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(
            color_frame,
            text="Background…",
            command=lambda: self.pick_color("bg"),
        ).pack(fill="x", pady=2)

        ttk.Button(
            color_frame,
            text="Inactive dot…",
            command=lambda: self.pick_color("inactive"),
        ).pack(fill="x", pady=2)

        ttk.Button(
            color_frame,
            text="Active dot…",
            command=lambda: self.pick_color("active"),
        ).pack(fill="x", pady=2)

        # Export controls
        export_frame = ttk.LabelFrame(controls, text="Export")
        export_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(export_frame, text="Format").pack(anchor="w")
        format_box = ttk.Combobox(
            export_frame,
            textvariable=self.export_format,
            values=["PNG", "JPEG", "SVG"],
            state="readonly",
        )
        format_box.pack(fill="x", pady=(0, 6))

        export_btn = ttk.Button(export_frame, text="Export Image…", command=self.export_image)
        export_btn.pack(fill="x")

        # Right: canvas preview
        canvas_frame = ttk.Frame(main)
        canvas_frame.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=self.bg_color)
        self.canvas.pack(fill="both", expand=True)

    # ---------- DATA / CSV ----------

    def reset_grid(self):
        self.data = [[0 for _ in range(20)] for _ in range(10)]
        self.draw_grid()

    def load_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, newline="") as f:
                reader = csv.reader(f)
                rows = [row for row in reader]

            # Remove completely empty rows
            rows = [r for r in rows if any(cell.strip() for cell in r)]
            if not rows:
                messagebox.showerror("Error", "CSV file appears to be empty.")
                return

            max_cols = max(len(r) for r in rows)
            data = []

            for r in rows:
                # Pad short rows
                row = list(r) + [""] * (max_cols - len(r))
                row_vals = []
                for cell in row:
                    cell_str = cell.strip()
                    # Treat any non-empty and non-zero cell as "active"
                    if cell_str and cell_str != "0":
                        row_vals.append(1)
                    else:
                        row_vals.append(0)
                data.append(row_vals)

            self.data = data
            self.draw_grid()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read CSV:\n{e}")

    # ---------- COLORS ----------

    def pick_color(self, kind: str):
        initial = {
            "bg": self.bg_color,
            "inactive": self.inactive_color,
            "active": self.active_color,
        }[kind]

        color, _ = colorchooser.askcolor(color=initial, parent=self.root)
        if not color:
            return

        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(color[0]), int(color[1]), int(color[2])
        )

        if kind == "bg":
            self.bg_color = hex_color
        elif kind == "inactive":
            self.inactive_color = hex_color
        elif kind == "active":
            self.active_color = hex_color

        self.draw_grid()

    # ---------- DRAWING / SIZE HELPERS ----------

    def _grid_dimensions(self):
        if not self.data:
            return 0, 0, 0.0, 0.0
        rows = len(self.data)
        cols = len(self.data[0])
        r = float(self.dot_radius.get())
        spacing = float(self.spacing.get())
        width = int(cols * spacing + spacing)
        height = int(rows * spacing + spacing)
        return rows, cols, width, height

    def draw_grid(self):
        self.canvas.delete("all")

        rows, cols, width, height = self._grid_dimensions()
        if rows == 0 or cols == 0:
            return

        r = float(self.dot_radius.get())
        spacing = float(self.spacing.get())

        # Resize canvas to fit grid
        self.canvas.config(width=width, height=height, bg=self.bg_color)

        for i in range(rows):
            for j in range(cols):
                cx = spacing / 2 + j * spacing
                cy = spacing / 2 + i * spacing

                color = self.active_color if self.data[i][j] else self.inactive_color
                self.canvas.create_oval(
                    cx - r, cy - r, cx + r, cy + r, fill=color, outline=""
                )

    # ---------- EXPORT ----------

    def export_image(self):
        if not self.data:
            messagebox.showerror("Error", "No data to export.")
            return

        rows, cols, width, height = self._grid_dimensions()
        if rows == 0 or cols == 0:
            messagebox.showerror("Error", "No data to export.")
            return

        fmt = self.export_format.get().upper()

        # Suggest extension based on format
        def_ext = ".png" if fmt == "PNG" else ".jpg" if fmt == "JPEG" else ".svg"

        path = filedialog.asksaveasfilename(
            defaultextension=def_ext,
            filetypes=[
                ("PNG image", "*.png"),
                ("JPEG image", "*.jpg;*.jpeg"),
                ("SVG vector", "*.svg"),
                ("All files", "*.*"),
            ],
            title="Save image",
        )
        if not path:
            return

        # Normalize extension to match chosen format
        if fmt == "PNG" and not path.lower().endswith(".png"):
            path += ".png"
        elif fmt == "JPEG" and not (path.lower().endswith(".jpg") or path.lower().endswith(".jpeg")):
            path += ".jpg"
        elif fmt == "SVG" and not path.lower().endswith(".svg"):
            path += ".svg"

        try:
            if fmt in ("PNG", "JPEG"):
                self._export_raster(path, fmt, width, height)
            elif fmt == "SVG":
                self._export_svg(path, width, height)
            messagebox.showinfo("Saved", f"Image saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image:\n{e}")

    def _export_raster(self, path: str, fmt: str, width: int, height: int):
        """
        PNG / JPEG export using Pillow.
        """
        rows = len(self.data)
        cols = len(self.data[0])
        r = float(self.dot_radius.get())
        spacing = float(self.spacing.get())

        img = Image.new("RGB", (width, height), self.bg_color)
        draw = ImageDraw.Draw(img)

        for i in range(rows):
            for j in range(cols):
                cx = spacing / 2 + j * spacing
                cy = spacing / 2 + i * spacing
                color = self.active_color if self.data[i][j] else self.inactive_color
                draw.ellipse(
                    (cx - r, cy - r, cx + r, cy + r),
                    fill=color,
                    outline=None,
                )

        # fmt is "PNG" or "JPEG"
        img.save(path, format=fmt)

    def _export_svg(self, path: str, width: int, height: int):
        """
        SVG export: write <circle> elements to a .svg file.
        """
        rows = len(self.data)
        cols = len(self.data[0])
        r = float(self.dot_radius.get())
        spacing = float(self.spacing.get())

        # Basic SVG header
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'<rect width="100%" height="100%" fill="{self.bg_color}" />',
        ]

        for i in range(rows):
            for j in range(cols):
                cx = spacing / 2 + j * spacing
                cy = spacing / 2 + i * spacing
                color = self.active_color if self.data[i][j] else self.inactive_color
                parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" />'
                )

        parts.append("</svg>")
        svg_str = "\n".join(parts)

        with open(path, "w", encoding="utf-8") as f:
            f.write(svg_str)


if __name__ == "__main__":
    root = tk.Tk()
    app = DotGridApp(root)
    root.mainloop()
