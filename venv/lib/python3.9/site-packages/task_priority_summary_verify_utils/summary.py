class Reporting:
    def __init__(self, status_mapping):
        """
        Initialize with the status_mapping, which should map task attributes to user-defined status names.
        """
        self.status_mapping = status_mapping  # Expecting something like {'done': 'Completed', 'in_progress': 'Incompleted', 'verified': 'Verified'}

    def task_summary(self, tasks):
        """
        Generate a summary of task statuses.
        """
        # Initialize the summary with user-defined statuses (keys) and set counts to zero.
        summary = {status_name: 0 for status_name in self.status_mapping.values()}  # Initialize with all possible statuses

        for task, employee in tasks:
            status = self.get_task_status(task)  # Dynamically determine the status based on task fields
            if status in summary:
                summary[status] += 1
            else:
                # If the status is not in the user-defined mapping, return a message
                summary['Undefined Status'] = summary.get('Undefined Status', 0) + 1
        
        return summary

    def get_task_status(self, task):
        """
        Return the internal status based on task's attributes, mapping to user-defined names.
        """
        # Check the task's internal attributes to determine status and map to user-defined names
        if task.complete:  # Check for completion (using the actual attribute 'complete' from the Task model)
            if 'done' in self.status_mapping:
                return self.status_mapping['done']  # Return the user-defined 'done' status
            else:
                raise ValueError("Status 'done' is not defined in the status_mapping. Please define it.")
        elif task.verified:  # If task is verified
            if 'verified' in self.status_mapping:
                return self.status_mapping['verified']  # Return the user-defined 'verified' status
            else:
                raise ValueError("Status 'verified' is not defined in the status_mapping. Please define it.")
        else:
            if 'in_progress' in self.status_mapping:
                return self.status_mapping['in_progress']  # Return the user-defined 'in_progress' status
            else:
                raise ValueError("Status 'in_progress' is not defined in the status_mapping. Please define it.")
