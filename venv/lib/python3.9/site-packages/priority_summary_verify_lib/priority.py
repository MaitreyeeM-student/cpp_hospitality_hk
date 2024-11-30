class Priority:
    def __init__(self, custom_priorities=None):
        """
        Initialize Priority with a custom priority dictionary.
        :param custom_priorities: Dictionary with priority levels and values, e.g., {'Urgent': 5, 'Normal': 2, 'Low': 1}.
        """
        if not custom_priorities:
            raise ValueError("Please set your priority levels and values.")
        
        # Assign custom priorities
        self.PRIORITIES = custom_priorities
        
        # Default priority set to the first level provided in the dictionary
        self.priority = next(iter(self.PRIORITIES))

    def set_priority(self, priority_level):
        """
        Set the priority level if it exists in the custom priorities.
        :param priority_level: Priority level to set (must exist in PRIORITIES).
        """
        if priority_level not in self.PRIORITIES:
            raise ValueError("Invalid priority level")
        self.priority = priority_level

    def get_priority(self):
        """
        Retrieve the current priority level.
        :return: The current priority level name.
        """
        return self.priority

    def get_priority_value(self):
        """
        Retrieve the value of the current priority level.
        :return: The value associated with the current priority level.
        """
        return self.PRIORITIES[self.priority]
