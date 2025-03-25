import customtkinter as ctk
from datetime import datetime, timedelta

class EPG(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="gray20")
        self.transparency = 0.8
        self.channels = []
        self.play_callback = None 
        
        self.header = ctk.CTkLabel(self, text="Electronic Program Guide", font=("Arial", 16, "bold"))
        self.header.pack(pady=10)
        
        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="gray15")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.epg_data = {}
    
    def load_epg_data(self, channels):
        """Lädt EPG-Daten aus den übergebenen Kanälen (simuliert hier)"""
        self.channels = channels
        self.epg_data = {}
        for channel in self.channels:
            tvg_name = channel['tvg_id']
            self.epg_data[tvg_name] = [
                {"title": f"News at {datetime.now().hour}:00", "start": datetime.now(), "end": datetime.now() + timedelta(hours=1)},
                {"title": "Movie: The Great Adventure", "start": datetime.now() + timedelta(hours=1), "end": datetime.now() + timedelta(hours=3)},
                {"title": "Talk Show", "start": datetime.now() + timedelta(hours=3), "end": datetime.now() + timedelta(hours=4)}
            ]
        self.create_epg_display()
    
    def create_epg_display(self):
        """Erstellt die EPG-Anzeige: Es werden nur klickbare Buttons mit dem tvg-Namen angezeigt."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        for index, channel in enumerate(self.channels):
            tvg_name = channel['tvg_id']
            btn = ctk.CTkButton(self.content_frame, text=tvg_name,
                                command=lambda idx=index: self.choose_channel(idx),
                                corner_radius=10, fg_color="blue", hover_color="darkblue")
            btn.pack(fill="x", padx=5, pady=2)
    
    def choose_channel(self, idx):
        """Wird beim Klick auf einen EPG-Eintrag aufgerufen – startet den Sender."""
        if self.play_callback is not None:
            self.play_callback(idx)
        self.toggle_visibility()
    
    def toggle_visibility(self):
        """Schaltet die Sichtbarkeit des EPG-Overlays um.
           Das Overlay wird als leicht transparentes Fenster über dem Videobild angezeigt."""
        if self.winfo_ismapped():
            self.pack_forget()
        else:
            self.pack(side="left", fill="y", expand=False)
            self.configure(width=400)
            self.set_transparency(self.transparency)
    
    def set_transparency(self, alpha):
        """Setzt die Transparenz des EPG-Overlays."""
        self.transparency = alpha
        if alpha < 1.0:
            self.configure(fg_color=self.apply_alpha(self.cget("fg_color"), alpha))
            for child in self.winfo_children():
                if isinstance(child, ctk.CTkBaseClass):
                    child.configure(fg_color=self.apply_alpha(child.cget("fg_color"), alpha))
    
    def apply_alpha(self, color, alpha):
        """Wendet Alpha-Transparenz auf eine Farbe an."""
        if isinstance(color, str) and color.startswith("#"):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            return f"#{r:02x}{g:02x}{b:02x}{int(alpha*255):02x}"
        return color

def show_epg(parent, channels):
    """
    Öffnet den EPG-Overlay als Toplevel-Fenster, das leicht transparent über dem Videobild angezeigt wird.
    Es werden nur die tvg-Namen als klickbare Buttons angezeigt.
    """
    epg_window = ctk.CTkToplevel(parent)
    parent.update()
    width = parent.winfo_width()
    height = parent.winfo_height()
    epg_window.geometry(f"{int(width*0.4)}x{height}+{parent.winfo_rootx()}+{parent.winfo_rooty()}")
    epg_window.title("EPG")
    epg_window.attributes("-alpha", 0.7)
    epg_window.configure(fg_color="gray20")
    
    epg_frame = EPG(epg_window)
    epg_frame.pack(fill="both", expand=True)
    epg_frame.load_epg_data(channels)
    
    close_btn = ctk.CTkButton(epg_window, text="Schließen", command=epg_window.destroy, fg_color="blue")
    close_btn.pack(pady=5)
