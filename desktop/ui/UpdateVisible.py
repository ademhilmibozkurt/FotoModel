import customtkinter as ctk
from io import BytesIO
from PIL import Image, ImageOps

class UpdateVisible:
    def __init__(self, fetch, tab, app):
        self.fetch = fetch
        self.tab  = tab
        self.app  = app

    def update_visible(self):
        if not self.fetch.templates_ready:
            return
        
        if not self.fetch.gallery_mode:
            self.fetch.gallery_mode = "upload"

        # upload mode -> show everything
        if self.fetch.gallery_mode == "upload":
            for i, frame in enumerate(self.fetch.template_cards):
                if not frame.winfo_exists():continue

                r = i // self.fetch.COLS
                c = i % self.fetch.COLS
                frame.grid(row=r, column=c, padx=15, pady=15, sticky="n")
            return

        # fetch mode -> lazy loading
        start, end = self.get_visible_indices()
        if (start, end) == self.fetch.visible_range:
            return

        self.tab.visible_range = (start, end)

        if self.fetch.gallery_mode == "fetch":
            for i, frame in enumerate(self.fetch.template_cards):
                if not frame.winfo_exists():continue

                r = i // self.fetch.COLS
                c = i % self.fetch.COLS
                frame.grid(row=r, column=c, padx=15, pady=15, sticky="n")

                if start <= i < end and not frame.loaded:
                    self.load_image_async(frame)
                else:
                    pass
        
        self.tab.preview_frame.update_idletasks()
        self.tab.canvas.configure(scrollregion=self.tab.canvas.bbox("all"))

    # calculate visible area
    def get_visible_indices(self):
        y1 = self.tab.canvas.canvasy(0)
        y2 = y1 + self.tab.canvas.winfo_height()

        row_h     = self.fetch.CARD_HEIGHT + self.fetch.CARD_PAD
        start_row = max(0, int(y1 // row_h) - 1)
        end_row   = int(y2 // row_h) + 4

        start = start_row * self.fetch.COLS 
        end   = end_row * self.fetch.COLS 

        return start, min(end, len(self.fetch.template_cards))
    
    # loading images with threading
    def load_image_async(self, frame):
        fn = frame.filename
        # if cache exist attach it
        if fn in self.fetch.ctk_cache:
            self.app.after(0, lambda: self.attach_image(frame))
            return
            
        def worker():
            res = self.supabase.download_templates_fromdb(fn)
            img = Image.open(BytesIO(res))
            img = ImageOps.contain(img, (self.fetch.CARD_WIDTH, self.fetch.CARD_HEIGHT), Image.LANCZOS)

            self.fetch.pil_cache[fn] = img
            self.fetch.ctk_cache[fn] = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=(img.width, img.height)
            )

            self.app.after(0, lambda: self.attach_image(frame))

        self.download_executor.submit(worker)

    # attach image to label
    def attach_image(self, frame):
        if frame.loaded:
            return

        img = self.fetch.ctk_cache.get(frame.filename)
        if not img:
            return

        frame.img_label.destroy()

        lbl       = ctk.CTkLabel(frame, image=img, text="")
        lbl.image = img
        lbl.pack(padx=15, pady=(10,5))

        lbl.bind("<Button-1>", lambda e, f=frame: self.fetch.toggle_select(f))

        frame.loaded = True