import numpy as np
from scipy import stats
from sklearn.preprocessing import MinMaxScaler
from scipy.special import inv_boxcox, boxcox, logit, expit as sigmoid


class StepTransformer:
    def __init__(self):
        self.step_scaler = MinMaxScaler(feature_range=(1, 10))
        self.lambda_param = None

    def fit_transform(self, step_events):
        all_steps = np.concatenate(step_events)
        all_steps = logit(all_steps)
        all_steps = self.step_scaler.fit_transform(all_steps.reshape(-1, 1)).flatten()
        all_steps, self.lambda_param = stats.boxcox(all_steps)
        return self.transform(step_events)

    def _transform(self, step_events):
        X = np.asarray(step_events).reshape(-1, 1)
        return stats.boxcox(self.step_scaler.transform(logit(X)).flatten(), lmbda=self.lambda_param)

    def _inv_transform(self, transformed):
        return sigmoid(self.step_scaler.inverse_transform(inv_boxcox(transformed, self.lambda_param).reshape(-1, 1)).flatten())

    def transform(self, step_events):
        if isinstance(step_events, list):
            transformed = []
            for day in range(len(step_events)):
                transformed.append(self._transform(step_events[day]))
        else:
            transformed = self._transform(step_events)
        return transformed

    def inverse_transform(self, transformed):
        if not hasattr(self, "lambda_param"):
            raise ValueError("The transformer has not been fitted yet")
        if isinstance(transformed, list):
            inversed = []
            for day in range(len(transformed)):
                inversed.append(self._inv_transform(transformed[day]))
        else:
            inversed = self._inv_transform(transformed)
        return inversed


class ParamTransformer:
    def __init__(self, step_events):
        self.n = [len(step_events[_day]) for _day in range(len(step_events))]
        self.max_n = max(self.n)

    def transform(self, gmm, day):

        # Extract the parameters and transform them
        transformed_means = gmm.means_.flatten()
        transformed_vars = np.log1p(gmm.covariances_).flatten()
        transformed_weights = logit(gmm.weights_.flatten())
        transformed_n = np.atleast_1d(np.log(self.n[day] / self.max_n))

        # Store the transformed parameters
        n_components = len(gmm.means_)
        if n_components == 1:
            features = [transformed_means, transformed_vars, transformed_n]

        else:
            features = [transformed_means, transformed_vars, transformed_weights, transformed_n]

        # Concatenate the transformed parameters
        return np.concatenate(features)

    def inverse_transform(self, features):

        n_components = len(features) // 3 - 1

        # Extract the transformed parameters
        transformed_means = features[:n_components]
        transformed_vars = features[n_components:2*n_components]
        if n_components == 1:
            transformed_weights = np.empty(0)
        else:
            transformed_weights = features[2*n_components:-1]
        transformed_n = features[-1]

        # Inverse-transform the parameters
        means = transformed_means
        variances = np.expm1(transformed_vars)
        if n_components == 1:
            weights = np.ones(1)
        else:
            weights = sigmoid(transformed_weights) # Inverse of logit
            weights /= np.sum(weights)  # Normalise the weights

        n = int(round(np.exp(transformed_n) * self.max_n))

        # Store the inverse-transformed parameters
        return {
            "means": means,
            "variances": variances,
            "weights": weights,
            "n": n,
            "n_components": n_components
        }
