import numpy as np
from pymdp.agent import Agent
from pymdp.utils import plot_beliefs, plot_likelihood
from pymdp import utils
from pymdp.envs import TMazeEnv
import copy

reward_probabilities = [0.98, 0.02] #
env = TMazeEnv(reward_probs=reward_probabilities)# probabilities used in the original SPM T

A_gp = env.get_likelihood_dist()
B_gp = env.get_transition_dist()

A_gm = copy.deepcopy(A_gp) # make a copy of the true observation likelihood to initialize the observation model
B_gm = copy.deepcopy(B_gp) # make a copy of the true transition likelihood to initialize the transition

agent = Agent(A=A_gm, B=B_gm, control_fac_idx=[0,])
agent.D[0] = utils.onehot(0, agent.num_states[0])
agent.C[1][1] = 3.0
agent.C[1][2] = -3.0

T = 2  # number of timesteps

obs = env.reset()  # reset the environment and get an initial observation

# these are useful for displaying read-outs during the loop over time
reward_conditions = ["Right", "Left"]
location_observations = ['CENTER','RIGHT ARM','LEFT ARM','CUE LOCATION']
reward_observations = ['No reward','Reward!','Loss!']
cue_observations = ['Cue Right','Cue Left']

msg = """ === Starting experiment === \n Reward condition: {}, Observation: [{}, {}, {}]"""
print(msg.format(reward_conditions[env.reward_condition], location_observations[obs[0]], reward_observations[obs[1]], cue_observations[obs[2]]))

for t in range(T):
    qx = agent.infer_states(obs)

    q_pi, efe = agent.infer_policies()
    print(f"efe{efe}")

    action = agent.sample_action()

    msg = """[Step {}] Action: [Move to {}]"""
    print(msg.format(t, location_observations[int(action[0])]))

    obs = env.step(action)

    msg = """[Step {}] Observation: [{},  {}, {}]"""
    print(msg.format(t, location_observations[obs[0]], reward_observations[obs[1]], cue_observations[obs[2]]))
