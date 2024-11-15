from typing import ClassVar

# --
# This is coda block, which contains documentation that can be weaved into
# full documents.


def function():
    """This is a regular docstring, which can be parsed by Python."""


# -- doc
# This is a Coda docsting which describes the function below.
def other_function():
    # This is a regular comment
    if True:
        pass
    # --
    # This is a nested block that will be used as an annotation when
    # presenting the details of the function.
    return None


class Class:

    # -- doc
    # Documentation of a class attribute
    Attribute: ClassVar[str] = "Hello, World"

    @staticmethod
    def StaticMethod():
        pass

    # -- doc
    # Coda documentation of a class method
    @classmethod
    def ClassMethod(cls):
        """Python documentation of a class method."""

    def __init__(self):
        # -- doc
        # Coda aocumentation of an attribute
        self.attribute = None

    # -- doc
    # Coda documentation of a method
    def method(self):
        """Python documentation of a method"""


# EOF
