from nba_api.stats.endpoints import leagueleaders
from nba_api.stats.library.parameters import LeagueID, PerMode48, Scope, SeasonTypeAllStar, StatCategoryAbbreviation

import csv
import json
import pprint as pp
import re
import unicodedata
import traceback


def generate_seasons(first_season, last_season):
    seasons = []
    for i in range(first_season, last_season + 1):
        next_season_abbr = (i + 1) % 100
        if next_season_abbr < 10:
            seasons.append(str(i) + '-0' + str(next_season_abbr))
        else:
            seasons.append(str(i) + '-' + str(next_season_abbr))
    return seasons


def get_param_indices():
    return {'PLAYER_ID': 0,
            'RANK': 1,
            'PLAYER': 2,
            'TEAM': 3,
            'GP': 4,
            'MIN': 5,
            'FGM': 6,
            'FGA': 7,
            'FG_PCT': 8,
            'FG3M': 9,
            'FG3A': 10,
            'FG3_PCT': 11,
            'FTM': 12,
            'FTA': 13,
            'FT_PCT': 14,
            'OREB': 15,
            'DREB': 16,
            'REB': 17,
            'AST': 18,
            'STL': 19,
            'BLK': 20,
            'TOV': 21,
            'PTS': 22,
            'EFF': 23}


def get_leaders(season, stat):
    leaders = leagueleaders.LeagueLeaders(league_id=LeagueID.nba, per_mode48=PerMode48.per_game, scope=Scope.s,
                                          season=season,
                                          season_type_all_star=SeasonTypeAllStar.regular,
                                          stat_category_abbreviation=stat)
    return leaders

# def get_leaders(season, stat):
#     try:
#         leaders = leagueleaders.LeagueLeaders(league_id=LeagueID.nba, per_mode48=PerMode48.per_game, scope=Scope.s,
#                                               season=season,
#                                               season_type_all_star=SeasonTypeAllStar.regular,
#                                               stat_category_abbreviation=stat)
#         return leaders
#     except:
#         traceback.print_exc()


def parse_leaders(players_dict, top_x, stat_name, stat_index, name_index, rank_index):
    leader_dict = {}
    for player in players_dict['resultSet']['rowSet'][:top_x]:
        leader_dict[player[name_index]] = [player[stat_index], stat_name, player[rank_index]]
    return leader_dict


def get_pts_reb_ast_leaders(seasons, top_x, player_param, rank_param):

    pts_stat = StatCategoryAbbreviation.pts
    ast_stat = StatCategoryAbbreviation.ast
    reb_stat = StatCategoryAbbreviation.reb
    param_indices = get_param_indices()

    top_stat_players = {}
    for season in seasons:
        print('Checking season:', season)

        pts_leaders = get_leaders(season, pts_stat)
        pts_dict = parse_leaders(pts_leaders.get_dict(), top_x, pts_stat,
                                 param_indices[pts_stat], param_indices[player_param], param_indices[rank_param])

        reb_leaders = get_leaders(season, reb_stat)
        reb_dict = parse_leaders(reb_leaders.get_dict(), top_x, reb_stat,
                                 param_indices[reb_stat], param_indices[player_param], param_indices[rank_param])

        ast_leaders = get_leaders(season, ast_stat)
        ast_dict = parse_leaders(ast_leaders.get_dict(), top_x, ast_stat,
                                 param_indices[ast_stat], param_indices[player_param], param_indices[rank_param])

        pts_reb_ast_dict = {}
        for key in pts_dict.keys():
            if key in ast_dict.keys() and key in reb_dict.keys():
                pts_reb_ast_dict[key] = [pts_dict[key], reb_dict[key], ast_dict[key]]
            if key in reb_dict.keys() and key not in ast_dict.keys():
                pts_reb_ast_dict[key] = [pts_dict[key], reb_dict[key]]
            if key in ast_dict.keys() and key not in reb_dict.keys():
                pts_reb_ast_dict[key] = [pts_dict[key], ast_dict[key]]
        if len(pts_reb_ast_dict.keys()) != 0:
            top_stat_players[season] = pts_reb_ast_dict

    with open('top_stat_players.json', 'w') as f:
        json.dump(top_stat_players, f)


