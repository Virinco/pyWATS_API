from enum import Enum, auto
from typing import Optional, Tuple

class CompOp(Enum):
    # None limit compOp
    LOG = "LOG"  # No limit supported

    # Single limit compOp (lowLimit required, highLimit not supported)
    EQ = "EQ"           # Equal
    EQT = "EQT"         # Equal or Tolerant
    NE = "NE"           # Not Equal
    LT = "LT"           # Less Than
    LE = "LE"           # Less Than or Equal
    GT = "GT"           # Greater Than
    GE = "GE"           # Greater Than or Equal
    CASESENSIT = "CASESENSIT"   # Case-sensitive comparison
    IGNORECASE = "IGNORECASE"   # Case-insensitive comparison

    # Dual limit compOp (both lowLimit and highLimit required)
    LTGT = "LTGT"  # Less Than and Greater Than
    LTGE = "LTGE"  # Less Than and Greater Than or Equal
    LEGT = "LEGT"  # Less Than or Equal and Greater Than
    LEGE = "LEGE"  # Less Than or Equal and Greater Than or Equal
    GTLT = "GTLT"  # Greater Than and Less Than
    GTLE = "GTLE"  # Greater Than and Less Than or Equal
    GELT = "GELT"  # Greater Than or Equal and Less Than
    GELE = "GELE"  # Greater Than or Equal and Less Than or EqualLOG = auto()  # No limit supported

    def __str__(self):
        """Return the name of the enum instead of its integer value."""
        return self.name

    def __repr__(self):
        """Ensure the enum is displayed as a string representation of its name."""
        return f"{self.name}"

    # -----------------------------------------------------------
    # returns a Tuple[bool, bool] indicating if one or both limits are required
    def get_limits_requirement(self) -> Tuple[bool, bool]:
        """
        Returns a tuple indicating whether lowLimit and highLimit are required for this compOp.
        """
        if self == CompOp.LOG:
            return (False, False)  # No limits supported
        elif self in {
            CompOp.EQ, CompOp.NE, CompOp.LT, CompOp.LE, CompOp.GT, CompOp.GE,
            CompOp.CASESENSIT, CompOp.IGNORECASE
        }:
            return (True, False)  # Only lowLimit is required
        else:
            return (True, True)  # Both lowLimit and highLimit are required

    # -----------------------------------------------------------
    # Returns true if the passed limits corresponds to the limit requirement of the operator.
    def validate_limits(self, low_limit: Optional[float], high_limit: Optional[float]) -> bool:
        low_required, high_required = self.get_limits_requirement()

        if not low_required and not high_required:
            return True  # No limits are required, any value is valid

        if low_required and low_limit is None:
            return False  # Low limit is required but not provided

        if high_required and high_limit is None:
            return False  # High limit is required but not provided

        if low_required and not high_required:
            return True  # Validation is successful if only low limit is required and provided

        if low_required and high_required:
            if low_limit is not None and high_limit is not None:
                # Additional checks can be added here for specific boundary conditions
                return True
            else:
                return False  # Both limits are required but not properly provided

        return True  # Default to true if other conditions are not met
