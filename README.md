# The Premier League Data Scraping Pipeline

## Overview
This project scrapes 2024/2025 Premier League data from [FBref](https://fbref.com/en/comps/9/Premier-League-Stats), including the Final Table, Top Team Scorers, and Squad Goalkeeping data. The data is cleaned, processed, and stored in a Google Sheet.

## Setup Instructions
1. Create a folder (e.g., `premier_league_scraper`) and navigate to it.
2. Set up a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install requests beautifulsoup4 pandas gspread oauth2client cloudscraper`
4. Set up Google Sheets API and save `credentials.json`.
5. Update `scraping.py` with your Google Sheet ID.

## Running the Pipeline
Run: `python scraping.py`

## Known Limitations
- Table IDs may change.
- Rate limits may cause 403 errors.