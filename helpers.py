import pandas as pd
import numpy as np
import pulp
from bs4 import BeautifulSoup


def read_data(gw_start, gw_end) -> pd.DataFrame:
        
    with open(f"gw{gw_start}-{gw_end}.html", 'r') as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    gameweeks = [f"gw{i}" for i in range(gw_start,gw_end+1)]
    lines = []
    keys = ['player', 'team', 'position', 'price'] + gameweeks
    for tr in soup.select("tr"):

        values = [_.text for _ in tr.select("td")]

        if len(values) == 0:
            continue

        line = {}

        for key, value in zip(keys, values):
            line[key] = value

        lines.append(line)

    df = pd.DataFrame(lines)

    for key in keys[3:]:
        df[key] = df[key].astype(float)

    df['team'] = df['team'].str.strip()

    df['gw_first_3'] = df[gameweeks[0:3]].sum(axis=1)
    df['gw_all'] = df[gameweeks].sum(axis=1)

    return df


def optimize(
    data, of, budget=100.0, defenders=5, midfielders=5, forwards=3, goalkeepers=2,
    team_restrictions=[], position_restrictions=[], player_selection=[], player_banned=[]
) -> pd.DataFrame:
    """
    of: Gameweek to optimize for
    position_restrictions: [('team', [max_gk_count], [max_def_count], [max_mid_count], [max_fwd_count])]
    team_restrictions: [('team', [max_player_count])]
    player_selection: [('team', 'player_name')]    
    """
    # Total team count should be the sum of field counds
    player_count = sum([defenders, midfielders, forwards, goalkeepers])
    
    dtr = 2
    tr = {}
    for team, players in team_restrictions:
        tr[team] = players
        
    dpr = 1
    pr = {}
    for team, g, d, m, f in position_restrictions:
        pr[team] = {
            "gk": g, "def": d, "mid": m, "fwd": f
        }
        
    model = pulp.LpProblem("FPL_team_optimization", pulp.LpMaximize)
    
    player_name = data.player.to_list()
    player_index = data.index.to_list()
    player_prices = data.price.to_list()
    player_expected_points = data[of].to_list()
    player_position = data.position.to_list()
    player_team = data.team.to_list()
    teams = data.team.unique()
    
    players = pulp.LpVariable.dicts("FLP_players",
                                     (i for i in player_index),
                                     lowBound=0,
                                     upBound=1,
                                     cat='Integer')
    
    # Objective function, maximize expected points
    model += (
        pulp.lpSum([player_expected_points[i]*players[i] for i in player_index])
    )

    # Set inequality constraints on both the budget and the player count
    model += pulp.lpSum([player_prices[i]*players[i] for i in player_index]) <= budget
    model += pulp.lpSum([players[i] for i in player_index]) == player_count
    
    # Set inequality constraints on team combinations, following the (2,5,5,3) lineup.
    model += pulp.lpSum([int(player_position[i]=='GK' )*players[i] for i in player_index]) <= goalkeepers
    model += pulp.lpSum([int(player_position[i]=='DEF')*players[i] for i in player_index]) <= defenders
    model += pulp.lpSum([int(player_position[i]=='MID')*players[i] for i in player_index]) <= midfielders
    model += pulp.lpSum([int(player_position[i]=='FWD')*players[i] for i in player_index]) <= forwards
    
    
    # Team restrictions
    for team in teams:
        
        team_poition_restrictions = pr.get(team, {})
        
        # Get the indexed for all the players that are in this team
        team_index = [i for i, t in zip(player_index, player_team) if t == team]
               
        model += pulp.lpSum([players[i] for i in team_index]) <= tr.get(team, dtr)
        
        model += pulp.lpSum([int(player_position[i]=='GK' )*players[i] for i in team_index]) <= team_poition_restrictions.get('gk', dpr)
        model += pulp.lpSum([int(player_position[i]=='DEF')*players[i] for i in team_index]) <= team_poition_restrictions.get('def', dpr)
        model += pulp.lpSum([int(player_position[i]=='MID')*players[i] for i in team_index]) <= team_poition_restrictions.get('mid', dpr)
        model += pulp.lpSum([int(player_position[i]=='FWD')*players[i] for i in team_index]) <= team_poition_restrictions.get('fwd', dpr)

    # Player restrictions
    for i, team, player in zip(player_index, player_team, player_name):
        if (team, player) in player_selection:
            model += players[i] == 1
        elif (team, player) in player_banned:
            model += players[i] == 0
      
    # Solve the problem and write the formulas to 
    model.writeLP("FPL.lp")
    model.solve()
        
    team = data[np.array([players[_].varValue for _ in player_index]) == 1]

    print(pulp.LpStatus[model.status])
    #print("team total cost:", team.price.sum())
    #print("expected points, sub captain:", [team[_].sort_values(ascending=False).head(11).sum().round() for _ in ['gw1', 'gw2', 'gw3', 'gw4', 'gw5', 'gw6']])
    return team