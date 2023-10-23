import numpy as np
import pandas as pd
import cvxpy as cp
from gglasso.problem import glasso_problem

def covariances(dataset: pd.DataFrame):
    return dataset.cov().dropna(how='all').dropna(how='all', axis=1).fillna(0)

def estimate_covariances(covariances: np.ndarray):
    n = len(covariances)
    X = cp.Variable((n,n), symmetric=True)
    objective = cp.Minimize(cp.norm(covariances - X, 'fro'))
    constraints = [X >> 0]
    problem = cp.Problem(objective, constraints)

    # Solve the problem
    problem.solve()

    # The optimal solution is stored in X.value
    optimal_X = X.value
    return optimal_X

def graphical_lasso(covariances_estimated: np.ndarray, n_samples: int, model_select_params={'lambda1_range': np.logspace(0, -2, 5)}, gamma=0.5):
    P = glasso_problem(covariances_estimated, n_samples, latent=False, do_scaling=False)
    P.model_selection(modelselect_params=model_select_params, method='eBIC', gamma=gamma)
    return P

__all__ = ['covariances', 'estimate_covariances', 'graphical_lasso']
