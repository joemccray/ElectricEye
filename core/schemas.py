from typing import Literal, TypedDict


class CreateGreetingRequest(TypedDict):
    first_name: str
    voice_id: str
    greeting_seconds: float
    video_path: str


class CreateGreetingResponse(TypedDict):
    job_id: str
    status: Literal["queued", "processing", "done", "failed"]


class GreetingJob(TypedDict):
    id: int
    first_name: str
    voice_id: str
    greeting_seconds: float
    video_path: str
    status: Literal["queued", "processing", "done", "failed"]
    result_url: str | None
