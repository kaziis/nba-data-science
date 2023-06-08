from requests_html import HTMLSession
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'vary': 'Y-PATH,Accept-Encoding',
    'x-yahoo-request-id': '1ouk8shhr6pj9',
    'referrer-policy': 'strict-origin-when-cross-origin',
    'content-encoding': 'gzip',
    'x-frame-options': 'SAMEORIGIN',
    'content-type': 'text/html; charset=UTF-8',
    'server': 'ATS',
    'Connection': 'keep-alive',
    'X-Content-Type-Options': 'nosniff'
    }

def yahoo(url):
    s = HTMLSession()
    r = s.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'html5lib')
    time.sleep(.5)
    return soup

# Links for getting href tags
urls = ['https://basketball.fantasysports.yahoo.com/nba/2288/players?status=ALL&pos=P&cut_type=33&stat1=S_S_2022&myteam=0&sort=AR&sdir=1&count=']
def next_page(soup):
    button = soup.find('li', class_="last Inlineblock")
    if not soup.find('li', class_="last Inlineblock F-shade"):
        for b in button:
            url = b.get('href').replace('/nba/2288/players', 'https://basketball.fantasysports.yahoo.com/nba/2288/players')
            urls.append(url)
        return url

# Player href tags
num_tags = []
def game_data(links):
    for link in links:
        a_tag = yahoo(link).find_all ('a', class_="Nowrap")
        for tag in a_tag:
            num_tags.append(tag.get('href').replace('https://sports.yahoo.com/nba/players/', ''))
        print (f"{len(num_tags)} tags converted.")
    print ('All tags successfully converted!')
    return num_tags



master_table = []
def per_game_data(tag, season_yr):
    try:
        player_json = f'https://graphite-secure.sports.yahoo.com/v1/query/shangrila/gameLogBasketball?lang=en-US&region=US&tz=America%2FNew_York&ysp_redesign=1&ysp_platform=smartphone&playerId=nba.p.{tag}&season={season_yr}&seasonPhase=REGULAR_SEASON'
        player = requests.get(player_json, headers).json()
        # Data collecting
        stat_heads = player ['data']['statTypes']
        player_stats = player ['data']['players'][0]['playerGameStats'][0]['stats']
        games_played = len (player ['data']['players'][0]['playerGameStats'])
        # Headers
        stat_header = ['Date', 'Name', 'Season', 'TM', 'Opp', 'Score']
        for heads in stat_heads:
            stat_header.append(heads['abbreviation'])
        # Stat
        for stats in range(games_played):
            name = (player ['data']['players'][0]['displayName']).title()
            date_data = (player ['data']['players'][0]['playerGameStats'][stats]['game']['startTime']).split('T')[0]
            season = (player ['data']['players'][0]['playerGameStats'][stats]['game']['season'])
            team_id = (player ['data']['players'][0]['playerGameStats'][stats]['teamId'])
            outcome = (player ['data']['players'][0]['playerGameStats'][stats]['game']['displayResult'])
            data = (player ['data']['players'][0]['playerGameStats'][stats]['stats'])
            home_team = (player ['data']['players'][0]['playerGameStats'][stats]['game'])['teams'][0]['abbreviation']
            away_team = (player ['data']['players'][0]['playerGameStats'][stats]['game'])['teams'][1]['abbreviation']
            athlete_stats = []
            # Date
            athlete_stats.append(datetime.strptime(date_data, '%Y-%m-%d').date())
            # Player name
            athlete_stats.append(name)
            #Season
            athlete_stats.append(season)
            # Home Team
            if (player ['data']['players'][0]['playerGameStats'][stats]['game'])['teams'][0]['teamId']==team_id:
                athlete_stats.append(home_team)
            else:
                athlete_stats.append(away_team)
            # Away Team
            if (player ['data']['players'][0]['playerGameStats'][stats]['game'])['teams'][1]['teamId']!=team_id:
                athlete_stats.append(away_team)
            else:
                athlete_stats.append(home_team)
            # Score
            athlete_stats.append(outcome)
            # Player stats per season
            for d in data:
                try:
                    athlete_stats.append(float(d['value']))
                except:
                    athlete_stats.append((d['value']))
            # Appending to the DataFrame for each game
            table = dict(zip(stat_header, athlete_stats))
            master_table.append(table)
            # Print progress
            print ('{}. Appended! Athlete: {}'.format(stats+1, name))
            print ("Score: {:15} Season: {}\n".format(outcome, season))
        print (f'Completed: {name}')
        return
    except:
        return print (f'No data for {tag}')

def main():
    # Site
    url = 'https://basketball.fantasysports.yahoo.com/nba/2288/players?status=ALL&pos=P&cut_type=33&stat1=S_S_2022&myteam=0&sort=AR&sdir=1&count='
    # Getting Pages
    while True:
        start = time.time()
        soup = yahoo(url)
        url = next_page(soup)
        if not url:
            break
        end = time.time()
        print (f'Getting pages... (Time Elapsed: {(end - start):.3})')
    # Tags
    game_data(urls)
    left = len(num_tags)
    for season_yr in range(2015,2023):
        done = 0
        for tags in num_tags:
            (per_game_data(tags, season_yr))
            done += 1
            # Progress
            print (f'Season: {season_yr}/2023')
            print (f'Completed: {done}/{left} ({(done/left*100):.2f}%)\n')

# File Name
file_name = input('Enter file name: ')

main ()

# DataFrame
df = pd.DataFrame(master_table)

# CSV
df.to_csv(f'{file_name}.csv')