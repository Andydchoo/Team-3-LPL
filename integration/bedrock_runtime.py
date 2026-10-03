"""Bounded Bedrock clients with shared pacing for the event's request limit."""

import threading
import time

from .aws_config import AWSSettings, create_client, create_session


class RequestPacer:
    def __init__(self):
        self._lock = threading.Lock()
        self._next_request_at = 0.0

    def call(self, callback, **request):
        with self._lock:
            delay = self._next_request_at - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            self._next_request_at = time.monotonic() + 1.0
            return callback(**request)


_PACER = RequestPacer()


class PacedBedrockClient:
    def __init__(self, client):
        self._client = client

    def converse(self, **request):
        return _PACER.call(self._client.converse, **request)


def create_bedrock_client():
    # A fresh session loads the current profile after a manual token refresh.
    settings = AWSSettings.from_environment()
    return PacedBedrockClient(create_client(create_session(settings), "bedrock-runtime"))
