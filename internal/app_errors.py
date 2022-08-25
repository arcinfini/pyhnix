from discord import app_commands, Interaction

class ClearanceError(app_commands.CheckFailure):
    pass

class TransformationError(app_commands.TransformerError):
    pass