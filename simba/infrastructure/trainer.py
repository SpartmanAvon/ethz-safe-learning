import numpy as np

from simba.infrastructure.logging_utils import TrainingLogger
from simba.infrastructure.logging_utils import logger


class RLTrainer(object):
    def __init__(self,
                 agent,
                 environemnt,
                 log_frequency,
                 video_log_frequency,
                 max_video_length,
                 training_logger_params):
        self.agent = agent
        self.environment = environemnt
        self.training_logger = TrainingLogger(**training_logger_params)
        self.log_frequency = log_frequency
        self.max_video_length = max_video_length
        self.video_log_frequency = video_log_frequency

    def train(self):
        self.agent.build_graph()
        converged = False
        iteration = 0
        while not converged:
            logger.info("Training iteration {}.".format(iteration))
            self.agent.interact(self.environment)
            self.agent.update()
            if self.log_frequency > 0 and iteration % self.log_frequency == 0:
                self.log(self.agent.report(), iteration)
            if self.log_frequency > 0 and iteration % self.video_log_frequency == 0:
                self.log_video(self.agent.render_trajectory(
                    environment=self.environment,
                    policy=self.agent.policy,
                    max_trajectory_length=self.max_video_length
                ), iteration)
            iteration += 1

    def play_trained_model(self):
        # self.agent.load_graph()
        pass

    def log(self, report, epoch):
        """
        Takes a report from the agent and logs it.
        """
        losses = report.pop('losses')
        for i, loss in enumerate(losses):
            self.training_logger.log_scalars(
                scalar_dict={'loss': loss},
                group_name='model_training_losses',
                step=i,
                phase=epoch
            )
        for key, value in report.items():
            self.training_logger.log_scalar(value, key, epoch)
        self.training_logger.flush()

    def log_video(self, trajectory_records, epoch):
        """
        Logs videos from rendered trajectories.
        """
        trajectory_rendering = trajectory_records
        video = np.transpose(trajectory_rendering, [0, 3, 1, 2])
        self.training_logger.log_video(
            np.expand_dims(video, axis=0),
            'what_the_policy_looks_like',
            epoch)