def get_yearly_all_stars(seasons, all_stars):
    yearly_all_stars = {season:[] for season in seasons}
    for all_star in all_stars:
        split1 = all_star[1].split(';')
        for year in split1:
            split2 = year.split('–')
            # all star seasons are given by year of all star game
            if len(split2) == 1:
                all_star_seasons = generate_seasons(int(split2[0])-1, int(split2[0])-1)
            else:
                all_star_seasons = generate_seasons(int(split2[0])-1, int(split2[1])-1)
            for season in all_star_seasons:
                yearly_all_stars[season].append(all_star[0])
    return yearly_all_stars


def results_to_csv(top_stat_all_stars):
    with open('stat_leader_all_stars.csv', mode='w', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['Year', 'Player', 'PTS', 'Stat', 'PTS Rank', 'Stat 2 Value', 'Stat 2', 'Stat 2 Rank', 'Stat 3 Value', 'Stat 3', 'Stat 3 Rank'])
        for year, player_dict in top_stat_all_stars.items():
            year_first_row = True
            for player, stats in player_dict.items():
                if year_first_row:
                    writer.writerow([year, player] + [item for stat_list in stats for item in stat_list])
                else:
                    writer.writerow(['', player] + [item for stat_list in stats for item in stat_list])
                year_first_row = False


def main():

    first_season = 1950
    last_season = 2019
    seasons = generate_seasons(first_season, last_season)
    top_x = 5
    player_param = 'PLAYER'
    rank_param = 'RANK'

    # get_pts_reb_ast_leaders(seasons, top_x, player_param, rank_param)

    with open('top_stat_players.json') as f:
        top_stat_players = json.load(f)

    with open('all_stars.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',')
        next(reader)
        all_stars = [row for row in reader]

    wiki_chars = '[\^\*†§,]|\[[a-z]\]|(\\xa0)'
    clean_all_stars = [ [re.sub(wiki_chars, '', all_star[0]), re.sub(wiki_chars, '', all_star[1])]
                        for all_star in all_stars ]
    cleaner_all_stars = [ [unicodedata.normalize('NFD', all_star[0]).encode('ascii', 'ignore').decode('utf-8'),
                           all_star[1]]
                          for all_star in clean_all_stars ]

    # test_re = '^[a-zA-Z_]+$'
    # test_re = '\W'
    # test_str = 'Nikola Vučevićç'
    # test_str2 = 'Nikola Vucevic'
    # test = re.match(test_re, test_str, re.ASCII)
    # test2 = re.match(test_re, test_str2)
    # pp.pprint(test == True)
    # pp.pprint(test2 == True)
    # pp.pprint(cleaner_all_stars)

    yearly_all_stars = get_yearly_all_stars(seasons, cleaner_all_stars)

    # test_str = '1970-1977;1979-1989'
    # test_str2 = '1971'
    # test_str3 = '1970-1977;1921'
    # split1 = test_str.split(';')
    # print(test_str2.split(';'))
    # print(split1[0].split('-'))
    # pp.pprint(generate_seasons(1970, 1970))
    # test_dict = {'1970-71': [], '1971-72': []}
    # test_dict['1970-71'].append(1)
    # test_dict['1970-71'].append(2)
    # pp.pprint(test_dict)

    top_stat_all_stars = {}
    top_stat_not_all_stars = {}
    for year, player_dict in top_stat_players.items():
        top_stat_all_star_dict = {}
        top_stat_not_all_star_dict = {}
        for player, stats in player_dict.items():
            if player in yearly_all_stars[year]:
                top_stat_all_star_dict[player] = stats
            else:
                top_stat_not_all_star_dict[player] = stats
        top_stat_all_stars[year] = top_stat_all_star_dict
        top_stat_not_all_stars[year] = top_stat_not_all_star_dict
    print('top stat and all stars')
    pp.pprint(top_stat_all_stars)
    print('top stat not all star')
    pp.pprint(top_stat_not_all_stars)

    top_stat_player_count = 0
    for year, player_dict in top_stat_players.items():
        top_stat_player_count += len(player_dict.keys())
    print('top stat players:', top_stat_player_count)

    print('top 3 stat players:')
    for year, player_dict in top_stat_players.items():
        for player_key, player_stats in player_dict.items():
            if len(player_stats) == 3:
                print(year, player_key, player_stats)
    # results_to_csv(top_stat_all_stars)
    pp.pprint(len(top_stat_not_all_stars.keys()))


if __name__ == '__main__':
    main()
