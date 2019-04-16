# """
# Runs libEnsemble on the 6-hump camel problem. Documented here:
#    https://www.sfu.ca/~ssurjano/camel6.html
#
# Execute via the following command:
#    mpiexec -np 4 python3 test_6-hump_camel_uniform_sampling.py
# The number of concurrent evaluations of the objective function will be 4-1=3.
# """
import numpy as np


# Import libEnsemble main, sim_specs, gen_specs, and persis_info
from libensemble.libE import libE
from libensemble.sim_funcs.six_hump_camel import six_hump_camel as sim_f 
from libensemble.alloc_funcs.give_pregenerated_work import give_pregenerated_sim_work as alloc_f
from libensemble.tests.regression_tests.common import parse_args, save_libE_output

# Parse args for test code
nworkers, is_master, libE_specs, _ = parse_args()

sim_specs = {'sim_f': sim_f, 'in': ['x'], 'out': [('f',float)]}

gen_specs = {}

H0 = np.zeros(100,dtype=[('x',float,2)])
np.random.seed(0)
H0['x'] = np.random.uniform(0,1,(100,2))

alloc_specs = {'alloc_f':alloc_f, 'out': [('x',float,2)]}

exit_criteria = {'sim_max': len(H0)}
# Perform the run
H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, alloc_specs=alloc_specs, libE_specs=libE_specs, H0=H0)

if is_master:
    assert len(H) == len(H0)
    print("\nlibEnsemble with Uniform random sampling didn't add anything to initial sample")
    save_libE_output(H,__file__,nworkers)
