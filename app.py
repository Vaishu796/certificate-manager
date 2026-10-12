import os
import uuid
import tempfile
import shutil
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import uvicorn

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVE_FOLDER_ID = "1BARCIs0ozbTE7hCXMFackiomqL2blT2Z"
SPREADSHEET_ID = "1MCHnJlIM6MWMwsDD9AYsUMExGFly9ZMAjmlERGq5-EU"
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="Certificate Management System",
    description="FOSSEE & Free and Open Source Creative Art Library Certificate Manager",
    version="1.0.0"
)

# Ensure static directories exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "uploads"), exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


import json

def get_google_creds(scopes):
    env_creds = os.environ.get("GOOGLE_CREDENTIALS") or os.environ.get("GOOGLE_SERVICE_ACCOUNT")
    if env_creds:
        try:
            creds_dict = json.loads(env_creds)
            return Credentials.from_service_account_info(creds_dict, scopes=scopes)
        except Exception as e:
            print(f"Error parsing GOOGLE_CREDENTIALS env var: {e}")

    if os.path.exists(CREDENTIALS_FILE):
        return Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)

    raise FileNotFoundError("Google credentials not found in environment variables or credentials.json")


def upload_to_drive(filepath: str, folder_id: str, original_filename: str) -> str:
    scopes = ['https://www.googleapis.com/auth/drive']
    creds = get_google_creds(scopes)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': original_filename,
        'parents': [folder_id]
    }

    media = MediaFileUpload(filepath, resumable=True)
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink, webContentLink',
        supportsAllDrives=True
    ).execute()

    return uploaded_file.get('id')


def record_in_sheet(data: dict, drive_file_id: str, spreadsheet_id: str) -> str:
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = get_google_creds(scopes)
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
    return current_time


@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Certificate Manager Web App</h1><p>Index file not found in static directory.</p>")


@app.get("/api/health")
async def health_check():
    """Verify that credentials file and configurations are present."""
    creds_exist = os.path.exists(CREDENTIALS_FILE)
    return {
        "status": "online",
        "credentials_configured": creds_exist,
        "drive_folder_id": DRIVE_FOLDER_ID,
        "spreadsheet_id": SPREADSHEET_ID,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/register")
async def register_activity(
    activity_name: str = Form(...),
    software: str = Form(...),
    organising_project: str = Form(...),
    coordinator: str = Form(...),
    activity_type: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    certificate_type: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        activity_id = f"ACT-2026-{str(uuid.uuid4())[:4].upper()}"
        template_id = f"T{str(uuid.uuid4())[:2].upper()}"

        # Save uploaded file safely
        saved_filename = f"{activity_id}_{file.filename}"
        uploads_dir = os.path.join(STATIC_DIR, "uploads")
        try:
            os.makedirs(uploads_dir, exist_ok=True)
            local_saved_path = os.path.join(uploads_dir, saved_filename)
            with open(local_saved_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_url = f"/static/uploads/{saved_filename}"
        except Exception:
            # Fallback to system temp directory (standard on Vercel/AWS Lambda)
            temp_dir = tempfile.gettempdir()
            local_saved_path = os.path.join(temp_dir, saved_filename)
            file.file.seek(0)
            with open(local_saved_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_url = f"/api/uploads/{saved_filename}"

        data = {
            "Activity ID": activity_id,
            "Activity Name": activity_name.strip(),
            "Software": software.strip(),
            "Organising Project": organising_project.strip(),
            "Coordinator": coordinator.strip(),
            "Activity Type": activity_type.strip(),
            "Start Date": start_date.strip(),
            "End Date": end_date.strip(),
            "Certificate Type": certificate_type.strip(),
            "Template ID": template_id,
            "Filename": file.filename,
            "LocalFileUrl": file_url
        }

        drive_id = None
        sheet_recorded = False
        error_notes = []

        # 1. Upload to Google Drive
        try:
            drive_id = upload_to_drive(local_saved_path, DRIVE_FOLDER_ID, file.filename)
        except Exception as e:
            error_notes.append(f"Google Drive upload warning: {str(e)}")

        # 2. Record to Google Sheet
        try:
            recorded_time = record_in_sheet(data, drive_id or "LOCAL_ONLY", SPREADSHEET_ID)
            data["Registered At"] = recorded_time
            sheet_recorded = True
        except Exception as e:
            error_notes.append(f"Google Sheets record warning: {str(e)}")
            data["Registered At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data["Drive File ID"] = drive_id
        data["Drive View Link"] = f"https://drive.google.com/file/d/{drive_id}/view" if drive_id else None
        data["Spreadsheet Link"] = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
        data["Warnings"] = error_notes

        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Activity registered successfully!",
            "data": data
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Server error: {str(e)}"}
        )


@app.get("/api/uploads/{filename}")
async def serve_uploaded_file(filename: str):
    # Try static uploads first, then system temp
    static_path = os.path.join(STATIC_DIR, "uploads", filename)
    if os.path.exists(static_path):
        return FileResponse(static_path)
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(temp_path):
        return FileResponse(temp_path)
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/activities")
async def get_recent_activities():
    """Fetch recent activities recorded in the Google Sheet."""
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = get_google_creds(scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        records = sheet.get_all_values()
        if not records:
            return {"activities": []}
        
        standard_headers = [
            "Activity ID", "Activity Name", "Software", "Organising Project",
            "Coordinator", "Activity Type", "Start Date", "End Date",
            "Certificate Type", "Template ID", "Drive File ID", "Registered At"
        ]

        # Check if the first row is a header
        first_row = records[0]
        if first_row and first_row[0].strip().lower() == "activity id":
            headers = first_row
            data_rows = records[1:]
        else:
            headers = standard_headers
            data_rows = records

        if not data_rows:
            return {"activities": []}

        # Return latest 15 rows (newest first)
        latest_rows = data_rows[-15:][::-1]
        results = []
        for r in latest_rows:
            row_dict = {}
            for idx, h in enumerate(headers):
                row_dict[h] = r[idx] if idx < len(r) else ""
            results.append(row_dict)

        return {"activities": results}
    except Exception as e:
        return {"activities": [], "error": str(e)}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
