import warnings
import numpy as np
from sklearn.mixture import GaussianMixture

from test.generative_model.transformers import StepTransformer, ParamTransformer
from sklearn.preprocessing import StandardScaler as FeaturesTransformer


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
        model: GaussianMixture,
        transforms: dict[str, StepTransformer or ParamTransformer or FeaturesTransformer],
        n_samples: int,  # This will be number of days that will be generated
) -> list[np.ndarray]:
    # Unpack the transforms
    step_transformer = transforms["step_transformer"]
    params_transformer = transforms["params_transformer"]
    features_transformer = transforms["features_transformer"]
    # Generate the features of the child models
    # (the parameters of the GMMs, and the number of samples to draw from them)
    transformed_features, _ = model.sample(n_samples=n_samples)
    # Initialize the list of steps
    step_events = []
    # Generate the steps for each day
    for day in range(n_samples):
        # print("day", day, "-" * 50)
        # Un-transform the features
        x = transformed_features[day].reshape(1, -1)
        un_standardised_feat = features_transformer.inverse_transform(x).flatten()
        # Get back the GMM parameters by inverse-transforming the features
        params = params_transformer.inverse_transform(un_standardised_feat)
        # Set up the gamma-model
        n_components = params["n_components"]
        n_steps = params["n"]
        means = params["means"]
        variances = params["variances"]
        weights = params["weights"]
        # print("-" * 50)
        # print("Sample parent model")
        # print("n_components", n_components)
        # print("means", means)
        # print("variances", variances)
        # print("weights", weights)
        # print("n_steps", n_steps)
        # print("-" * 50)
        # print("trial", trial)
        rng = np.random.default_rng(day)   #  + trial*1000)
        dist_to_draw_from = rng.choice(np.arange(n_components), size=n_steps, p=weights)
        # print("dist_to_draw_from", dist_to_draw_from)

        # Count the occurrences of each value in the preset list
        counts = [np.count_nonzero(dist_to_draw_from == value) for value in np.arange(n_components)]

        samples = []
        for c in range(n_components):
            # print("counts", counts[c])
            smp = rng.normal(loc=means[c], scale=variances[c], size=counts[c])
            # print("c", c, "smp", smp)
            samples.append(smp)
        # print("samples before concat", samples)
        samples = np.concatenate(samples)
        # print("samples shape", samples.shape)
        # print("samples size", samples.size)
        # print("samples", samples)
        # gmm = GaussianMixture(
        #     n_components=n_components,
        #     random_state=day + trial*1000,
        #     means_init=params["means"].reshape(-1, 1),
        #     precisions_init=(1/params["variances"]).reshape(-1, 1, 1),
        #     weights_init=params["weights"]
        # )
        # gmm.fit(np.empty(1).reshape(-1, 1))
        # gmm.means_ = np.ones(1).reshape(-1, 1)
        # params["means"].reshape(-1, 1)
        # print("means", gmm.means_)
        # gmm.covariances_ = params["variances"].reshape(-1, 1, 1)
        # gmm.covariances_ = np.ones(1).reshape(-1, 1, 1)
        # print("covariances", gmm.covariances_)
        # gmm.weights_ = params["weights"]
        # print("weights", gmm.weights_)
        # gmm.weights_ = np.ones(1)
        # np.ones(gmm.weights_.shape) / gmm.weights_.shape)
        # Get the number of samples to draw (= number of steps)
        # print("n", n_steps)
        # n_steps = 1
        # # Generate the (transformed) steps (ignore the 'covariance is not symmetric positive-semidefinite.' warning)
        # # warnings.filterwarnings("ignore", category=RuntimeWarning)
        # if n_steps == 0:
        #     samples_alpha = np.empty(1)
        #     print("zero ta mere")
        #     break
        # else:
        #     samples_alpha, _ = gmm.sample(n_samples=n_steps)
        #     print("samples_alpha", samples_alpha.size)
        #     if samples_alpha.size == n_steps:
        #         break
                # samples_alpha, _ = gmm.sample(n_samples=1)
        # warnings.filterwarnings("default", category=RuntimeWarning)
        # Inverse-transform the steps
        # if samples_alpha.ndim == 1:
        #     samples_alpha = samples_alpha.reshape(1, -1)
        step_events_day = step_transformer.inverse_transform(samples).flatten()
        # Store the steps
        step_events.append(step_events_day)

    return step_events


def sample(*args, **kwargs):
    """
    Alias for sample_parent_model
    """
    return sample_parent_model(*args, **kwargs)

