class InvalidSpeakerCountException(Exception):
    """Custom Exception for invalid number of speakers"""

    def __init__(self, message="Invalid number of speakers detected!"):
        self.message = message
        super().__init__(self.message)
