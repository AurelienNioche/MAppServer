import numpy as np
import copy

from pymdp.agent import Agent
from pymdp import utils
from pymdp.envs import TMazeEnvNullOutcome

reward_probabilities = [0.85, 0.15]  # the 'true' reward probabilities
env = TMazeEnvNullOutcome(reward_probs=reward_probabilities)
A_gp = env.get_likelihood_dist()
B_gp = env.get_transition_dist()
pA = utils.dirichlet_like(A_gp, scale=1e16)
pA[1][1:, 1:3, :] = 1.0
A_gm = utils.norm_dist_obj_arr(pA)
B_gm = copy.deepcopy(B_gp)

controllable_indices = [0]   # this is a list of the indices of the hidden state factors that are controllable
learnable_modalities = [1]   # this is a list of the modalities that you want to be learn-able

agent = Agent(
    A=A_gm, pA=pA, B=B_gm,
    control_fac_idx=controllable_indices,
    modalities_to_learn=learnable_modalities,
    lr_pA=0.25,
    use_param_info_gain=True)

agent.D[0] = utils.onehot(0, agent.num_states[0])
agent.C[1][1] = 2.0
agent.C[1][2] = -2.0

print(agent.D)
print(agent.C)


T = 1  # number of timesteps

obs = env.reset()  # reset the environment and get an initial observation

# these are useful for displaying read-outs during the loop over time
reward_conditions = ["Right Arm Better", "Left arm Better"]
location_observations = ['CENTER', 'RIGHT ARM', 'LEFT ARM', 'CUE LOCATION']
reward_observations = ['No reward', 'Reward!', 'Loss!']
cue_observations = ['Null', 'Cue Right', 'Cue Left']
msg = """ === Starting experiment === \n Reward condition: {}, Observation: [{}, {}, {}]"""
print(msg.format(reward_conditions[env.reward_condition], location_observations[obs[0]], reward_observations[obs[1]], cue_observations[obs[2]]))

pA_history = []

all_actions = np.zeros((T, 2))
for t in range(T):

    print(f"t = {t}")
    print("*" * 50)

    qx = agent.infer_states(obs)

    print(f"qx = {qx}")

    q_pi, efe = agent.infer_policies()

    action = agent.sample_action()

    pA_t = agent.update_A(obs)
    pA_history.append(pA_t)

    msg = """[Step {}] Action: [Move to {}]"""
    print(msg.format(t, location_observations[int(action[0])]))

    obs = env.step(action)

    all_actions[t, :] = action

    msg = """[Step {}] Observation: [{},  {}, {}]"""
    print(msg.format(t, location_observations[int(obs[0])], reward_observations[int(obs[1])], cue_observations[int(obs[2])]))


