
class Validate:
    """
    A utility class for validation methods.
    Provides static methods to validate various types of inputs.
    """

    @staticmethod
    def non_empty_string(
            value: str, 
            name: str
        ) -> None:
        """
        Validate that the given value is a non-empty string.
        Raises ValueError if the value is not a non-empty string.
        """
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

    @staticmethod
    def is_instance(
            value: object, 
            expected_type: type, 
            name: str
        ) -> None:
        """
        Validate that the given value is an instance of the expected type.
        Raises TypeError if the value is not an instance of the expected type.
        """
        if not isinstance(value, expected_type):
            raise TypeError(f"{name} must be an instance of {expected_type.__name__}")
        