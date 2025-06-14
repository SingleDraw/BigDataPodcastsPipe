import os
import logging
import glob
import sys
from celery import Task
# from faster_whisper import WhisperModel
from app.src.utils import parse_conn_uri # parse_s3_uri,  - REMOVE
from app.src.helpers import split_mp3
from app.src.broker import broker as r  # Redis client for tracking progress
from app.src.storages import storages   # Storage client provider

# use this download method if source is storage, for links use wget??
# move parse_s3_uri to s3 storage class or make it universal for all sources

_max_duration = float(os.getenv("CHUNK_MAX_DURATION", 600))
_task_soft_time_limit = float(os.getenv("TASK_SOFT_TIME_LIMIT", 600))   # soft timeout: raises SoftTimeLimitExceeded
_default_retry_delay = float(os.getenv("DEFAULT_RETRY_DELAY", 30))      # retry delay in seconds
_max_retries = int(os.getenv("MAX_RETRIES", 3))                         # max retries

_cleanup_timeout = max(
    float(os.getenv("CHUNK_CLEANUP_TIMEOUT", 600)), 
    float(os.getenv("TASK_SOFT_TIME_LIMIT", 600)) + 60
) 

# Set up logging for the module
logger = logging.getLogger("whisperer")

# =============================================================================
# OPTION 2: Multiprocessing with function reference (for CPU-bound tasks)
# =============================================================================

