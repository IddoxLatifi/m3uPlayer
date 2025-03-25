## This tool was created to automatically check your M3U lists. You can join multiple lists together; 
## the program will create a valid playlist and play it in VLC Player.
## VLC Player Download: https://www.videolan.org/vlc/index.de.html    Have fun with it.
## Created by @apt_start_latifi
## ALL RIGHTS RESERVED ©

import customtkinter as ctk
import vlc
import os
import sys
import re
import time
import requests
from datetime import datetime, timedelta
from epg import EPG 

os.add_dll_directory(r'C:\Program Files\VideoLAN\VLC')

VALIDATED_FILE= "validated_playlist.m3u"
timeout_ms = 10000  
playback_timeout_id = None
play_start_time = 0

class EPG(ctk.CTkFrame):
    def __init__(self, master, video_frame, **kwargs):
        super().__init__(master, **kwargs)
        self.video_frame = video_frame
        self.configure(fg_color="gray20")
        self.transparency = 0.8
        self.overlay = ctk.CTkFrame(master, fg_color="gray20")
        self.overlay.place(relx=0, rely=0, relwidth=0.3, relheight=1, anchor="nw")
        self.overlay.lift()
        self.header = ctk.CTkLabel(self.overlay, text="Electronic Program Guide", font=("Arial", 16, "bold"))
        self.header.pack(pady=10)
        self.content_frame = ctk.CTkScrollableFrame(self.overlay, fg_color="gray15")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.overlay.place_forget()
    
    def load_epg_data(self, channels):
        """Lade EPG-Daten aus den Channels (simuliert hier)"""
        self.channels = channels
        self.epg_data = {}
        for channel in self.channels:
            tvg_id = channel['tvg_id']
            self.epg_data[tvg_id] = [
                {"title": f"News at {datetime.now().hour}:00", "start": datetime.now(), "end": datetime.now() + timedelta(hours=1)},
                {"title": "Movie: The Great Adventure", "start": datetime.now() + timedelta(hours=1), "end": datetime.now() + timedelta(hours=3)},
                {"title": "Talk Show", "start": datetime.now() + timedelta(hours=3), "end": datetime.now() + timedelta(hours=4)}
            ]
        self.create_epg_display()
    
    def create_epg_display(self):
        """Erstellt die EPG-Anzeige: Es werden nur Buttons mit dem tvg-Namen angezeigt."""
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
        if hasattr(self, 'play_callback') and self.play_callback:
            self.play_callback(idx)
        self.toggle_visibility()
    
    def toggle_visibility(self):
        """Schaltet die Sichtbarkeit des EPG-Overlays um."""
        if self.overlay.winfo_ismapped():
            self.overlay.place_forget()
        else:
            self.overlay.place(relx=0, rely=0, relwidth=0.3, relheight=1, anchor="nw")
            self.overlay.lift()
            self.set_transparency(self.transparency)
    
    def set_transparency(self, alpha):
        """Setzt die Transparenz des EPG-Overlays."""
        self.transparency = alpha
        if alpha < 1.0:
            self.overlay.configure(fg_color=self._apply_alpha(self.overlay.cget("fg_color"), alpha))
            for child in self.overlay.winfo_children():
                if isinstance(child, ctk.CTkBaseClass):
                    child.configure(fg_color=self._apply_alpha(child.cget("fg_color"), alpha))
    
    def _apply_alpha(self, color, alpha):
        """Wendet Alpha-Transparenz auf eine Farbe an."""
        if isinstance(color, str) and color.startswith("#"):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            return f"#{r:02x}{g:02x}{b:02x}{int(alpha*255):02x}"
        return color


def load_playlists():
    """
    Liest die angegebenen Playlist-Dateien ein und extrahiert aus
    EXTINF-Zeilen den Wert für tvg-id. Für jeden Kanal wird ein Dictionary
    mit 'url' und 'tvg_id' erstellt.
    """
    channels = []
    playlist_files_env = os.getenv("PLAYLIST_FILES", "Germany_270.m3u")
    playlist_files = [pf.strip() for pf in playlist_files_env.split(",") if pf.strip()]
    
    for filename in playlist_files:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    if line.startswith('#EXTINF:'):
                        match = re.search(r'tvg-id="([^"]+)"', line)
                        tvg_id = match.group(1) if match else "Unbekannt"
                        if i + 1 < len(lines):
                            url_line = lines[i + 1].strip()
                            if url_line and not url_line.startswith('#'):
                                channels.append({'url': url_line, 'tvg_id': tvg_id})
                            i += 2
                        else:
                            i += 1
                    elif line and not line.startswith('#'):
                        channels.append({'url': line, 'tvg_id': "Unbekannt"})
                        i += 1
                    else:
                        i += 1
        else:
            print(f"Datei '{filename}' nicht gefunden.")
    return channels

