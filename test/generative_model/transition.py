import numpy as np

def compute_position_transition_matrix(position, velocity, sigma_transition_position):
    # position = np.linspace(0, np.max(sum_steps)*1.2, 30)
    # Compute position transition matrix
    sigma_transition_position = 10.0
    tr = np.zeros((position.size, velocity.size, position.size))
    for p_idx, p in enumerate(position):
        for v_idx, v in enumerate(velocity):
            dist = stats.norm.pdf(position, loc=p + v, scale=sigma_transition_position)
            if np.sum(dist) == 0:
                if p + v < 0:
                    dist[0] = 1
                elif p + v > position[-1]:
                    dist[-1] = 1 # All weight on greatest position
                else:
                    print(f"bounds: {position[0]}, {position[-1]}")
                    print(f"p+v: {p+v}")
                    raise ValueError("This should not happen, try increasing 'sigma_transition_position'")
            tr[p_idx, v_idx, :] = dist

    transition_position_pvp = normalize_last_dim(tr)

    # Make sure that all probabilities sum to (more or less) one
    np.allclose(np.sum(transition_position_pvp, axis=-1), 1)