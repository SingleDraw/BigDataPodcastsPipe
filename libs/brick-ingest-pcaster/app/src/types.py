from typing import TypedDict

class PodcastType(TypedDict):
    source: str
    id: str
    title: str
    categories: list[str]

class EpisodeType(TypedDict):
    id: str
    title: str
    release_date: str
    duration: int
    transcription: str
    audio_source: str