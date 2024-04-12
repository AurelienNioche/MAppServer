import numpy as np
from sklearn.mixture import GaussianMixture
import warnings

import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

from . transformers import StepTransformer, ParamTransformer


def sample_child_model(model, step_transformer, n_steps, timestep):

    # Generate the steps for the day with the fitted model
    samples_alpha, _ = model.sample(n_samples=n_steps)

    # Inverse-transform the steps
    step_events_day = step_transformer.inverse_transform(samples_alpha).flatten()

    # Compute the cumulative steps and the derivative of the cumulative steps to get the activity
    cum_steps_day = np.sum(step_events_day <= timestep[:, None], axis=1)
    deriv_cum_steps_day = np.gradient(cum_steps_day, timestep + 1) / (timestep.size - 1)
    return deriv_cum_steps_day


def sample_parent_model(
        model,
        transforms,
        n_samples,  # This will be number of days that will be generated
        seed=12345
) -> list[np.ndarray]:

    # Unpack the transforms
    step_transformer = transforms["step_transformer"]
    params_transformer = transforms["params_transformer"]
    features_transformer = transforms["features_transformer"]

    # Set the seed
    np.random.seed(seed)

    # Generate the features of the child models
    # (the parameters of the GMMs, and the number of samples to draw from them)
    transformed_features, _ = model.sample(n_samples=n_samples)

    step_events = []

    for day in range(n_samples):

        # Choose with type of model to use ---------------------------

        # Using the alpha-model, draw a model type for model-gamma according to the goodness of fit scores

        # Un-transform the features
        x = transformed_features[day].reshape(1, -1)
        un_standardised_feat = features_transformer.inverse_transform(x).flatten()
        # Get back the GMM parameters by inverse-transforming the features
        params = params_transformer.inverse_transform(un_standardised_feat)

        # Set up the gamma-model
        n_components = params["n_components"]
        gmm = GaussianMixture(n_components=n_components)
        gmm.means_ = params["means"].reshape(-1, 1)
        gmm.covariances_ = params["variances"].reshape(-1, 1, 1)
        gmm.weights_ = params["weights"]

        # Get the number of samples to draw (= number of steps)
        n = params["n"]

        # Generate the (transformed) steps (ignore the 'covariance is not symmetric positive-semidefinite.' warning)
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        samples_alpha, _ = gmm.sample(n_samples=n)
        warnings.filterwarnings("default", category=RuntimeWarning)

        # Inverse-transform the steps
        step_events_day = step_transformer.inverse_transform(samples_alpha).flatten()

        step_events.append(step_events_day)

    return step_events


def sample(*args, **kwargs):
    """
    Alias for sample_parent_model
    """
    return sample_parent_model(*args, **kwargs)

