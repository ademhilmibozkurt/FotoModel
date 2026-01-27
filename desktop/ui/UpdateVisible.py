import customtkinter as ctk
from io import BytesIO
from PIL import Image, ImageOps

class UpdateVisible:
    def __init__(self, tab):
        self.tab = tab

    def update_visible(self):
        if not self.tab.templates_ready:
            return
        
        if not self.tab.gallery_mode:
            self.tab.gallery_mode = "upload"

        # upload mode -> show everything
        if self.tab.gallery_mode == "upload":
            for i, frame in enumerate(self.tab.template_cards):
                if not frame.winfo_exists():continue

                r = i // self.COLS
                c = i % self.COLS
                frame.grid(row=r, column=c, padx=15, pady=15, sticky="n")
            return

        # fetch mode -> lazy loading
        start, end = self.get_visible_indices()
        if (start, end) == self.tab.visible_range:
            return

        self.tab.visible_range = (start, end)

        if self.tab.gallery_mode == "fetch":
            for i, frame in enumerate(self.tab.template_cards):
                if not frame.winfo_exists():continue

                r = i // self.COLS
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

        row_h     = self.CARD_HEIGHT + self.CARD_PAD
        start_row = max(0, int(y1 // row_h) - 1)
        end_row   = int(y2 // row_h) + 4

        start = start_row * self.COLS 
        end   = end_row * self.COLS 

        return start, min(end, len(self.tab.template_cards))
    
    # loading images with threading
    def load_image_async(self, frame):
        fn = frame.filename
        # if cache exist attach it
        if fn in self.tab.ctk_cache:
            self.app.after(0, lambda: self.attach_image(frame))
            return
            
        def worker():
            res = self.supabase.download_templates_fromdb(fn)
            img = Image.open(BytesIO(res))
            img = ImageOps.contain(img, (self.CARD_WIDTH, self.CARD_HEIGHT), Image.LANCZOS)

            self.tab.pil_cache[fn] = img
            self.tab.ctk_cache[fn] = ctk.CTkImage(
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

        img = self.tab.ctk_cache.get(frame.filename)
        if not img:
            return

        frame.img_label.destroy()

        lbl       = ctk.CTkLabel(frame, image=img, text="")
        lbl.image = img
        lbl.pack(padx=15, pady=(10,5))

        lbl.bind("<Button-1>", lambda e, f=frame: self.tab.toggle_select(f))

        frame.loaded = True