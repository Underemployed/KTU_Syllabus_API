from flask import Flask, jsonify, request, abort
from bs4 import BeautifulSoup
import requests
import json
import validators
import os
import time
from datetime import datetime, timedelta
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

DATA_FILE = "syllabus.json"
SCRAPE_URL = "https://www.ktuqbank.com/p/ktu-2019-batch-btech-syllabus.html"
last_scrape_time = None

def scrape_and_save(link):
    response = requests.get(link)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"class": "table-mc-blue"})
        
        if table:
            data_dict = {}
            rows = table.find_all("tr")
            
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    branch_name = cells[1].text.strip()
                    year_buttons = cells[2].find_all("button")
                    branch_data = {}
                    
                    # Process each year (which contains 2 semesters)
                    for year_idx, year_button in enumerate(year_buttons, 1):
                        year_link = year_button.get("onclick").split("'")[1]
                        year_response = requests.get(year_link, timeout=2000)
                        
                        if year_response.status_code == 200:
                            year_soup = BeautifulSoup(year_response.text, "html.parser")
                            semester_tables = year_soup.find_all("table", {"class": "table table-bordered table-striped table-hover table-mc-blue"})
                            
                            # Process both semesters in this year
                            for sem_idx, sem_table in enumerate(semester_tables, 1):
                                actual_sem = (year_idx - 1) * 2 + sem_idx
                                semester_key = f"Semester {actual_sem}"
                                print(f"Fetching data for {branch_name}, {semester_key}")
                                
                                semester_data = {}
                                rows = sem_table.find_all("tr")[1:]
                                
                                for row in rows:
                                    cells = row.find_all("td")
                                    if len(cells) == 2:
                                        course_name = cells[0].find("center").text.strip()
                                        try:
                                            button = cells[1].find("button")
                                            drive_link = button.get("onclick").split("'")[1] if button else "#no_link"
                                        except AttributeError:
                                            drive_link = "#no_link"
                                        
                                        semester_data[course_name] = drive_link
                                
                                branch_data[semester_key] = semester_data
                    
                    data_dict[branch_name] = branch_data
            
            with open(DATA_FILE, "w") as output_file:
                json.dump(data_dict, output_file, indent=2)
            
            return data_dict

@app.route('/scrape', methods=['GET'])
def get_data():
    try:
        with open(DATA_FILE, "r") as data_file:
            data = json.load(data_file)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/search', methods=['GET'])
def search():
    term = request.args.get('term', default="", type=str).lower()
    if not term:
        abort(400, description="Search term is required")

    try:
        with open(DATA_FILE, "r") as data_file:
            data = json.load(data_file)

        results = {}
        for course, semesters in data.items():
            for semester, subjects in semesters.items():
                for subject, link in subjects.items():
                    if term in subject.lower():
                        if course not in results:
                            results[course] = {}
                        if semester not in results[course]:
                            results[course][semester] = {}
                        results[course][semester][subject] = link

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.errorhandler(400)
def handle_bad_request(e):
    return jsonify(error=str(e)), 400

@app.errorhandler(500)
def handle_internal_server_error(e):
    return jsonify(error=str(e)), 500


if __name__ == '__main__':
    scrape_and_save(SCRAPE_URL)

