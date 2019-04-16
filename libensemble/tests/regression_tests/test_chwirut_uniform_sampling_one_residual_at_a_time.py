# """
# Runs libEnsemble with a simple uniform random sample on one instance of the GKLS
# problem. # Execute via the following command:

# mpiexec -np 4 python3 test_chwirut_uniform_sampling_one_residual_at_a_time.py

# """
import numpy as np
from copy import deepcopy

# Import libEnsemble items
from libensemble.libE import libE
from libensemble.sim_funcs.chwirut1 import chwirut_eval as sim_f
from libensemble.gen_funcs.uniform_sampling import uniform_random_sample_obj_components as gen_f
from libensemble.alloc_funcs.fast_alloc_and_pausing import give_sim_work_first as alloc_f
from libensemble.tests.regression_tests.support import persis_info_3 as persis_info
from libensemble.tests.regression_tests.common import parse_args, save_libE_output, give_each_worker_own_stream

# Parse args for test code
nworkers, is_master, libE_specs, _ = parse_args()
if libE_specs['comms'] != 'mpi':
    quit()

### Declare the run parameters/functions
m = 214
n = 3
max_sim_budget = 10*m

sim_specs = {'sim_f': sim_f,
             'in': ['x', 'obj_component'],
             'out': [('f_i',float)],
           'component_nan_frequency': 0.01,
             }

gen_specs = {'gen_f': gen_f,
             'in': ['pt_id'],
             'out': [('x',float,n),
                 ('priority',float),
                      ('paused',bool),
                      ('obj_component',int),
                      ('pt_id',int),],
             'gen_batch_size': 2,
             'single_component_at_a_time': True,
             'combine_component_func': lambda x: np.sum(np.power(x,2)),
             'num_active_gens': 1,
             'batch_mode': True,
             'lb': (-2-np.pi/10)*np.ones(n), # Trying to avoid exactly having x[1]=-x[2] from being hit, which results in division by zero in chwirut. 
             'ub':  2*np.ones(n),
             'components': m,
             }

alloc_specs = { 'alloc_f':alloc_f,
        'out':[('allocated',bool)], 
               'stop_on_NaNs': True,
               'stop_partial_fvec_eval': True,
               }

persis_info = give_each_worker_own_stream(persis_info,nworkers+1)
persis_info_safe = deepcopy(persis_info)

exit_criteria = {'sim_max': max_sim_budget, 'elapsed_wallclock_time': 300}

# Perform the run
H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, persis_info, alloc_specs, libE_specs)
if is_master:
    assert flag == 0
    save_libE_output(H,__file__,nworkers)

# Perform the run but not stopping on NaNs
alloc_specs.pop('stop_on_NaNs')
persis_info = deepcopy(persis_info_safe) 
H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, persis_info, alloc_specs, libE_specs)
if is_master:
    assert flag == 0

# Perform the run also not stopping on partial fvec evals
alloc_specs.pop('stop_partial_fvec_eval')
persis_info = deepcopy(persis_info_safe) 
H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, persis_info, alloc_specs, libE_specs)
if is_master:
    assert flag == 0
