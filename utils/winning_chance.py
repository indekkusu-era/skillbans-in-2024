import pandas as pd
import numpy as np
from tqdm import tqdm

def calculate_winning_chance(player1, player2, pivot, rc, ln):
    win_mask = ~(pivot[player1].isna() | pivot[player2].isna())
    rc_subset = rc[player1][win_mask]
    ln_subset = ln[player1][win_mask]
    win_values = (pivot[player1] > pivot[player2]).astype(float) + 0.5 * (pivot[player1] == pivot[player2]).astype(float)

    # Precompute total values
    ttl_rice = rc_subset.sum()
    ttl_ln = ln_subset.sum()

    total = 0
    div = 0

    if ttl_rice > 0:
        total += (win_values[win_mask] * rc_subset).sum() / ttl_rice
        div += 1

    if ttl_ln > 0:
        total += (win_values[win_mask] * ln_subset).sum() / ttl_ln
        div += 1

    if div == 0:
        return np.nan

    return total / div

def process_winning_chance(dataset, beatmaps):
    pivot = dataset.pivot(index='beatmap_id', columns='user_id', values='score')
    users = pivot.columns
    beatmaps.index = beatmaps['beatmap_id']
    beatmaps['RC_ratio'] = beatmaps['RC'] / (beatmaps['RC'] + beatmaps['LN'])
    beatmaps['LN_ratio'] = 1 - beatmaps['RC_ratio']
    rc = beatmaps[['RC_ratio']].values
    rc =  pd.DataFrame(rc.repeat(len(pivot.columns), axis=1), columns=pivot.columns, index=pivot.index)
    ln = beatmaps[['LN_ratio']].values
    ln =  pd.DataFrame(ln.repeat(len(pivot.columns), axis=1), columns=pivot.columns, index=pivot.index)
    mat = np.zeros((len(users), len(users))) * np.nan

    for i, player1 in tqdm(enumerate(users)):
        for j, player2 in enumerate(users):
            if i == j: 
                mat[i,j] = 0.5
                continue
            if i > j:
                mat[i,j] = 1 - mat[j,i]
                continue
            chance = calculate_winning_chance(player1, player2, pivot, rc, ln)
            mat[i, j] = chance
    winning_chances = pd.DataFrame(mat, index=users, columns=users)
    return winning_chances.loc[~winning_chances.index.duplicated(),~winning_chances.columns.duplicated()].copy()
