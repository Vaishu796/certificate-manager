import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import uuid
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- Configuration ---
DRIVE_FOLDER_ID = "1BARCIs0ozbTE7hCXMFackiomqL2blT2Z"
SPREADSHEET_ID = "1MCHnJlIM6MWMwsDD9AYsUMExGFly9ZMAjmlERGq5-EU"
CREDENTIALS_FILE = "credentials.json"

# --- Google API Functions ---
def upload_to_drive(filepath, folder_id):
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    
    filename = os.path.basename(filepath)
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(filepath, resumable=True)
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    return uploaded_file.get('id')

def record_in_sheet(data, drive_file_id, spreadsheet_id):
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(spreadsheet_id).sheet1
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    row_data = [
        data.get("Activity ID", ""),
        data.get("Activity Name", ""),
        data.get("Software", ""),
        data.get("Organising Project", ""),
        data.get("Coordinator", ""),
        data.get("Activity Type", ""),
        data.get("Start Date", ""),
        data.get("End Date", ""),
        data.get("Certificate Type", ""),
        data.get("Template ID", ""),
        drive_file_id,
        current_time
    ]
    
    sheet.append_row(row_data)

# --- GUI Application ---
class CertificateManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FREE and Open Source Creative Art Library - Certificate Management System")
        self.geometry("850x820")
        self.configure(bg="#f8f9fa")

        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        style.configure('TFrame', background='#f8f9fa')
        style.configure('TLabel', background='#f8f9fa', font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 18, 'bold'), foreground='#0a3a60')
        style.configure('TEntry', fieldbackground='white', padding=5)
        style.configure('TRadiobutton', background='#f8f9fa', font=('Segoe UI', 10))
        style.configure('TCombobox', padding=5)

        # Header banner
        header_frame = tk.Frame(self, bg="white", height=90)
        header_frame.pack(fill="x", side="top")
        
        try:
            logo_img = Image.open("focal_logo.png")
            aspect_ratio = logo_img.width / logo_img.height
            new_width = int(70 * aspect_ratio)
            logo_img = logo_img.resize((new_width, 70), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(header_frame, image=self.logo_photo, bg="white")
            logo_label.pack(side="left", padx=30, pady=10)
        except Exception as e:
            print(f"Error loading logo: {e}")

        header_label = tk.Label(header_frame, text="FREE AND OPEN SOURCE CREATIVE ART LIBRARY", font=("Georgia", 16, "bold"), bg="white", fg="#0a3a60")
        header_label.pack(side="left", pady=10)

        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=40, pady=15)
        self.frames = {}
        
        self.frames["Registration"] = RegistrationFrame(self.container, self)
        self.frames["Success"] = SuccessFrame(self.container, self)

        self.frames["Registration"].grid(row=0, column=0, sticky="nsew")
        self.frames["Success"].grid(row=0, column=0, sticky="nsew")

        self.show_frame("Registration")

    def show_frame(self, page_name, data=None):
        frame = self.frames[page_name]
        if page_name == "Success" and data:
            frame.populate_data(data)
        frame.tkraise()

class RegistrationFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Register a New Activity", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        self.entries = {}
        fields = ["Activity Name", "Software", "Organising Project", "Coordinator"]
        for i, field in enumerate(fields):
            ttk.Label(self, text=field + " *", font=("Segoe UI", 10, "bold")).grid(row=i*2+1, column=0, sticky="w", pady=(2, 0))
            entry = ttk.Entry(self, width=60)
            entry.grid(row=i*2+2, column=0, columnspan=2, sticky="w", pady=(0, 5))
            self.entries[field] = entry

        ttk.Label(self, text="Activity Type *", font=("Segoe UI", 10, "bold")).grid(row=9, column=0, sticky="w", pady=(2, 0))
        self.activity_type = ttk.Combobox(self, values=["Workshop", "Seminar", "Hackathon", "Course"], width=57, state="readonly")
        self.activity_type.grid(row=10, column=0, columnspan=2, sticky="w", pady=(0, 5))
        self.activity_type.set("Select Activity Type")

        ttk.Label(self, text="Start Date *", font=("Segoe UI", 10, "bold")).grid(row=11, column=0, sticky="w")
        ttk.Label(self, text="End Date *", font=("Segoe UI", 10, "bold")).grid(row=11, column=1, sticky="w")
        self.start_date = ttk.Entry(self, width=28)
        self.start_date.insert(0, "dd-mm-yyyy")
        self.start_date.grid(row=12, column=0, sticky="w", pady=(0, 5), padx=(0, 10))
        self.end_date = ttk.Entry(self, width=28)
        self.end_date.insert(0, "dd-mm-yyyy")
        self.end_date.grid(row=12, column=1, sticky="w", pady=(0, 5))

        ttk.Label(self, text="Certificate Type *", font=("Segoe UI", 10, "bold")).grid(row=13, column=0, sticky="w", pady=(5, 2))
        self.cert_type_var = tk.StringVar(value="Participation")
        
        cert_types = [
            ("Participation", 0, 0), ("Appreciation", 0, 1),
            ("Achievement / Winner", 1, 0), ("Contribution", 1, 1),
            ("Completion", 2, 0), ("Lab Migration", 2, 1),
            ("Special Recognition", 3, 0)
        ]
        
        radio_frame = ttk.Frame(self)
        radio_frame.grid(row=14, column=0, columnspan=2, sticky="w")
        
        for text, r, c in cert_types:
            ttk.Radiobutton(radio_frame, text=text, variable=self.cert_type_var, value=text).grid(row=r, column=c, sticky="w", padx=(0, 25), pady=1)

        self.register_btn = tk.Button(self, text="REGISTER ACTIVITY", bg="#8C2131", fg="white", font=("Segoe UI", 11, "bold"), command=self.handle_register, relief="flat", activebackground="#6b1926", activeforeground="white", cursor="hand2")
        self.register_btn.grid(row=15, column=0, columnspan=2, pady=15, ipadx=50, ipady=5)

    def handle_register(self):
        filepath = filedialog.askopenfilename(
            title="Select Blank Certificate Template",
            filetypes=[("PDF/Image Files", "*.pdf *.png *.jpg")]
        )
        
        if not filepath:
            return 

        data = {
            "Activity ID": f"ACT-2026-{str(uuid.uuid4())[:4].upper()}",
            "Activity Name": self.entries["Activity Name"].get(),
            "Software": self.entries["Software"].get(),
            "Organising Project": self.entries["Organising Project"].get(),
            "Coordinator": self.entries["Coordinator"].get(),
            "Activity Type": self.activity_type.get(),
            "Start Date": self.start_date.get(),
            "End Date": self.end_date.get(),
            "Certificate Type": self.cert_type_var.get(),
            "Template ID": f"T{str(uuid.uuid4())[:2].upper()}",
            "Filepath": filepath
        }

        try:
            # Update button to show progress
            self.register_btn.config(text="Uploading...", state="disabled")
            self.update()

            drive_id = upload_to_drive(filepath, DRIVE_FOLDER_ID)
            record_in_sheet(data, drive_id, SPREADSHEET_ID)
            
            # Reset button state
            self.register_btn.config(text="Register Activity", state="normal")
            
            self.controller.show_frame("Success", data)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.register_btn.config(text="Register Activity", state="normal")

class SuccessFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        banner = tk.Label(self, text="✓ Activity Registered Successfully", bg="#dcfce7", fg="#166534", font=("Segoe UI", 13, "bold"), anchor="w", padx=15, pady=12)
        banner.pack(fill="x", pady=(0, 25))

        self.details_frame = ttk.Frame(self)
        self.details_frame.pack(fill="x", pady=10)

        ttk.Label(self, text="Approved Blank Certificate Template", font=("Segoe UI", 12, "bold"), foreground="#0a3a60").pack(anchor="w", pady=(15, 5))
        self.preview_canvas = tk.Canvas(self, bg="#eaeff3", height=250, highlightthickness=1, highlightbackground="#ccc")
        self.preview_canvas.pack(fill="x", pady=5)
        self.preview_text = self.preview_canvas.create_text(350, 125, text="Preview Not Loaded", fill="#555", font=("Segoe UI", 14, "italic"))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=15)
        
        tk.Button(btn_frame, text="VIEW FULL SIZE", bg="#0a3a60", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(side="left", padx=(0, 15), ipadx=10, ipady=5)
        tk.Button(btn_frame, text="DOWNLOAD BLANK TEMPLATE", bg="#8C2131", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").pack(side="left", ipadx=10, ipady=5)
        
        tk.Button(self, text="← Register Another Activity", bg="#e2e8f0", fg="#333", font=("Segoe UI", 10, "bold"), command=lambda: self.controller.show_frame("Registration"), relief="flat", cursor="hand2").pack(anchor="w", pady=30, ipadx=15, ipady=5)

    def populate_data(self, data):
        for widget in self.details_frame.winfo_children():
            widget.destroy()

        row = 0
        display_fields = ["Activity ID", "Activity Name", "Software", "Organising Project", "Coordinator", "Activity Type", "Start Date", "End Date", "Certificate Type", "Template ID"]
        for field in display_fields:
            ttk.Label(self.details_frame, text=field, width=20, font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Label(self.details_frame, text=data.get(field, "")).grid(row=row, column=1, sticky="w", pady=2)
            row += 1

        filename = os.path.basename(data["Filepath"])
        self.preview_canvas.itemconfig(self.preview_text, text=filename)

if __name__ == "__main__":
    app = CertificateManagerApp()
    app.mainloop()
