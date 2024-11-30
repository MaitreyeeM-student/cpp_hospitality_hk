# Updated verification library with flexible status key

class TaskVerification:
    def __init__(self, name, status, statuses, verification_key):
        """
        Initialize a TaskVerification instance.

        :param name: The name or identifier of the task.
        :param status: The current status of the task.
        :param statuses: A dictionary mapping status keys to status values.
        :param verification_key: The key in statuses that defines the required verification status.
        """
        self.name = name
        self.status = status
        self.statuses = statuses
        self.verification_key = verification_key  # The key to check for verification status

    def __repr__(self):
        return f"<TaskVerification name={self.name} status={self.status}>"

    def verify(self):
        # Dynamically check if the task status matches the verification status from the key
        required_status = self.statuses.get(self.verification_key, None)
        return self.status == required_status


class TaskManager:
    def __init__(self, tasks, verification_key):
        """
        Initialize a TaskManager instance.

        :param tasks: A dictionary of tasks to manage.
        :param verification_key: The key used to define the completion status in each task's statuses.
        """
        self.tasks = tasks
        self.verification_key = verification_key  # Define which status key represents "completion"

    def verify_task(self, task_id):
        # Retrieve the task by task_id and verify its status
        task = self.tasks.get(task_id)
        return task.verify() if task else False
