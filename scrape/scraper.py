from bs4 import BeautifulSoup
import requests as r
import time as t
import pandas as pd
import json
from tqdm import tqdm

agent = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"}

# Scraper
def scraper (url):
    while True:
        request = r.get(url, headers=agent)
        t.sleep(0.35)
        if request.status_code == 200:
            soup = BeautifulSoup(request.content, "html.parser")
            return soup


# Find all the pages until there is a gray button
def url_extraction (starting_url):
    urls = [starting_url, ]
    while True:
        soup = scraper (starting_url)
        if not soup.find('li', class_="last Inlineblock F-shade"):
            href = soup.find('li', class_="last Inlineblock")
            starting_url = "".join(["https://basketball.fantasysports.yahoo.com"+tag['href'] for tag in href])
            urls.append(starting_url)
            print (f"{len(urls)} links so far")
        else:
            return urls

# Where we get player number Tags
def id_extraction (urls):
    ids = []
    for url in tqdm(urls, desc="Player ID"):
        soup = scraper (url)
        href_tags = soup.find_all('a', class_="Nowrap", href=True)
        [ids.append(id['href'].replace('https://sports.yahoo.com/nba/players/', '')) for id in href_tags]
    print (f"{len(ids)} Player ID's")
    return ids

def main ():
    starting_url = "https://basketball.fantasysports.yahoo.com/nba/2288/players?&sort=AR&sdir=1&status=ALL&pos=P&stat1=S_AS_2022&jsenabled="
    urls_extracted = url_extraction (starting_url)
    ids = id_extraction (urls_extracted)
    season_name = ["POSTSEASON", "REGULAR_SEASON"]
    urls = [f"https://graphite-secure.sports.yahoo.com/v1/query/shangrila/gameLogBasketball?lang=en-US&region=US&tz=America%2FNew_York&ysp_redesign=1&ysp_platform=smartphone&playerId=nba.p.{id}&season={season}&seasonPhase={season_type}" for id in ids for season in range(2010, 2023) for season_type in season_name]
    data = []
    for url in tqdm(urls, desc="Scraping Athlete Data"):
        soup = json.loads(scraper(url).text)
        name = soup['data']['players'][0]['displayName']
        for game in range(len(soup['data']['players'][0]['playerGameStats'])):
            info = {}
            team = soup['data']['players'][0]['playerGameStats'][game]['teamId']
            game_info = soup['data']['players'][0]['playerGameStats'][game]['game']
            info ['player'] = name

            for i, (k,v) in enumerate(game_info.items()):
                if k == "teams":
                    info ["player_team"] = "".join([playerteam['abbreviation'] for playerteam in v if team == playerteam['teamId']])
                    info ["opponent"] = "".join([playerteam['abbreviation'] for playerteam in v if team != playerteam['teamId']])
                else:
                    if k != "entity":
                        info[k] = v

            for index in range(len(soup['data']['players'][0]['playerGameStats'][game]['stats'])):
                stats = soup['data']['players'][0]['playerGameStats'][game]['stats'][index]
                for i, (k,v) in enumerate(stats.items()):
                    if k == "statId":
                        info [v] = "".join([v if v != None else "0" for i, (k,v) in enumerate(stats.items()) if k == 'value'])
            data.append(info)

    df = pd.DataFrame.from_records(data)
    path = r"C:\Users\kazir\OneDrive\Desktop\Github\NBA\CSVs\nbaV2.csv"
    pd.DataFrame.to_csv(df, path)
    print ("Scraping completed!")

main()