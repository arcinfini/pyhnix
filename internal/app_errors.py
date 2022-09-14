from discord import app_commands, Interaction

class ClearanceError(app_commands.CheckFailure):
    pass

class TransformationError(app_commands.TransformerError):
    
    def __init__(self, message, **kwargs):
        super(Exception, self).__init__(message)