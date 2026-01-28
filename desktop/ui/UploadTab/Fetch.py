import customtkinter as ctk
from concurrent.futures import ThreadPoolExecutor

from infra.database import SupabaseDB
from ui.UpdateVisible import UpdateVisible
from services.FetchOps import FetchOps

class Fetch:
    def __init__(self, tab, app):
        self.tab = tab
        self.app = app

        self.supabase = SupabaseDB()
        self.update_visible = UpdateVisible(self, self.tab, self.app)
        self.fetchOps = FetchOps(self, self.tab, self.app)

        self.CARD_WIDTH  = 299
        self.CARD_HEIGHT = 168
        self.CARD_PAD    = 20
        self.COLS = 4

        self.templates_ready = False

        # for lazy loading
        # self.gallery_mode = "None"
        self.template_cards = []

        self.pil_cache = {}
        self.ctk_cache = {}
        self.visible_range = (0, 0)

        self.download_executor = ThreadPoolExecutor(max_workers=10)

    def fetch_templates(self):
        self.fetchOps.fetch_templates()

    def update(self):
        self.app.after(100, self.update_visible.update_fetch)# update_visible)

    # download and show fetched list
    def show_templates(self, filenames):
        self.dragging = False
        self.drag_rect = None
        self.drag_start_x = 0
        self.drag_start_y = 0

        self.gallery_mode = "fetch"

        for widget in self.tab.preview_frame.winfo_children():
            widget.destroy()

        self.template_cards.clear()
        self.templates_ready = False

        for filename in filenames:
            frame = ctk.CTkFrame(
                self.tab.preview_frame,
                width=self.CARD_WIDTH,
                height=self.CARD_HEIGHT,
                corner_radius=12
            )
            frame.grid_propagate(False)

            frame.filename = filename
            frame.selected = False
            frame.loaded   = False
            
            lbl = ctk.CTkLabel(frame, text="Yükleniyor...")
            lbl.pack(expand=True)

            frame.img_label = lbl

            frame.bind("<Button-1>", lambda e, f=frame: self.toggle_select_click(e, f))
            lbl.bind("<Button-1>", lambda e, f=frame: self.toggle_select(f))

            self.template_cards.append(frame)

        self.templates_ready = True
        self.visible_range = (-1,-1)
        self.app.after(100, self.update_visible.update_fetch) # update_visible)

        self.tab.preview_frame.bind("<ButtonPress-1>", self.start_drag)
        self.tab.preview_frame.bind("<B1-Motion>", self.drag_select)
        self.tab.preview_frame.bind("<ButtonRelease-1>", self.end_drag)

    def toggle_select_click(self, event, frame):
        # if dragging ignore click
        if self.dragging:
            return
        self.toggle_select(frame)

    def toggle_select(self, frame):
        frame.selected = not frame.selected
        frame.configure(border_color="#3b82f6" if frame.selected else "#111827", border_width=2)

    # multiple select with drag select
    def start_drag(self, event):
        self.dragging = True

        self.drag_start_x = event.x
        self.drag_start_y = event.y

        if self.drag_rect is not None:
            self.drag_rect.destroy()

        self.drag_rect = ctk.CTkFrame(
            self.tab.preview_frame,
            width=1,
            height=1,
            border_color="#3b82f6",
            border_width=2
        )
        
        self.drag_rect.place(
            x=self.drag_start_x,
            y=self.drag_start_y
        )
        self.drag_rect.configure(width=1, height=1)

    def drag_select(self, event):
        if not self.dragging or self.drag_rect is None:
            return
        
        x1 = self.drag_start_x
        y1 = self.drag_start_y
        x2 = event.x
        y2 = event.y

        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)

        self.drag_rect.place(x=x, y=y)
        self.drag_rect.configure(width=w, height=h)

    def end_drag(self, event):
        if not self.dragging:
            return

        self.dragging = False

        if self.drag_rect is None:
            return

        x1 = self.drag_rect.winfo_x()
        y1 = self.drag_rect.winfo_y()
        x2 = x1 + self.drag_rect.winfo_width()
        y2 = y1 + self.drag_rect.winfo_height()

        self.drag_rect.destroy()
        self.drag_rect = None

        self.select_frames_in_rect(x1, y1, x2, y2)

    def select_frames_in_rect(self, x1, y1, x2, y2):
        for frame in self.template_cards:
            if not frame.winfo_ismapped():
                continue

            fx = frame.winfo_x()
            fy = frame.winfo_y()
            fw = frame.winfo_width()
            fh = frame.winfo_height()

            if(
                fx < x2 and fx + fw > x1 and
                fy < y2 and fy + fh > y1
            ):
                if not frame.selected:
                    self.toggle_select(frame)