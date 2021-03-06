from typing import List, Union, Dict

import pyemma as pm
import numpy as np
from glob import glob
from pyemma import config 
from multiprocessing import Pool, current_process, cpu_count
from rich.progress import Progress


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


# This is not a great name for this function...
def do_bootstrap(args):
    traj_paths, hps, lags, nits = args
    trajs = get_features(traj_paths)
    sampled_trajs = sample_trajectories(trajs)
    dtrajs = discretize_trajectories(hps, sampled_trajs)
    its = pm.msm.its(dtrajs, lags=lags, nits=nits)
    return its.timescales


def bootstrap_ts2(n: int, hps: Dict[str, Dict[str, int]], traj_paths: List[str], lags: np.ndarray) -> np.ndarray:
    nits = 5
    n_workers = cpu_count()
    with Pool(n_workers) as pool:
        args_list = [(traj_paths, hps, lags, nits)]*int(n)
        result = pool.map(do_bootstrap, args_list)
        
    shape = result[0].shape 
    all_its = []
    for i in range(n):
        try:
            all_its.append(result[i].reshape(1, *shape))
        except ValueError:
            pass
    all_its = np.concatenate(all_its, axis=0)
    return all_its
        
    
def do_vamp(args):
    traj_paths, hps, lag, vamp_k = args
    trajs = get_features(traj_paths)
    sampled_trajs = sample_trajectories(trajs)
    dtrajs = discretize_trajectories(hps, sampled_trajs)
    mm = pm.msm.estimate_markov_model(dtrajs, lag)
    score = mm.score(dtrajs, score_k=vamp_k, score_method='vamp2')
    return score

    
def bootstrap_vamp(n: int, hps: Dict[str, Dict[str, int]], traj_paths: List[str], vamp_k: int, lag: int) -> np.ndarray:
    n_workers = cpu_count()
    args_list = [(traj_paths, hps, lag, vamp_k)]*int(n)
    results = []
    with Pool(n_workers) as pool:
        results = list(pool.imap_unordered(do_vamp, args_list))
#         with Progress() as progress:
#             task = progress.add_task('[blue] Bootstrapping VAMP...', total=n)
#             for i, result in enumerate(pool.imap_unordered(do_vamp, args_list)):
#                 progress.update(task, advance=1)
#                 results.append(result)
    return results


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
    
