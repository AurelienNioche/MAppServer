import numpy as np
from scipy import stats
from sklearn.preprocessing import MinMaxScaler
from scipy.special import inv_boxcox, logit, expit as sigmoid


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
        # if transformed.ndim == 1:
        #     transformed = transformed.reshape(-1, 1)
        # print("transformed shape", transformed.shape)
        _inv_boxcox = inv_boxcox(transformed, self.lambda_param).reshape(-1, 1)
        # print("_inv_boxcox shape", _inv_boxcox.shape)
        _inv_trans = self.step_scaler.inverse_transform(_inv_boxcox).flatten()
        return sigmoid(_inv_trans)

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
        means = gmm.means_.flatten()
        variances = np.log1p(gmm.covariances_).flatten()
        weights = logit(gmm.weights_.flatten())
        n_steps = np.atleast_1d(np.log(self.n[day] / self.max_n))
        # Store the transformed parameters
        features = [n_steps, means, variances]
        n_components = means.size
        if n_components > 1:
            features += [weights]
        assert len(means) == len(variances) == len(weights) == n_components
        # Concatenate the transformed parameters
        return np.concatenate(features)

    def inverse_transform(self, features):
        # Determine the number of components
        # 4 parameters per component. The first one is n.
        # Exception: if there is only one component, there is no weight, so only 2 parameters and n.
        # Because of that, we put min(1, ...)
        n_components = min(1, (len(features) - 1) // 3)
        # print("n_components in inverse transform", n_components)
        # Extract the transformed parameters
        n_steps = features[0]
        means = features[1:n_components+1]
        variances = features[n_components+1:2*n_components+1]
        if n_components > 1:
            weights = features[2*n_components+1:]
        else:
            weights = np.ones(1)
        # Inverse-transform the parameters (the means are unchanged)
        n_steps = int(round(np.exp(n_steps) * self.max_n))
        variances = np.expm1(variances)
        if n_components > 1:
            weights = sigmoid(weights)  # Inverse of logit
            weights /= np.sum(weights)  # Normalise the weights
        # Check the dimensions
        assert len(means) == len(variances) == len(weights) == n_components
        # Store the inverse-transformed parameters
        return {
            "means": means,
            "variances": variances,
            "weights": weights,
            "n": n_steps,
            "n_components": n_components
        }
