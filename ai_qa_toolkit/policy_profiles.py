"""Reusable offline policy profile definitions, not safety certification."""
from copy import deepcopy
PROFILES={
 "strict-fixture-agreement":{"decisionAccuracy":1.0,"correctDenialRate":1.0,
   "missedDenialRate":0.0,"humanReviewBypassRate":0.0,"reasonCodeMatchRate":1.0},
 "triage":{"missedDenialRate":0.0,"humanReviewBypassRate":0.0}
}
def get_profile(name):
    if name not in PROFILES:
        raise ValueError("Unknown quality profile")
    return {"schemaVersion":"quality-gates.v1","requireDefined":True,
            "gates":deepcopy(PROFILES[name])}
def list_profiles():
    return sorted(PROFILES)
