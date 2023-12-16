import pandas as pd
import numpy as np

from utils.data_export import export_data
from utils.data_processor import export_osu_to_parquet
from utils.winning_chance import process_winning_chance
from utils.skillbans import winning_chances_to_elo, skillbans

# export_data()
# dataset = pd.read_parquet('dataset/scores.parquet')
# beatmaps = pd.read_parquet('dataset/beatmaps.parquet')

# ball = pd.read_csv('ball.csv', header=None)
# filtered = dataset[dataset['beatmap_id'].isin(ball[4].values)]
# winning_chances = process_winning_chance(filtered, beatmaps[beatmaps['beatmap_id'].isin(ball[4].values)])
# winning_chances.to_parquet('dataset/winning_chances.parquet')

# export_osu_to_parquet("select user_id, username from sample_users", 'dataset/users.parquet')

winning_chances = pd.read_parquet('dataset/winning_chances.parquet')
rank = pd.read_parquet('dataset/pp_4k.parquet')

elo = winning_chances_to_elo(winning_chances)
elo.to_csv('elo.csv')

skillbans_result = skillbans(elo, rank)
skillbans_result.skillbanned.to_csv('skillbans.csv')
print(skillbans_result.threshold)

