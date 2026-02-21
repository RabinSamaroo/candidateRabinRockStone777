import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Required for JSON serialization of datetime objects
def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class EventStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.seen_ids = set()
        if self.path.exists():
            for line in self.path.open():
                event = json.loads(line)
                self.seen_ids.add(event['event_id'])

    def append(self, event: Dict[str, Any]) -> bool:
        if event['event_id'] in self.seen_ids: # idempotent
            return False 
        with self.path.open('a') as f:
            f.write(json.dumps(event, default=default_serializer) + '\n')
        self.seen_ids.add(event['event_id'])
        return True

    def load_all(self) -> List[Dict[str, Any]]:
        with self.path.open() as f:
            return [json.loads(line) for line in f]

    def load_by_locker(self, locker_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.load_all() if e['locker_id'] == locker_id]