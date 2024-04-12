import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture

from . transformers import StepTransformer, ParamTransformer


def fit_child_model(step_events, n_components=3) -> (list[GaussianMixture], list[float]):

    n_days = len(step_events)

    # Transform the data (steps)
    step_transformer = StepTransformer()
    transformed_all_steps = step_transformer.fit_transform(step_events)

    # Prepare the containers for the results (to be filled in the loop)
    # Result are "features", that are the transformed parameters that will feed the parent model
    if n_components == 1:
        # for each model: per day, logit(mean), log1p(var), n
        child_models_features = np.zeros((n_days, 3))
    else:
        # for each model: per day, logit(means), log1p(var), logit(coeff)
        child_models_features = np.zeros((n_days, n_components*3+1))

    param_transformer = ParamTransformer(step_events)

    # Store the fitted models
    child_models = np.zeros(n_days, dtype=object)

    # ------------------------------------------------------------------

    for day in range(n_days):

        # Get the (transformed) steps for the day
        x = transformed_all_steps[day].reshape(-1, 1)

        # Fit the model
        gmm = GaussianMixture(n_components=n_components, random_state=123)
        gmm.fit(x)

        # Store the model
        # Note: will could store the BIC score: gmm.bic(X)
        child_models[day] = gmm

        # Store the (transformed) parameters (referred to as `features`)
        features = param_transformer.transform(gmm, day)
        child_models_features[day] = features

    return child_models, child_models_features, step_transformer, param_transformer


def fit_parent_model(
        child_models_features
) -> (np.ndarray, np.ndarray, np.ndarray):
    """
    Fit the parent model using the features of the child models.
    This model will therefore generate the parameters of daily activity models
    (one sample of the parent model correspond to the parameters of one day).
    """

    # Standardize the data
    features_transformer = StandardScaler()
    x = features_transformer.fit_transform(child_models_features)

    n_components_range_beta = range(1, 18)

    all_beta_gmm = [GaussianMixture(n_components=n_components).fit(x) for n_components in n_components_range_beta]
    all_beta_scores = [_gmm.bic(x) for _gmm in all_beta_gmm]

    # Choose the best model
    best_beta_idx = np.argmin(all_beta_scores)
    best_beta_gmm = all_beta_gmm[best_beta_idx]
    return best_beta_gmm, features_transformer


def fit_model(step_events, child_models_n_components=3) -> (np.ndarray, list):
    """
    Fit the child and parent models.
    """

    # Fit the child models
    child_models, child_models_features, step_transformer, params_transformer = (
        fit_child_model(step_events, child_models_n_components))

    # Fit the parent model
    parent_model, features_transformer = fit_parent_model(child_models_features)

    return parent_model, {
        "step_transformer": step_transformer,
        "params_transformer": params_transformer,
        "features_transformer": features_transformer
    }
