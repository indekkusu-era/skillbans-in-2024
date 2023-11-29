import numpy as np
from .constants import elo_constant

def grad(xi, xj, pij):
    p_hat = 1 / (1 + np.exp((xj - xi) * elo_constant))
    diff = pij - p_hat
    return diff

def elo(data, x0, gamma=0.9995, eps=1e-2):
    max_iterations = int(np.ceil(np.log(eps * (1 - gamma)) / np.log(gamma))) # proof: upper bound elo by geometric series
    print(f"{max_iterations = }")
    n_games = np.zeros(len(x0))
    multipiler = np.ones(len(x0))
    x = x0
    while True:
        if np.all(n_games >= max_iterations):
            break
        current_iterations = np.min(n_games)
        print(f"{current_iterations = }")
        np.random.shuffle(data)
        for i, j, pij in data:
            xi = x[int(i)]
            xj = x[int(j)]
            df = grad(xi, xj, pij)
            x[int(i)] += df * multipiler[int(i)]
            x[int(j)] -= df * multipiler[int(j)]
            n_games[int(i)] += 1
            n_games[int(j)] += 1
            multipiler[int(i)] *= gamma
            multipiler[int(j)] *= gamma
    return x

__all__ = ['elo']
