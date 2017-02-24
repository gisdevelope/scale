"""Defines the class that holds a node's current conditions"""
from __future__ import unicode_literals

import logging
from collections import namedtuple

from django.utils.timezone import now

from job.tasks.health_task import HealthTask


logger = logging.getLogger(__name__)
NodeError = namedtuple('NodeError', ['name', 'title', 'description', 'daemon_bad', 'pull_bad'])


class ActiveError(object):
    """This class represents an active error for a node."""

    def __init__(self, error):
        """Constructor

        :param error: The node error
        :type error: :class:`scheduler.node.conditions.NodeError`
        """

        self.error = error
        self.started = None
        self.last_updated = None


class NodeConditions(object):
    """This class represents the set of current conditions that apply to a node."""

    # Errors
    BAD_DAEMON_ERR = NodeError(name='BAD_DAEMON', title='Docker Not Responding',
                               description='The Docker daemon on this node is not responding.', daemon_bad=True,
                               pull_bad=True)
    BAD_LOGSTASH_ERR = NodeError(name='BAD_LOGSTASH', title='Logstash Not Responding',
                                 description='The Scale logstash is not responding to this node.', daemon_bad=False,
                                 pull_bad=False)
    CLEANUP_ERR = NodeError(name='CLEANUP', title='Cleanup Failure',
                            description='The node failed to clean up some Scale Docker containers and volumes.',
                            daemon_bad=False, pull_bad=False)
    HEALTH_TIMEOUT_ERR = NodeError(name='HEALTH_TIMEOUT', title='Health Check Timeout',
                                   description='The last node health check timed out.', daemon_bad=False,
                                   pull_bad=False)
    IMAGE_PULL_ERR = NodeError(name='IMAGE_PULL', title='Image Pull Failure',
                               description='The node failed to pull the Scale Docker image from the registry.',
                               daemon_bad=False, pull_bad=False)
    LOW_DOCKER_SPACE_ERR = NodeError(name='LOW_DOCKER_SPACE', title='Low Docker Disk Space',
                                     description='The free disk space available to Docker is low.', daemon_bad=False,
                                     pull_bad=True)
    # Errors that can occur due to health checks
    HEALTH_ERRORS = [BAD_DAEMON_ERR, BAD_LOGSTASH_ERR, HEALTH_TIMEOUT_ERR, LOW_DOCKER_SPACE_ERR]

    def __init__(self, hostname):
        """Constructor

        :param hostname: The node's hostname
        :type hostname: string
        """

        self._active_errors = {}  # {Error name: ActiveError}
        self._hostname = hostname

        # TODO: figure out when to calculate is_daemon_bad and is_pull_bad
        self.is_daemon_bad = False  # Whether the node's Docker daemon is bad, preventing Docker tasks from running
        self.is_health_check_normal = True  # Whether the last node health check was normal
        self.is_pull_bad = False  # Whether the node should attempt to perform Docker image pulls

    def handle_cleanup_task_completed(self):
        """Handles the successful completion of a node cleanup task
        """

        self._error_inactive(NodeConditions.CLEANUP_ERR)

    def handle_cleanup_task_failed(self):
        """Handles the failure of a node cleanup task
        """

        self._error_active(NodeConditions.CLEANUP_ERR)

    def handle_health_task_completed(self):
        """Handles the successful completion of a node health check task
        """

        self.is_health_check_normal = True
        self._error_inactive_all_health()

    def handle_health_task_failed(self, task_update):
        """Handles the given failed task update for a node health check task

        :param task_update: The health check task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        self.is_health_check_normal = False
        self._error_inactive_all_health()
        if task_update.exit_code == HealthTask.BAD_DAEMON_CODE:
            logger.warning('Docker daemon not responding on host %s', self._hostname)
            self._error_active(NodeConditions.BAD_DAEMON_ERR)
        elif task_update.exit_code == HealthTask.LOW_DOCKER_SPACE_CODE:
            logger.warning('Low Docker disk space on host %s', self._hostname)
            self._error_active(NodeConditions.LOW_DOCKER_SPACE_ERR)
        elif task_update.exit_code == HealthTask.BAD_LOGSTASH_CODE:
            logger.warning('Logstash not responding on host %s', self._hostname)
            self._error_active(NodeConditions.BAD_LOGSTASH_ERR)
        else:
            logger.error('Unknown failed health check exit code: %s', str(task_update.exit_code))

    def handle_pull_task_completed(self):
        """Handles the successful completion of a node image pull task
        """

        self._error_inactive(NodeConditions.IMAGE_PULL_ERR)

    def handle_pull_task_failed(self):
        """Handles the failure of a node image pull task
        """

        self._error_active(NodeConditions.IMAGE_PULL_ERR)

    def cleanup_task_timeout(self):
        """Indicates that a node cleanup task has timed out
        """

        self._error_active(NodeConditions.CLEANUP_ERR)

    def health_task_timeout(self):
        """Indicates that a node health check task has timed out
        """

        self.is_health_check_normal = False
        self._error_inactive_all_health()
        self._error_active(NodeConditions.HEALTH_TIMEOUT_ERR)

    def pull_task_timeout(self):
        """Indicates that a node image pull task has timed out
        """

        self._error_active(NodeConditions.IMAGE_PULL_ERR)

    def _error_active(self, error):
        """Indicates that the given error is now active

        :param error: The node error
        :type error: :class:`scheduler.node.conditions.NodeError`
        """

        when = now()
        if error.name in self._active_errors:
            active_error = self._active_errors[error.name]
        else:
            active_error = ActiveError(error)
            active_error.started = when
            self._active_errors[error.name] = active_error
        active_error.last_updated = when

    def _error_inactive(self, error):
        """Indicates that the given error is now inactive

        :param error: The node error
        :type error: :class:`scheduler.node.conditions.NodeError`
        """

        if error.name in self._active_errors:
            del self._active_errors[error.name]

    def _error_inactive_all_health(self):
        """Inactivates all node errors related to health checks
        """

        for error in NodeConditions.HEALTH_ERRORS:
            self._error_inactive(error)
