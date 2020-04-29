import tensorflow as tf
import numpy as np
from simba.infrastructure.common import standardize_name
from simba.models import BaseModel, MlpEnsemble


class TransitionModel(BaseModel):
    def __init__(self,
                 model,
                 observation_space_dim,
                 action_space_dim,
                 **kwargs):
        super().__init__(observation_space_dim + action_space_dim,
                         observation_space_dim)
        self.model_scope = model
        self.model = eval(standardize_name(model))(
            inputs_dim=self.inputs_dim,
            outputs_dim=self.outputs_dim,
            **kwargs)
        self.observation_space_dim = observation_space_dim
        self.action_space_dim = action_space_dim
        self.inputs_mean = tf.zeros((self.inputs_dim,))
        self.inputs_stddev = tf.ones((self.inputs_dim,))

    def build(self):
        self.model.build()

    def fit(self, inputs, targets):
        self.inputs_mean = tf.convert_to_tensor(inputs.mean(axis=0))
        self.inputs_stddev = tf.convert_to_tensor(inputs.std(axis=0))
        observations = inputs[:, self.observation_space_dim:]
        next_observations = targets
        return self.model.fit(
            (inputs - self.inputs_mean.numpy()) / (self.inputs_stddev.numpy() + 1e-8),
            next_observations - observations)

    def predict(self, inputs):
        return self.simulate_trajectories(
            current_state=inputs[..., :self.observation_space_dim],
            action_sequences=np.expand_dims(inputs[..., -self.action_space_dim:], axis=1)
        )

    def simulate_trajectories(self, current_state, action_sequences):
        return self.propagate(
            current_state.astype(np.float32),
            action_sequences.astype(np.float32)
        )

    @tf.function
    def propagate(self, s_0, action_sequences):
        horizon = action_sequences.shape[1]
        trajectories = tf.TensorArray(tf.float32, size=horizon)
        s_t = s_0
        for t in tf.range(horizon):
            a_t = action_sequences[:, t, ...]
            s_t_a_t = self.process_inputs(tf.concat([s_t, a_t], axis=1))
            # The model predicts s_t_1 - s_t hence we add here the previous state.
            d_s_t = self.model(s_t_a_t)
            s_t += d_s_t
            trajectories = trajectories.write(t, s_t)
        return tf.transpose(trajectories.stack(), [1, 0, 2])

    @tf.function
    def process_inputs(self, inputs):
        return (inputs - self.inputs_mean) / (self.inputs_stddev + 1e-8)

    def save(self):
        pass

    def load(self):
        pass
