
class TypeNameLogError(Exception):
    def __init__(self, typename:str) -> None:
        super().__init__(f'typename parameter for log function not matching: \"{typename}\"')