def validate_links(channels, timeout=5):
    """
    Prüft jeden Kanal mittels eines HTTP-HEAD-Requests.
    Nur Links mit Status 200, 301 oder 302 werden übernommen.
    """
    valid_channels = []
    for channel in channels:
        url = channel['url']
        tvg_id = channel['tvg_id']
        try:
            print(f"Prüfe {tvg_id}: {url}")
            response = requests.head(url, timeout=timeout)
            if response.status_code in (200, 301, 302):
                valid_channels.append(channel)
                print(f"--> {tvg_id} funktioniert (Status: {response.status_code})")
            else:
                print(f"--> {tvg_id} liefert ungültigen Statuscode: {response.status_code}")
        except Exception as e:
            print(f"--> {tvg_id} Fehler: {e}")
    return valid_channels

def write_validated_playlist(channels, filename=VALIDATED_FILE):
    """
    Schreibt die validierten Kanäle in eine M3U-Datei.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for channel in channels:
            f.write(f'#EXTINF:-1 tvg-id="{channel["tvg_id"]}", {channel["tvg_id"]}\n')
            f.write(channel["url"] + "\n")

def load_playlist_from_file(filename):
    """
    Lädt eine M3U-Datei (mit EXTINF) und gibt eine Liste der Kanäle zurück.
    """
    channels = []
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("#EXTINF:"):
                match = re.search(r'tvg-id="([^"]+)"', line)
                tvg_id = match.group(1) if match else "Unbekannt"
                if i + 1 < len(lines):
                    url_line = lines[i+1].strip()
                    if url_line and not url_line.startswith('#'):
                        channels.append({'url': url_line, 'tvg_id': tvg_id})
                    i += 2
                else:
                    i += 1
            elif line and not line.startswith('#'):
                channels.append({'url': line, 'tvg_id': "Unbekannt"})
                i += 1
            else:
                i += 1
    return channels

def get_channels():
    """
    Prüft, ob bereits eine validierte Playlist vorliegt. Falls ja, wird sie geladen,
    andernfalls werden die Original-Listen geladen, validiert, gespeichert und zurückgegeben.
    """
    if os.path.exists(VALIDATED_FILE):
        print("Lade validierte Playlist...")
        return load_playlist_from_file(VALIDATED_FILE)
    else:
        print("Keine validierte Playlist gefunden. Lade und validiere Original-Listen...")
        channels = load_playlists()
        channels = validate_links(channels)
        if not channels:
            print("Keine funktionierenden Kanäle gefunden!")
            sys.exit()
        write_validated_playlist(channels)
        return channels

channels = get_channels()
current_channel = 0

instance = vlc.Instance()
player = instance.media_player_new()

def update_validated_file():
    """Schreibt die aktuelle Kanal-Liste in die Validierungsdatei."""
    write_validated_playlist(channels)

def remove_current_channel():
    """
    Entfernt den aktuellen Kanal aus der globalen Liste und aktualisiert die Validierungsdatei.
    """
    global channels, current_channel
    removed = channels.pop(current_channel)
    print(f"Entferne Kanal: {removed['tvg_id']}")
    update_validated_file()
    if not channels:
        print("Keine funktionierenden Kanäle mehr übrig!")
        sys.exit()
    current_channel = current_channel % len(channels)

def on_error(event):
    """
    Fehler-Callback: Bei VLC-Fehler wird der aktuelle Kanal entfernt und zum nächsten gewechselt.
    """
    print("Fehler beim Stream. Kanal wird entfernt.")
    remove_current_channel()
    root.after(500, lambda: play_channel(current_channel))

def check_playback_timeout():
    """
    Überprüft nach timeout_ms, ob der Player in den Zustand Playing oder Paused gewechselt hat.
    Wenn nicht, wird der Kanal als fehlerhaft gewertet, entfernt und der nächste geladen.
    """
    global playback_timeout_id
    current_state = player.get_state()
    if current_state not in (vlc.State.Playing, vlc.State.Paused):
        elapsed = time.time() - play_start_time
        if elapsed >= timeout_ms / 1000:
            print("Timeout: Kanal startet nicht. Kanal wird entfernt.")
            remove_current_channel()
            root.after(500, lambda: play_channel(current_channel))
            return
    playback_timeout_id = root.after(1000, check_playback_timeout)

def play_channel(index):
    """
    Stoppt die vorherige Wiedergabe, setzt den Error-Callback und startet den Kanal.
    Aktualisiert auch die Anzeige des aktuellen Titels.
    """
    global current_channel, play_start_time, playback_timeout_id
    current_channel = index
    player.stop()
    if playback_timeout_id is not None:
        root.after_cancel(playback_timeout_id)
    media = instance.media_new(channels[index]['url'])
    player.set_media(media)
    event_manager = player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEncounteredError, on_error)
    player.play()
    update_title_label(channels[index]['tvg_id'])
    play_start_time = time.time()
    playback_timeout_id = root.after(timeout_ms, check_playback_timeout)

def switch_channel(new_index):
    """
    Führt einen sauberen Kanalwechsel durch – stoppt den aktuellen Stream,
    wartet kurz und startet dann den neuen Kanal.
    """
    player.stop()
    if playback_timeout_id is not None:
        root.after_cancel(playback_timeout_id)
    root.after(500, lambda: play_channel(new_index))

def next_channel():
    switch_channel((current_channel + 1) % len(channels))

def prev_channel():
    switch_channel((current_channel - 1) % len(channels))

def toggle_pause():
    player.pause()

def set_volume(val):
    volume = int(val)
    player.audio_set_volume(volume)

def perform_search():
    query = search_entry.get().lower().strip()
    for widget in results_frame.winfo_children():
        widget.destroy()
    if not query:
        results_frame.pack_forget()
        return
    
    results = [ (i, ch) for i, ch in enumerate(channels) if query in ch['tvg_id'].lower() ]
    
    if not results:
        result_label = ctk.CTkLabel(results_frame, text="Keine Treffer gefunden.")
        result_label.pack(padx=5, pady=5)
    else:
        for idx, ch in results:
            btn = ctk.CTkButton(results_frame, text=ch['tvg_id'],
                              command=lambda idx=idx: play_channel(idx),
                              corner_radius=10)
            btn.pack(fill="x", padx=5, pady=2)
    
    results_frame.configure(height=min(120, (len(results) if results else 1) * 40 + 20))
    results_frame.pack(side="top", fill="x", padx=5, pady=(0,5))

def hide_results(event=None):
    try:
        if not search_entry.winfo_containing(event.x_root, event.y_root) and not results_frame.winfo_containing(event.x_root, event.y_root):
            results_frame.pack_forget()
    except Exception:
        pass

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("M3U8 Player")
root.state("zoomed") 
main_container = ctk.CTkFrame(root)
main_container.pack(fill="both", expand=True)
video_frame = ctk.CTkFrame(main_container)
video_frame.pack(fill="both", expand=True, padx=10, pady=10)
search_frame = ctk.CTkFrame(main_container, fg_color="transparent")
search_frame.place(relx=1, rely=0, x=-10, y=10, anchor="ne")
search_entry = ctk.CTkEntry(search_frame, placeholder_text="Suche nach tvg-id...", width=200)
search_entry.pack(padx=5, pady=5)
search_entry.bind("<Return>", lambda event: perform_search())
search_entry.bind("<FocusOut>", hide_results)
search_button = ctk.CTkButton(search_frame, text="Suchen", command=perform_search, corner_radius=10)
search_button.pack(padx=5, pady=5)
results_frame = ctk.CTkFrame(search_frame, fg_color="gray20", width=200, height=0)
control_frame = ctk.CTkFrame(main_container)
control_frame.pack(side="bottom", fill="x", padx=10, pady=10)
left_frame = ctk.CTkFrame(control_frame, width=200, border_width=2, border_color="blue")
left_frame.grid(row=0, column=0, sticky="w", padx=5)
current_title_label = ctk.CTkLabel(left_frame, text=f"Kanal: {channels[current_channel]['tvg_id']}", anchor="w")
current_title_label.pack(side="left", padx=5, pady=5)

def update_title_label(text):
    current_title_label.configure(text=f"Kanal: {text}")

center_frame = ctk.CTkFrame(control_frame)
center_frame.grid(row=0, column=1, sticky="nsew", padx=5)
control_frame.grid_columnconfigure(1, weight=1)

back_button = ctk.CTkButton(center_frame, text="Back", command=prev_channel, width=80, corner_radius=10)
back_button.pack(side="left", padx=5)

pause_button = ctk.CTkButton(center_frame, text="Pause/Play", command=toggle_pause, width=80, corner_radius=10)
pause_button.pack(side="left", padx=5)

next_button = ctk.CTkButton(center_frame, text="Next", command=next_channel, width=80, corner_radius=10)
next_button.pack(side="left", padx=5)

epg_button = ctk.CTkButton(center_frame, text="EPG", width=80, corner_radius=10)
epg_button.pack(side="left", padx=5)

right_frame = ctk.CTkFrame(control_frame, width=200)
right_frame.grid(row=0, column=2, sticky="e", padx=5)
volume_label = ctk.CTkLabel(right_frame, text="Volume:")
volume_label.pack(side="left", padx=5)
volume_slider = ctk.CTkSlider(right_frame, from_=0, to=100, command=set_volume, width=150)
volume_slider.set(player.audio_get_volume())
volume_slider.pack(side="left", padx=5)

epg = EPG(main_container, video_frame)
epg.play_callback = lambda idx: play_channel(idx)
epg_button.configure(command=epg.toggle_visibility)
epg.load_epg_data(channels)

root.bind("<Button-1>", hide_results)

root.update()
if sys.platform == "win32":
    player.set_hwnd(video_frame.winfo_id())
elif sys.platform == "linux":
    player.set_xwindow(video_frame.winfo_id())
elif sys.platform == "darwin":
    player.set_nsobject(video_frame.winfo_id())

root.after(1000, lambda: play_channel(current_channel))
root.mainloop()
