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
    global last_scrape_time

    response = requests.get(link)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table", {"class": "table-mc-blue"})

        if table:
            links_dict = {}
            data_dict = {}

            rows = table.find_all("tr")

            for row in rows:
                cells = row.find_all("td")

                if len(cells) >= 3:
                    branch_name = cells[1].text.strip()
                    semester_buttons = cells[2].find_all("button")

                    branch_links = {}
                    branch_data = {}

                    for button in semester_buttons:
                        semester = button.find("span").text
                        link = button.get("onclick").split("'")[1]
                        branch_links[semester] = link

                        semester_data = {}
                        response = requests.get(link, timeout=2000)

                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, "html.parser")

                            tables = soup.find_all(
                                "table",
                                {
                                    "class": "table table-bordered table-striped table-hover table-mc-blue"
                                },
                            )

                            if tables:
                                for i, table in enumerate(tables):
                                    course_semester = f"Semester {semester}"
                                    semester_data[course_semester] = {}
                                    rows = table.find_all("tr")[1:]

                                    for row in rows:
                                        cells = row.find_all("td")
                                        if len(cells) == 2:
                                            course_name = (
                                                cells[0].find("center").text.strip()
                                            )
                                            try:
                                                drive_link = (
                                                    cells[1]
                                                    .find("button")
                                                    .get("onclick")
                                                    .split("'")[1]
                                                )
                                            except AttributeError as e:
                                                print(
                                                    f"Error extracting link for {course_name}: {e}"
                                                )
                                                drive_link = link

                                            semester_data[course_semester][
                                                course_name
                                            ] = drive_link

                            else:
                                print("Table not found on the webpage.")
                        else:
                            print(
                                "Failed to retrieve the webpage. Status code:",
                                response.status_code,
                            )

                        branch_data[semester] = semester_data

                    links_dict[branch_name] = branch_links
                    data_dict[branch_name] = branch_data

            new_data = {}
            for course, years in data_dict.items():
                new_data[course] = {}
                for year, semesters in years.items():
                    for semester, subjects in semesters.items():
                        if semester in new_data[course]:
                            new_data[course][semester].extend(subjects)
                        else:
                            new_data[course][semester] = subjects

            with open(DATA_FILE, "w") as output_file:
                json.dump(new_data, output_file, indent=2)

            last_scrape_time = time.time()

            print("Data saved as 'syllabus.json'")
        else:
            print(f"Table not found on the webpage: {link}")
    else:
        print(
            f"Failed to retrieve the webpage {link}. Status code: {response.status_code}"
        )

    return new_data

def scrape_if_needed():
    global last_scrape_time

    if not os.path.exists(DATA_FILE):
        scrape_and_save(SCRAPE_URL)
    elif last_scrape_time is None or time.time() - last_scrape_time > 30 * 24 * 60 * 60:  # 30 days
        scrape_and_save(SCRAPE_URL)

@app.route('/scrape', methods=['GET'])
def get_data():
    try:
        scrape_if_needed()
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

def periodic_scrape():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scrape_and_save, trigger="interval", args=[SCRAPE_URL], days=30)
    scheduler.start()

if __name__ == '__main__':
    scrape_if_needed()
    periodic_scrape()
    app.run(debug=True)