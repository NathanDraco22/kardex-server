from typing_extensions import Self


class Mediator:
    """
    This class is a mediator between the cli and the onion generator.
    It is a singleton and it is used to call the methods of the cli
    from the onion generator.
    """

    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(Mediator, cls).__new__(cls)
        return cls.instance

    output_folders: list[str] = []
