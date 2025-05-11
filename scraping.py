import requests
import pandas as pd
import time
import logging
from bs4 import BeautifulSoup
import cloudscraper
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Set up logging to track progress and errors
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_premier_league_data(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=headers)
        response.raise_for_status()
        time.sleep(5)

        # Parse the webpage
        soup = BeautifulSoup(response.text, 'html.parser')

        # Store the data
        data = {
            'final_table': [],
            'top_scorers': [],
            'goalkeeping': []
        }

        # Scrape Final Table
        table = soup.find('table', {'id': 'results2024-202591_overall'})
        if table:
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if cols:
                    data['final_table'].append({
                        'Team': row.find('th').text.strip(),
                        'Matches': cols[0].text.strip(),
                        'Wins': cols[1].text.strip(),
                        'Draws': cols[2].text.strip(),
                        'Losses': cols[3].text.strip(),
                        'Goals For': cols[4].text.strip(),
                        'Goals Against': cols[5].text.strip(),
                        'Points': cols[6].text.strip()
                    })
            logging.info("Final table scraped successfully")
        else:
            logging.warning("Final table not found")

        # Scrape Top Goal Scorers
        scorers_table = soup.find('table', {'id': 'results2024-202591_overall'})
        if scorers_table:
            rows = scorers_table.find('tbody').find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if cols:
                    data['top_scorers'].append({
                        'Team': row.find('th').text.strip(),
                        'Top Team Scorers': cols[11].text.strip(),
                    })
            logging.info("Top scorers scraped successfully")
        else:
            logging.warning("Top scorers table not found")

        # Scrape Squad Goalkeeping
        gk_table = soup.find('table', {'id': 'stats_squads_keeper_for'})
        if gk_table:
            rows = gk_table.find('tbody').find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if cols:
                    data['goalkeeping'].append({
                        'Team': row.find('th').text.strip(),
                        'Goals Against': cols[0].text.strip(),
                        'Saves': cols[1].text.strip(),
                        'Clean Sheets': cols[2].text.strip()
                    })
            logging.info("Goalkeeping data scraped successfully")
        else:
            logging.warning("Goalkeeping table not found")

        return data

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return None
    

def clean_data(data):
    # Convert to DataFrames
    final_table_df = pd.DataFrame(data['final_table'])
    top_scorers_df = pd.DataFrame(data['top_scorers'])
    goalkeeping_df = pd.DataFrame(data['goalkeeping'])

    # Clean Final Table
    if not final_table_df.empty:
        final_table_df = final_table_df.dropna(how='all')  # Remove fully empty rows
        # Convert numeric columns
        numeric_columns = ['Matches', 'Wins', 'Draws', 'Losses', 'Goals For', 'Goals Against', 'Points']
        final_table_df[numeric_columns] = final_table_df[numeric_columns].apply(pd.to_numeric, errors='coerce')
        # Calculate additional metric: Goal Difference
        final_table_df['Goal Difference'] = final_table_df['Goals For'] - final_table_df['Goals Against']
        final_table_df = final_table_df.fillna(0)  # Use 0 for numeric columns

    # Clean Top Scorers
    if not top_scorers_df.empty:
        top_scorers_df = top_scorers_df.dropna(how='all')
        # Ensure Top Team Scorers is text and handle NaN
        top_scorers_df['Top Team Scorers'] = top_scorers_df['Top Team Scorers'].fillna('N/A').astype(str)
        top_scorers_df = top_scorers_df.fillna('N/A')

    # Clean Goalkeeping
    if not goalkeeping_df.empty:
        goalkeeping_df = goalkeeping_df.dropna(how='all')
        # Convert numeric columns
        numeric_columns = ['Goals Against', 'Saves', 'Clean Sheets']
        goalkeeping_df[numeric_columns] = goalkeeping_df[numeric_columns].apply(pd.to_numeric, errors='coerce')
        goalkeeping_df = goalkeeping_df.fillna(0)  # Use 0 for numeric columns

    return final_table_df, top_scorers_df, goalkeeping_df

def write_to_google_sheets(final_table_df, top_scorers_df, goalkeeping_df, spreadsheet_id):
    try:
        # Connect to Google Sheets
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('premierleaguescraper.json', scope)
        client = gspread.authorize(creds)

        # Open the spreadsheet
        sheet = client.open_by_key(spreadsheet_id)

        # Write Final Table
        worksheet = sheet.worksheet('Final Table') if 'Final Table' in [ws.title for ws in sheet.worksheets()] else sheet.add_worksheet(title='Final Table', rows=100, cols=20)
        worksheet.clear()
        worksheet.update([final_table_df.columns.values.tolist()] + final_table_df.values.tolist())
        logging.info("Final Table written to Google Sheet")

        # Write Top Scorers
        worksheet = sheet.worksheet('Top Scorers') if 'Top Scorers' in [ws.title for ws in sheet.worksheets()] else sheet.add_worksheet(title='Top Scorers', rows=100, cols=20)
        worksheet.clear()
        worksheet.update([top_scorers_df.columns.values.tolist()] + top_scorers_df.values.tolist())
        logging.info("Top Scorers written to Google Sheet")

        # Write Goalkeeping
        worksheet = sheet.worksheet('Goalkeeping') if 'Goalkeeping' in [ws.title for ws in sheet.worksheets()] else sheet.add_worksheet(title='Goalkeeping', rows=100, cols=20)
        worksheet.clear()
        worksheet.update([goalkeeping_df.columns.values.tolist()] + goalkeeping_df.values.tolist())
        logging.info("Goalkeeping written to Google Sheet")

    except Exception as e:
        logging.error(f"Error writing to Google Sheet: {e}")

if __name__ == "__main__":
    url = "https://fbref.com/en/comps/9/Premier-League-Stats"
    spreadsheet_id = "165uoF40lApWvWzM86s9B95BtGlqMfhNQhLqCkB7pubM"
    data = scrape_premier_league_data(url)
    if data:
        final_table_df, top_scorers_df, goalkeeping_df = clean_data(data)
        print("Cleaned Final Table:\n", final_table_df)
        print("Cleaned Top Scorers:\n", top_scorers_df)
        print("Cleaned Goalkeeping:\n", goalkeeping_df)
        write_to_google_sheets(final_table_df, top_scorers_df, goalkeeping_df, spreadsheet_id)



