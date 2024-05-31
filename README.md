
# Syllabus Scraper API

This Flask application serves as an API for scraping and searching syllabus data. It scrapes syllabus data from a specific URL, saves it to a JSON file, and provides endpoints for accessing the data and searching through it.

## Features

- Scrapes syllabus data from a specific URL and saves it to a JSON file.
- Provides endpoints for accessing the scraped data (`/scrape`) and searching through it (`/search`).
- Uses BeautifulSoup for web scraping.
- Automatically scrapes new data every 30 days to ensure freshness.
- Implements error handling for bad requests and internal server errors.

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/syllabus-scraper.git
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the Flask application:
   ```
   python main.py
   ```

## Usage

### Scrape Data
To manually trigger a scrape and save operation, send a GET request to `/scrape` endpoint:
```
GET http://127.0.0.1:5000/scrape
```

### Retrieve Data
To retrieve the scraped syllabus data, send a GET request to `/scrape` endpoint:
```
GET http://127.0.0.1:5000/scrape
```

### Search Data
To search for syllabus data based on a search term, send a GET request to `/search` endpoint with the `term` query parameter:
```
GET http://127.0.0.1:5000/search?term=searchterm
```
Replace `searchterm` with your desired search term.

## Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



