reinitialize
load /Users/robertarbon/Documents/Research/Mal_L_MMRT/Analysis/reactant/top-374-459.pdb, traj
load_traj /Users/robertarbon/Documents/Research/Mal_L_MMRT/Analysis/reactant/aligned/run_10_470-520ns.xtc, traj, state=1, interval=10
smooth traj, 30, 2
movie.produce /Users/robertarbon/Documents/Research/Mal_L_MMRT/Analysis/reactant/animations/run_10_470-520ns.mpg, quality=75

