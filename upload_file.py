import os
import json
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = "service_account.json"
PARENT_FOLDER_ID = "1Am-sllHc9rEdKpnYEaitzFHN8oUsR-LY" 

def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=credentials)

def create_folder(service, folder_name, parent_id=None):
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id] if parent_id else []
    }
    
    folder = service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()
    
    print(f'Created folder: {folder_name} with ID: {folder.get("id")}')
    return folder.get('id')

def upload_file(service, file_path, folder_id):
    file_name = os.path.basename(file_path)
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(
        file_path,
        mimetype='application/pdf',
        resumable=True
    )
    
    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True
        ).execute()
        
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(
            fileId=file['id'],
            body=permission
        ).execute()
        
        print(f"Successfully uploaded: {file_name}")
        return file.get('webViewLink')
    except Exception as e:
        print(f"Error uploading {file_name}: {str(e)}")
        return None

def process_syllabus(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    service = get_drive_service()
    
    main_folder_id = PARENT_FOLDER_ID
    
    for branch_name, semesters in data.items():
        branch_folder_id = create_folder(service, branch_name, main_folder_id)
        
        for semester, courses in semesters.items():
            semester_folder_id = create_folder(service, semester, branch_folder_id)
            
            for course_name, _ in courses.items():
                sanitized_branch_name = re.sub(r'[^\w\s-]', '', branch_name).strip()
                sanitized_semester = re.sub(r'[^\w\s-]', '', semester).strip()
                sanitized_course_name = re.sub(r'[^\w\s-]', '', course_name).strip()
                file_path = f"pdfs/{sanitized_branch_name} {sanitized_semester} {sanitized_course_name}.pdf"
                
                if os.path.exists(file_path):
                    new_link = upload_file(service, file_path, semester_folder_id)
                    if new_link:
                        data[branch_name][semester][course_name] = new_link
                else:
                    print(f"Warning: File not found - {file_path}")
    
    with open('updated_syllabus.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

if __name__ == "__main__":
    try:
        updated_data = process_syllabus('syllabus.json')
        print("Process completed. Check updated_syllabus.json for results.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")