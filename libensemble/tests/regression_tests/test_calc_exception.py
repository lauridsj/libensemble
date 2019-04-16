import sys, os             # for adding to path
import numpy as np

from libensemble.libE import libE
from libensemble.libE_manager import ManagerException
from libensemble.gen_funcs.uniform_sampling import uniform_random_sample as gen_f
from libensemble.tests.regression_tests.common import parse_args, give_each_worker_own_stream

# Parse args for test code
nworkers, is_master, libE_specs, _ = parse_args()

# Define sim_func
def six_hump_camel_err(H, persis_info, sim_specs, _):
    raise Exception('Deliberate error')


sim_specs = {'sim_f': six_hump_camel_err, 'in': ['x'], 'out': [('f',float),]}
gen_specs = {'gen_f': gen_f, 
        'in': ['sim_id'],
        'out': [('x',float,2)],
        'lb': np.array([-3,-2]),
        'ub': np.array([ 3, 2]),
        'gen_batch_size': 10,
        }

persis_info = give_each_worker_own_stream({},nworkers+1)

# Tell libEnsemble when to stop
exit_criteria = {'elapsed_wallclock_time': 10}

libE_specs['abort_on_exception'] = False

# Perform the run
return_flag = 1
try:
    H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, persis_info, libE_specs=libE_specs)
except ManagerException as e:
    print("Caught deliberate exception: {}".format(e))
    return_flag = 0

if is_master:
    assert return_flag == 0
