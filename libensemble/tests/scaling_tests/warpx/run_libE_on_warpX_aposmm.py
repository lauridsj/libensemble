#!/usr/bin/env python
# """
# Execute via one of the following commands:
#    mpiexec -np 4 python run_libE_on_warpX.py
#    python run_libE_on_warpX_aposmm.py --comms local --nworkers 3

# The number of concurrent evaluations of the objective function will be 4-2=2
# as one MPI rank for the manager and one MPI rank for the persistent gen_f.
# """

import numpy as np
from warpX_simf import run_warpX  # Sim func from current dir

# Import libEnsemble modules
from libensemble.libE import libE

import libensemble.gen_funcs
libensemble.gen_funcs.rc.aposmm_optimizer = 'nlopt'
from libensemble.gen_funcs.persistent_aposmm import aposmm as gen_f

from libensemble.alloc_funcs.persistent_aposmm_alloc import persistent_aposmm_alloc as alloc_f
from libensemble.tools import parse_args, save_libE_output, add_unique_random_streams
from libensemble import libE_logger
from libensemble.executors.mpi_executor import MPIExecutor

from Summit import machine_specs

libE_logger.set_level('INFO')

nworkers, is_master, libE_specs, _ = parse_args()

# Set to full path of warp executable
sim_app = machine_specs['sim_app']

n = 4  # Problem dimension
exctr = MPIExecutor(central_mode=True)
exctr.register_calc(full_path=sim_app, calc_type='sim')

# State the objective function, its arguments, output, and necessary parameters (and their sizes)
sim_specs = {'sim_f': run_warpX,           # Function whose output is being minimized
             'in': ['x'],                  # Name of input for sim_f
             'out': [('f', float),   # Optimize on this.
                     ('energy_std', float, (1,)),
                     ('energy_avg', float, (1,)),
                     ('charge', float, (1,)),
                     ('emittance', float, (1,)),
                     ('ramp_down_1', float, (1,)),
                     ('ramp_down_2', float, (1,)),
                     ('zlens_1', float, (1,)),
                     ('adjust_factor', float, (1,)),
                 ],
             'user': {'nodes': machine_specs['nodes'],
                      'ranks_per_node': machine_specs['ranks_per_node'],
                      'input_filename': 'inputs',
                      'sim_kill_minutes': 10.0,
                      'dummy': False}  # Timeout for sim ....
             }

gen_out = [('x', float, (n,)), ('x_on_cube', float, (n,)), ('sim_id', int),
           ('local_min', bool), ('local_pt', bool)]

# State the generating function, its arguments, output, and necessary parameters.
gen_specs = {'gen_f': gen_f,                  # Generator function
             'in': [],                        # Generator input
             'out': gen_out,
             'user': {'initial_sample_size': 4,
                      'localopt_method': 'LN_BOBYQA',
                      'num_pts_first_pass': nworkers,
                      'xtol_rel': 1e-3,
                      'ftol_abs': 3e-8,
                      'lb': np.array([2.e-3, 2.e-3, 0.005, .1]),  # Lower bound for the n parameters
                      'ub': np.array([2.e-2, 2.e-2, 0.028, 3.]), # Upper bound for the n parameters
                      }
             }

alloc_specs = {'alloc_f': alloc_f, 'out': [('given_back', bool)], 'user': {}}

libE_specs['save_every_k_sims'] = 100   # Save H to file every N simulation evaluations
libE_specs['sim_input_dir'] = 'sim'     # Sim dir to be copied for each worker

# Maximum number of simulations
sim_max = 400
exit_criteria = {'sim_max': sim_max}

# Create a different random number stream for each worker and the manager
persis_info = add_unique_random_streams({}, nworkers + 1)

# # Showing how, if you had a past set of points that you wanted to give to
# # libE/APOSMM, it can be done in the following fashion:
# num_old_pts = 100

# H0 = np.zeros(num_old_pts, dtype=[('x', float, n),         
#                                   ('x_on_cube', float, n),   
#                                   ('sim_id', int),
#                                   ('local_min', bool),
#                                   ('local_pt', bool),
#                                   ('given_back', bool), 
#                                   ('f', float), 
#                                   ('returned', bool),
#                                   ('given', bool)
#                                   ])

# # Previously evaluated points
# H0['x'] = np.random.uniform(0,1,(num_old_pts, n))
# H0['x_on_cube'] = (H0['x']-gen_specs['user']['lb']) / (gen_specs['user']['ub']-gen_specs['user']['lb'])

# # Numbering them 
# H0['sim_id'] = range(num_old_pts)

# # Are these points all sample points or localopt points? Are any known minima?
# H0['local_pt'] = False  
# H0['local_min'] = False  

# # Let libE know these points have been 'given' to be evaluated and 'returned'.
# # Let allocation function know they've been 'given_back' to APOSMM.
# H0[['given', 'given_back', 'returned']] = True

# # The values should already exist
# for i in range(num_old_pts):
#     H0['f'][i] = six_hump_camel_func(H0['x'][i])
# # And then call with H0
# H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria,
#                             persis_info, alloc_specs, libE_specs, H0)


H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria,
                            persis_info, alloc_specs, libE_specs)
print( persis_info[1]['run_order'] )

# Save results to numpy file
if is_master:
    save_libE_output(H, persis_info, __file__, nworkers)
