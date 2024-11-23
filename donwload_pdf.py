import requests
import json
import os
import re

def download_file_from_google_drive(file_id, destination):
    URL = "https://docs.google.com/uc?export=download&confirm=1"

    session = requests.Session()

    response = session.get(URL, params={"id": file_id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {"id": file_id, "confirm": token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value

    return None


def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
                f.write(chunk)


def extract_google_drive_id(url):
    match = re.search(r'(?:id=|/d/)([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None


def sanitize_filename(filename):
    return re.sub(r'[^\w\s-]', '', filename).strip()


with open('syllabus.json', 'r') as f:
    data = json.load(f)

if not os.path.exists('pdfs'):
    os.makedirs('pdfs')

for branch_name, semesters in data.items():
    for semester, courses in semesters.items():
        for course_name, drive_link in courses.items():
            sanitized_branch_name = sanitize_filename(branch_name)
            sanitized_semester = sanitize_filename(semester)
            sanitized_course_name = sanitize_filename(course_name)
            filename = f"pdfs/{sanitized_branch_name} {sanitized_semester} {sanitized_course_name}.pdf"

            if os.path.exists(filename):
                print(f"File already exists, skipping: {filename}")
                continue

            file_id = extract_google_drive_id(drive_link)
            if file_id:
                print(f"Downloading {filename}")
                download_file_from_google_drive(file_id, filename)
                print(f"Successfully downloaded {filename}")
            else:
                print(f"Failed to extract file ID from URL: {drive_link}")
                print("All files have been processed.")