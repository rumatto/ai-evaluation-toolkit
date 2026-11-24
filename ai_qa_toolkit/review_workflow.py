"""Offline review decisions; never executes or applies agent changes."""
from datetime import datetime, timezone
from pathlib import Path
from io_core import load_object, write_json_atomic

VALID={"approved","rejected","needs-information"}
def review_decision(queue, item_id, decision, reviewer, note):
    if not isinstance(queue,dict):
        raise ValueError("Review queue must be an object")
    if queue.get("schemaVersion")!="evaluation-review-queue.v1":
        raise ValueError("Unsupported review queue schema")
    if not isinstance(decision,str) or decision not in VALID:
        raise ValueError("Unsupported decision")
    if not isinstance(reviewer,str) or not reviewer.strip():
        raise ValueError("Reviewer is required")
    if not isinstance(note,str) or not note.strip():
        raise ValueError("Review note is required")
    items=queue.get("items")
    if not isinstance(items,list):
        raise ValueError("Review items must be a list")
    if not isinstance(item_id,str) or not item_id.strip():
        raise ValueError("Review item ID is required")
    if any(not isinstance(item,dict) for item in items):
        raise ValueError("Malformed review item")
    identifiers=[item.get("id") for item in items]
    if any(not isinstance(value,str) or not value.strip() for value in identifiers):
        raise ValueError("Malformed review item ID")
    if len(identifiers)!=len(set(identifiers)):
        raise ValueError("Duplicate review item IDs")
    matches=[item for item in items if item.get("id")==item_id]
    if len(matches)!=1:
        raise ValueError("Review item not uniquely identified")
    item=matches[0]
    if item.get("status")!="pending-human-review":
        raise ValueError("Item already reviewed")
    item["status"]="reviewed"
    item["humanDecision"]={
        "decision":decision,"reviewer":reviewer.strip(),"note":note.strip(),
        "recordedAt":datetime.now(timezone.utc).isoformat(),
        "appliedToAgent":False}
    return queue

def review_file(queue_path, output_path, item_id, decision, reviewer, note):
    queue=load_object(queue_path,"evaluation-review-queue.v1")
    updated=review_decision(queue,item_id,decision,reviewer,note)
    write_json_atomic(output_path,updated,protected=[queue_path])
    return updated