class TranscriptionTask(Task):
    abstract = True
    logger = logging.getLogger(__name__)
    broker = r
    storages = storages             # Storage client provider
    parse_conn_uri = parse_conn_uri # Parse connection URI

    def __init__(
            self, 
            *args, 
            **kwargs
        ):
        super().__init__(*args, **kwargs)
        self.task_id = None
        self.chunked_source = []
        self.local_input = None
        self.local_output = None
        self._local_output = None
        self.chunk_pattern = None
        self.needs_processing = True
        self.max_duration = _max_duration
        self.language = None
        self.use_gpu = False
        
        self.source_storage = None
        self.sink_storage = None


    def setup(
            self,
            task_id: str,
            source_uri: str,  # s3://bucket/key or azure://container/key
            sink_uri: str,    # s3://bucket/key or azure://container/key
    ) -> None:
        """
        Setup the transcription job.
        This includes downloading the input file and splitting it into chunks.
        """
        self.task_id = task_id
        self.source = source_uri
        self.sink = sink_uri
        # self.client = storages.get_client(self.source["type"]) if self.source['type'] == "storage" else None

        self.task_id = task_id

        self.chunked_source = []
        self.local_input = f"/tmp/{task_id}.mp3"
        self.local_output = f"/tmp/{task_id}.txt"
        self._local_output = f"/tmp/_{task_id}.txt"
        self.chunk_pattern = f"/tmp/chunk_{task_id}*.mp3"
        self._needs_processing = True

        self.max_duration = _max_duration
        self.language = None
        self.use_gpu = False



    def _is_transcription_result_ready(
            self
        ) -> bool:
        """
        Check if the result is ready.
        This includes checking if the output file already exists.
        """
        is_result_ready = os.path.exists(self.local_output)

        if is_result_ready:
            self.logger.info(f"Output file {self.local_output} already exists. Attempting retry.")
            self.broker.set(f"task_progress:{self.task_id}", "Output file already exists. Attempting retry.")
        return is_result_ready
        


    @property
    def needs_processing(
            self
        ) -> bool:
        """
        Check if the task needs processing.
        This is used to determine if the task needs to be processed again.
        """
        return self._needs_processing



    @needs_processing.setter
    def needs_processing(
            self,
            needs_processing: bool
        ) -> None:
        """
        Set the needs_processing flag.
        This is used to determine if the task needs to be processed again.
        """
        self._needs_processing = needs_processing



    def _are_audio_chunks_ready(
            self
        ) -> bool:
        """
        Check if the audio chunks are ready.
        This includes checking if the chunk files already exist.
        """
        self.logger.info(f"Chunk files {self.chunk_pattern} already exist. Attempting retry.")
        self.broker.set(f"task_progress:{self.task_id}", "Chunk files already exist. Attempting retry.")
        return glob.glob(self.chunk_pattern)
    


    def _get_audio_chunk_files_list(
            self
        ) -> list:
        """
        Get the audio chunk files.
        This includes checking if the chunk files already exist.
        """
        return sorted(glob.glob(self.chunk_pattern))
    


    def _is_audio_source_downloaded(
            self
        ) -> bool:
        """
        Check if the audio source is downloaded.
        This includes checking if the downloaded input audio file exists.
        """
        is_downloaded = os.path.exists(self.local_input)
        if is_downloaded:
            self.logger.info(f"Input file {self.local_input} already exists. Attempting retry.")
            self.broker.set(f"task_progress:{self.task_id}", "Input file already exists. Attempting retry.")
        return is_downloaded



    def _split_audio_into_chunks(
            self
        ) -> list:
        """
        Split the audio file into chunks.
        Returns a list of chunk files.
        """
        self.broker.set(f"task_progress:{self.task_id}", "Splitting into chunks...")
         # Create chunks of the input file
        chunk_files = split_mp3(
            self.local_input,
            self.task_id,
            chunk_duration=self.max_duration
        )

        os.remove(self.local_input)  # Cleanup input file after chunking
        return chunk_files
    


    def _download_input_source_file(
            self
        ) -> None:
        """
        Download the input source file.
        """
        self.broker.set(f"task_progress:{self.task_id}", "Downloading input file...")

        conn_name, conn_type, storage_unit, key_path = parse_conn_uri(self.source)

        if conn_type in ["http", "https"]:
            # Use requests library to download the file
            import requests
            url = f"{conn_type}://{storage_unit}/{key_path}"
            response = requests.get(url, stream=True)
            with open(self.local_input, "wb") as f:
                f.write(response.content)

        else:
            # Use the storage client to download the file
            self.source_storage = self.storages.get_client(
                name=conn_name,
                type=conn_type
            )

            self.source_storage.download_file(
                container_name=storage_unit,
                storage_key=key_path,
                destination_path=self.local_input
            )

        self.logger.info(f"Downloaded input file {os.path.basename(key_path)} to {self.local_input}.")
        self.broker.set(f"task_progress:{self.task_id}", "Input file downloaded...")





    def upload_output_file(
            self
        ) -> None:
        """ Upload the output file to the storage sink.
        This method is called after the task is executed.
        It uploads the output file to the storage sink.
        """
        conn_name, conn_type, storage_unit, key_path = parse_conn_uri(
            uri=self.sink,      # output URI
            allow_http=False    # Output must be a storage URI, not HTTP
        )

        # Use the storage client to download the file
        self.sink_storage = self.storages.get_client(
            name=conn_name,
            type=conn_type
        )

        # Upload the output file to the storage sink
        self.sink_storage.upload_file(
            source=self.local_output,
            container_name=storage_unit,
            storage_key=key_path,
            overwrite=True  # Overwrite the file if it already exists
        )

        self.logger.info(f"Uploaded output file {os.path.basename(key_path)} to {self.sink}.")



    def init_task(
            self,
        ) -> None:
        """
        Setup the transcription job.
        This includes downloading the input file and splitting it into chunks.
        This method is called before the task is executed.
        Sets flags for processing:
        > 1. needs_processing: True if the task needs to be processed (no previous output exists)
        > 2. chunked_source: List of chunk files if the task needs to be processed
        """

        self.broker.set(f"task_progress:{self.task_id}", "Starting...")  

        self.needs_processing = True
        self.chunked_source = None

        if self._is_transcription_result_ready():
            self.needs_processing = False

        elif self._are_audio_chunks_ready():
            self.chunked_source = self._get_audio_chunk_files_list()

        elif self._is_audio_source_downloaded():
            self.chunked_source = self._split_audio_into_chunks()

        else:
            self._download_input_source_file()
            self.chunked_source = self._split_audio_into_chunks()

       








    def safe_remove_files(
            self,
            *paths: str, 
            glob_patterns: list[str] = []
        ) -> None:
        """
        Safely remove files and directories, 
        ignoring errors and logging warnings.
        """
        
        for path in paths:
            try:
                os.remove(path)
            except Exception as e:
                logger.warning(
                    f"Failed to remove {path}: {e}"
                )

        for pattern in glob_patterns:
            for file in glob.glob(pattern):
                try:
                    os.remove(file)
                except Exception as e:
                    logger.warning(
                        f"Failed to remove globbed file {file}: {e}"
                    )


