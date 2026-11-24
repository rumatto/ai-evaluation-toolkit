"""Stable error codes for offline CLI consumers."""
from enum import IntEnum
class ExitCode(IntEnum):
    SUCCESS = 0
    EVALUATION_FAILED = 1
    INVALID_INPUT = 2
class EvaluationInputError(ValueError):
    code = "EVALUATION_INPUT_INVALID"
class ProvenanceError(EvaluationInputError):
    code = "PROVENANCE_VERIFICATION_FAILED"
def error_payload(error):
    return {"error": {"code": getattr(error, "code", "EVALUATION_INPUT_INVALID"),
                      "message": str(error)}}
