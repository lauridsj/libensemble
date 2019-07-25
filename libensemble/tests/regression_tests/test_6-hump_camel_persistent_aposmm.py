# """
# Runs libEnsemble on the 6-hump camel problem. Documented here:
#    https://www.sfu.ca/~ssurjano/camel6.html
#
# Execute via one of the following commands (e.g. 3 workers):
#    mpiexec -np 4 python3 test_6-hump_camel_persistent_uniform_sampling.py
#    python3 test_6-hump_camel_persistent_uniform_sampling.py --nworkers 3 --comms local
#    python3 test_6-hump_camel_persistent_uniform_sampling.py --nworkers 3 --comms tcp
#
# The number of concurrent evaluations of the objective function will be 4-1=3.
# """

# Do not change these lines - they are parsed by run-tests.sh
# TESTSUITE_COMMS: mpi local tcp
# TESTSUITE_NPROCS: 3 4

import sys
import numpy as np

# Import libEnsemble items for this test
from libensemble.libE import libE
from libensemble.sim_funcs.six_hump_camel import six_hump_camel as sim_f
from libensemble.gen_funcs.persistent_aposmm import aposmm as gen_f
from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens as alloc_f
from libensemble.tests.regression_tests.common import parse_args, save_libE_output, per_worker_stream

nworkers, is_master, libE_specs, _ = parse_args()

if nworkers < 2:
    sys.exit("Cannot run with a persistent worker if only one worker -- aborting...")

n = 2
sim_specs = {'sim_f': sim_f,
             'in': ['x'],
             'out': [('f', float), ('grad', float, n)]}

gen_out = [('x', float, n), ('x_on_cube', float, n), ('sim_id', int)]
gen_specs = {'gen_f': gen_f,
             'in': [],
             'out': gen_out,
             'batch_mode': True,
             'initial_sample_size': 50,
             'localopt_method': 'LD_MMA',
             'xtol_rel': 1e-3,
             'max_active_runs': 1,
             'lb': np.array([-3, -2]),
             'ub': np.array([3, 2])}

alloc_specs = {'alloc_f': alloc_f, 'out': [('given_back',bool)]}

persis_info = per_worker_stream({}, nworkers + 1)

exit_criteria = {'sim_max': 400}

# Perform the run
H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, persis_info,
                            alloc_specs, libE_specs)

if is_master:
    save_libE_output(H, persis_info, __file__, nworkers)
