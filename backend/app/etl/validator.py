import re
import datetime
from typing import Optional, Tuple, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ValidationInfo

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

class EmployeeRawRecord(BaseModel):
    employee_id: Any
    name: Any
    department: Any
    salary: Any
    joining_date: Any
    email: Any


class EmployeeValidatedRecord(BaseModel):
    employee_id: int
    name: str
    department: str
    salary: float
    joining_date: datetime.date
    email: str

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        cleaned = str(v).strip()
        if not cleaned or len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return cleaned

    @field_validator("department")
    def validate_dept(cls, v: str) -> str:
        cleaned = str(v).strip().title()
        if not cleaned:
            raise ValueError("Department cannot be empty.")
        return cleaned

    @field_validator("salary")
    def validate_salary(cls, v: float) -> float:
        if v is None or v <= 0:
            raise ValueError("Salary must be a strictly positive numerical value.")
        if v > 10_000_000:
            raise ValueError(f"Salary {v} exceeds reasonable upper threshold ($10,000,000).")
        return round(float(v), 2)

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        cleaned = str(v).strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError(f"Invalid email format: '{v}'")
        return cleaned


class RecordValidationResult:
    def __init__(
        self,
        is_valid: bool,
        raw_record: Dict[str, Any],
        validated_record: Optional[EmployeeValidatedRecord] = None,
        error_message: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.raw_record = raw_record
        self.validated_record = validated_record
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "raw_record": self.raw_record,
            "validated_record": self.validated_record.model_dump() if self.validated_record else None,
            "error_message": self.error_message
        }


def validate_record(raw: Dict[str, Any]) -> RecordValidationResult:
    """
    Validates a single transformed record dictionary against strict business rules.
    """
    try:
        validated = EmployeeValidatedRecord(**raw)
        return RecordValidationResult(
            is_valid=True,
            raw_record=raw,
            validated_record=validated,
            error_message=None
        )
    except Exception as e:
        return RecordValidationResult(
            is_valid=False,
            raw_record=raw,
            validated_record=None,
            error_message=str(e)
        )
