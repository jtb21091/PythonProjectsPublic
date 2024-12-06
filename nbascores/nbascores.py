import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import leaguegamefinder, playercareerstats
from requests import get
from pprint import PrettyPrinter
import os

# Base URLs and endpoints
BASE_URL = "https://data.nba.net"
ALL_JSON = "/prod/v1/today.json"

printer = PrettyPrinter()


def get_links():
    """
    Retrieve the 'links' section of the NBA data, which provides
    endpoints for currentScoreboard, leagueTeamStatsLeaders, etc.
    """
    data = get(BASE_URL + ALL_JSON).json()
    links = data['links']
    return links


def get_scoreboard():
    """
    Fetch current scoreboard info and save to 'nba_scoreboard.xlsx'.
    Includes home team, away team, scores, clock, and period.
    """
    scoreboard = get_links()['currentScoreboard']
    games_json = get(BASE_URL + scoreboard).json().get('games', [])

    if not games_json:
        print("No current games available.")
        return

    game_data = []
    for game in games_json:
        home_team = game['hTeam']
        away_team = game['vTeam']
        clock = game['clock']
        period = game['period']

        game_data.append({
            "home_team": home_team['triCode'],
            "away_team": away_team['triCode'],
            "home_score": home_team['score'],
            "away_score": away_team['score'],
            "clock": clock,
            "period": period['current']
        })

        print("------------------------------------------")
        print(f"{home_team['triCode']} vs {away_team['triCode']}")
        print(f"{home_team['score']} - {away_team['score']}")
        print(f"{clock} - {period['current']}")

    # Convert to DataFrame and save to Excel
    df = pd.DataFrame(game_data)
    df.to_excel("nba_scoreboard.xlsx", index=False)
    print("Scoreboard data saved to 'nba_scoreboard.xlsx'.")


def get_stats():
    """
    Retrieve league team stats leaders and save the data to 'nba_team_stats.xlsx'.
    Prints a ranked list of teams based on points per game (ppg).
    """
    stats_link = get_links()['leagueTeamStatsLeaders']
    response = get(BASE_URL + stats_link).json()

    teams_data = response.get('league', {}).get('standard', {}).get('regularSeason', {}).get('teams', [])
    if not teams_data:
        print("No team stats data found.")
        return

    # Filter out placeholder "Team" entries
    teams_data = list(filter(lambda x: x['name'] != "Team", teams_data))
    teams_data.sort(key=lambda x: int(x['ppg']['rank']))

    team_data = []
    for i, team in enumerate(teams_data):
        name = team['name']
        nickname = team['nickname']
        ppg = team['ppg']['avg']
        team_data.append({
            "rank": i + 1,
            "name": name,
            "nickname": nickname,
            "ppg": ppg
        })
        print(f"{i + 1}. {name} - {nickname} - {ppg}")

    # Convert to DataFrame and save to Excel
    df = pd.DataFrame(team_data)
    df.to_excel("nba_team_stats.xlsx", index=False)
    print("Team stats data saved to 'nba_team_stats.xlsx'.")


def get_team_games(team_name):
    """
    Retrieve games played by a specific team.
    Saves the result to '<team_name>_games.xlsx'.
    """
    nba_teams = teams.get_teams()
    matching_teams = [t for t in nba_teams if t['full_name'].lower() == team_name.lower()]

    if not matching_teams:
        print(f"No team found with the name '{team_name}'.")
        return None

    team_id = matching_teams[0]['id']

    # Use the LeagueGameFinder endpoint for team games
    gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
    games_df = gamefinder.get_data_frames()[0]

    filename = f"{team_name.replace(' ', '_')}_games.xlsx"
    games_df.to_excel(filename, index=False)
    print(f"Game data for '{team_name}' saved to '{filename}'.")
    return games_df


def get_team_info(team_name):
    """
    Get basic info about a given NBA team (id, abbreviation, city, full name).
    """
    nba_teams = teams.get_teams()
    matching_teams = [t for t in nba_teams if t['full_name'].lower() == team_name.lower()]

    if not matching_teams:
        print(f"No team found with the name '{team_name}'.")
        return None

    team = matching_teams[0]
    print(f"Team ID: {team['id']}")
    print(f"Abbreviation: {team['abbreviation']}")
    print(f"City: {team['city']}")
    print(f"Full Name: {team['full_name']}")
    return team


def get_player_id_by_name(player_name):
    """
    Retrieve a player's ID given their full name.
    """
    all_players = players.get_players()
    matching_players = [p for p in all_players if p['full_name'].lower() == player_name.lower()]

    if not matching_players:
        print(f"No player found with the name '{player_name}'.")
        return None

    return matching_players[0]['id']


def get_player_career_stats(player_name):
    """
    Get a player's career stats using playercareerstats endpoint.
    Saves the data to '<player_name>_career_stats.xlsx'.
    """
    player_id = get_player_id_by_name(player_name)
    if not player_id:
        return None

    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    career_df = career.get_data_frames()[0]

    filename = f"{player_name.replace(' ', '_')}_career_stats.xlsx"
    career_df.to_excel(filename, index=False)
    print(f"Career stats for '{player_name}' saved to '{filename}'.")
    return career_df


# Example usage
if __name__ == "__main__":
    # You can comment these input prompts out if you'd prefer to hard-code values.
    # For demonstration:
    user_choice = input("Do you want to look up a (T)eam or (P)layer? Enter T or P: ").strip().lower()
    if user_choice == 't':
        team_name_input = input("Enter the full team name (e.g., 'Los Angeles Lakers'): ").strip()
        get_team_info(team_name_input)
        get_team_games(team_name_input)
    elif user_choice == 'p':
        player_name_input = input("Enter the player's full name (e.g., 'LeBron James'): ").strip()
        get_player_career_stats(player_name_input)

    # Fetch scoreboard and league-wide stats (optional)
    get_scoreboard()
    get_stats()
