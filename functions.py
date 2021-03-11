from typing import List, Union, Dict

import pyemma as pm
import numpy as np
from glob import glob
from pyemma import config 

config.show_progress_bars = False 


def get_probabilities(trajs: List[np.ndarray]) -> np.ndarray:
    lengths = np.array([x.shape[0] for x in trajs])
    probs = lengths/np.sum(lengths)
    return probs


def sample_trajectories(trajs: List[np.ndarray])-> List[np.ndarray]:
    ix = np.arange(len(trajs))
    probs = get_probabilities(trajs)
    sample_ix = np.random.choice(ix, size=ix.shape[0], p=probs, replace=True)
    sampled_trajs = [trajs[i] for i in sample_ix]
    return sampled_trajs


def bootstrap_ts2(n: int, hps: Dict[str, Dict[str, int]], trajs: List[np.ndarray], lags: np.ndarray) -> np.ndarray:
    nits = 5
    all_its = np.empty((n, lags.shape[0], nits))
    for i in range(n):
#         print(i, end=', ')
        sampled_trajs = sample_trajectories(trajs)
        dtrajs = discretize_trajectories(hps, sampled_trajs)
        its = pm.msm.its(dtrajs, lags=lags, nits=nits)
        all_its[i, :, :] = its.timescales
    return all_its
        

def get_feature_traj_paths(sim_name: str, feature: str) -> List[str]:
    return glob(f"{sim_name}/features/{feature}/*.npy")


def get_features(paths: List[str]) -> List[np.ndarray]:
    return [np.load(x) for x in paths]


def sample_hyperparameters(search_space: Dict[str, Dict[str, List[int]]]) -> Dict[str, Dict[str, int]]:
    hps = {}
    for module, kw_args_range in search_space.items(): 
        kw_args = {}
        for keyword, val_range in kw_args_range.items():
            if isinstance(val_range, list):
                vmin, vmax = val_range
                val = np.random.choice(range(vmin, vmax+1))
            else:
                val = val_range
            kw_args[keyword] = int(val)      
        hps[module] = kw_args
    return hps


def discretize_trajectories(hyperparameters: Dict[str, Dict[str, int]], trajs: List[np.ndarray]) -> List[np.ndarray]:

    vamp = pm.coordinates.vamp(trajs, **hyperparameters['vamp'])
    y = vamp.get_output()
    kmeans = pm.coordinates.cluster_kmeans(y, **hyperparameters['cluster_kmeans'])
    z = kmeans.dtrajs
    z = [x.flatten() for x in z]
    return z
    
