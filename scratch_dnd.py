from tkinterdnd2 import TkinterDnD, DND_FILES
import customtkinter as ctk

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        self.title("Test DnD")
        self.geometry("300x200")
        
        self.label = ctk.CTkLabel(self, text="Drop folder here")
        self.label.pack(expand=True, fill="both")
        
        self.label.drop_target_register(DND_FILES)
        self.label.dnd_bind('<<Drop>>', self.drop)
        
    def drop(self, event):
        self.label.configure(text=event.data)

if __name__ == "__main__":
    app = App()
    app.after(1000, app.destroy) # close after 1s for testing
    app.mainloop()
