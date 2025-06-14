import os
import logging
import glob
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded, WorkerLostError
from app.src.task.transcription_task import TranscriptionTask
from app.src.task.transcription_process_handler import TranscriptionProcessHandler
from app.src.broker import broker as r  # Redis client for tracking progress
from app.src.storage.errors import StorageDownloadError, StorageUploadError
from app.src.helpers import progress_bar_callback, cleanup_old_chunks
from typing import Optional

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

@shared_task(
        bind=True, 
        base=TranscriptionTask,                 # Use the custom task class
        # Task name
        name="whisperer.transcribe",
        # Acknowledgment settings
        ack_late=True,                          # acknowledge task after execution
        reject_on_worker_lost=True,             # requeue task if worker dies

        # Retry settings
        retry_kwargs={
            "max_retries": _max_retries,         # max retries
            "countdown": _default_retry_delay    # delay between retries
        },

        # Task timing settings
        soft_time_limit=_task_soft_time_limit,  # soft timeout: raises SoftTimeLimitExceeded
        time_limit=_task_soft_time_limit + 5,   # hard timeout: forcibly kills task

        # Task tracking settings
        track_started=True,                    # track task start time
        task_acks_on_failure_or_timeout=True,   # ack on failure or timeout
    )
def transcribe(
        self, # Celery task context - needed for task referencing
        input: str,
        output: str,
        use_gpu: bool = False,
        language: Optional[str] = None,
        # storage_name: str = "default",
        cleanup_timeout: float = _cleanup_timeout,
        max_duration: float = _max_duration
    ) -> None:
    """
    Transcribe an audio file using the Whisper model.
    Args:
        input s3_uri/http (str): S3 URI of the input audio file.
        output s3_uri (str): S3 URI for the output transcription file.
        use_gpu (bool): Flag to use GPU for transcription.
        language (str): Language code for transcription.
        storage_name (str): Predefined storage name for input/output.
    """

    task_id=self.request.id

    try:

        # Set up job
        self.setup(
            task_id=self.request.id,
            source_uri=input,
            sink_uri=output
        )

        # Set initial state
        # This stage determines if the task needs processing and what steps are needed to take
        # This includes downloading the input file and splitting it into chunks
        # Sets flags for processing:
        # 1. needs_processing: True if the task needs to be processed (no previous output exists)
        # 2. chunked_source: List of chunk files if the task needs to be processed
        # Its especially useful for retrying tasks
        self.init_task()
            
        # 3. Check if the output file already exists

        if self.needs_processing:
            process_handler = TranscriptionProcessHandler()
            job_kwargs = {
                "chunk_files": self.chunked_source,
                "task_id": task_id,
                "local_input": self.local_input,
                "local_output": self.local_output,
                "_local_output": self._local_output,
                "max_duration": max_duration,
                "language": language,
                "use_gpu": use_gpu
            }
            result = process_handler.run_transcription(kwargs=job_kwargs)
            logger.info(f"Transcription completed for task {task_id}: {result}")





        # Upload the output file to the storage sink
        self.upload_output_file()







        # Upload result - always to storage sink
        # # out_bucket, out_key = parse_s3_uri(output)

        # <optional_conn_name>+<conn_type>://<storage_unit>/<key_path>
        # example: default+s3://my-bucket/my-key
        # or: default+az://whisperer/transcriptions/output.txt

            # conn_name, conn_type, storage_unit, key_path = parse_conn_uri(
            #     uri=self.sink, # output
            #     allow_http=False  # Output must be a storage URI, not HTTP
            # )

            # # Use the storage client to download the file
            # self.sink_storage = self.storages.get_client(
            #     name=conn_name,
            #     type=conn_type
            # )

            # # Upload the output file to the storage sink
            # self.sink_storage.upload_file(
            #     source_path=self.local_output,
            #     storage_unit=storage_unit,
            #     storage_path=key_path
            # )


        # # Upload result - always to storage sink
        # self.storage.upload_file(
        #         source_path=self.local_output, 
        #         storage_unit=out_bucket, 
        #         storage_path=out_key
        # )
        os.remove(self.local_output)  # Cleanup local output file












        r.set(f"task_progress:{self.task_id}", "--complete")
        progress_bar_callback("Transcribing... 100%")
        progress_bar_callback("--complete") # !IMPORANT: do not change this flag, it is used to signal completion



    # Handle specific exceptions


    except SoftTimeLimitExceeded as e:
        logger.warning(f"Task {task_id} exceeded soft time limit - NOT completing")
        
        # Clean up partial work
        r.set(f"task_progress:{task_id}", "Timed out - cleaning up")
        
        # Determine if we should retry
        if self.request.retries < _max_retries:
            logger.info(f"Retrying timed out task {task_id} (attempt {self.request.retries + 1}/{_max_retries})")
            raise self.retry(
                countdown=_default_retry_delay * (2 ** self.request.retries),
                exc=e
            )
        else:
            logger.error(f"Task {task_id} timed out after {_max_retries} attempts")



            # Cleanup any partial work
            """
            General cleanup for any partial work
            """


            raise e
    
    except StorageDownloadError as e:
        logger.error(f"Storage download error for task {task_id}: {str(e)}")
        if self.request.retries < _max_retries:
            raise self.retry(
                countdown=_default_retry_delay * (2 ** self.request.retries),
                exc=e
            )
        


        # Cleanup any partial work
        """
        General cleanup for any partial work
        """



        raise e

    except StorageUploadError as e:
        logger.error(f"Storage upload error for task {task_id}: {str(e)}")
        if self.request.retries < _max_retries:
            raise self.retry(
                countdown=_default_retry_delay * (2 ** self.request.retries),
                exc=e
            )
        # Cleanup any partial work


        """
        General cleanup for any partial work
        """



        raise e

    except WorkerLostError:
        logger.error(f"Worker lost error for task {task_id}")
        # Don't retry on worker lost - let Celery handle the requeue
        raise
    
    except Exception as exc:
        logger.error(f"Task {task_id} failed with error: {str(exc)}")
        
        # Check if we should retry
        if self.request.retries < _max_retries:
            logger.info(f"Retrying task {task_id} (attempt {self.request.retries + 1}/{_max_retries})")
            raise self.retry(
                countdown=_default_retry_delay * (2 ** self.request.retries),  # Exponential backoff
                exc=exc
            )
        else:
            logger.error(f"Task {task_id} failed after {_max_retries} retries")





            """
            General cleanup for any partial work
            This includes:
            - Removing chunk files
            - Removing local output file
            - Removing local input file
            - Removing temporary chunk files
            """
            # Cleanup any partial work
            for chunk_file in self.chunked_source:
                try:
                    os.remove(chunk_file)
                except Exception as e:
                    logger.warning(f"Failed to remove chunk file {chunk_file}: {e}")
            # Cleanup local output file
            try:
                os.remove(self.local_output)
            except Exception as e:
                logger.warning(f"Failed to remove local output file {self.local_output}: {e}")
            # Cleanup local input file
            try:
                os.remove(self.local_input)
            except Exception as e:
                logger.warning(f"Failed to remove local input file {self.local_input}: {e}")
            # Cleanup temporary chunk files
            for chunk_file in glob.glob(self.chunk_pattern):
                try:
                    os.remove(chunk_file)
                except Exception as e:
                    logger.warning(f"Failed to remove chunk file {chunk_file}: {e}")






            raise exc  # Fatal error, do not retry

    finally:
        try:
            cleanup_old_chunks(expiry_seconds=cleanup_timeout)
        except Exception as e:
            logger.warning(f"Failed to cleanup old chunks: {e}")

        # Cleanup Redis progress tracking
        try:
            r.delete(f"task_progress:{self.request.id}")
        except Exception as e:
            logger.warning(f"Failed to cleanup Redis progress: {e}")











































