import os
import logging
from celery import shared_task, exceptions
# from app.src.task.transcription_task import TranscriptionTask
# from app.src.task.transcription_process_handler import TranscriptionProcessHandler
from app.src.task import TranscriptionTask, TranscriptionProcessHandler
from app.src.broker import broker as r  # Redis client for tracking progress
from app.src.errors import StorageDownloadError, StorageUploadError
from app.src.helpers import progress_bar_callback
from app.settings import retry_kwargs
from typing import Optional

# Set up logging for the module
logger = logging.getLogger("whisperer")

@shared_task(
        bind=True, 
        base=TranscriptionTask,
        name="app.src.transcribe.transcribe",
        retry_kwargs=retry_kwargs
)
def transcribe(
        self,
        input: str,
        output: str,
        use_gpu: bool = False,
        language: Optional[str] = None
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

        self.init_task() # Set initial state - pick up from the last state
            
        # 3. Check if the output file already exists
        if self.needs_processing:
            result = (
                TranscriptionProcessHandler()
                .run_transcription(
                    kwargs={
                        "chunk_files": self.chunked_source,
                        "task_id": task_id,
                        "local_input": self.local_input,
                        "local_output": self.local_output,
                        "_local_output": self._local_output,
                        "max_duration": self.max_duration,
                        "language": language,
                        "use_gpu": use_gpu
                    }
                )
            )
            logger.info(f"Transcription completed for task {task_id}: {result}")
        
        self.upload_output_file() # Upload the output file to the storage sink

        os.remove(self.local_output) # Cleanup local output file
        r.set(f"task_progress:{self.task_id}", "--complete")
        progress_bar_callback("Transcribing... 100%")

        # !IMPORANT: do not change this flag, 
        # it is used to signal completion
        progress_bar_callback("--complete") 
   

    # Handle specific exceptions
    except exceptions.SoftTimeLimitExceeded as e:
        logger.warning(f"Task {task_id} exceeded soft time limit - NOT completing")
        r.set(f"task_progress:{task_id}", "Timed out - cleaning up")
        self.handle_task_failure(exc=e)
        raise e
    
    except StorageDownloadError as e:
        logger.error(f"Storage download error for task {task_id}: {str(e)}")
        self.handle_task_failure(exc=e)
        raise e

    except StorageUploadError as e:
        logger.error(f"Storage upload error for task {task_id}: {str(e)}")
        self.handle_task_failure(exc=e)
        raise e

    except exceptions.WorkerLostError as e:
        logger.error(f"Worker lost error for task {task_id}")
        raise e # Don't retry on worker lost - let Celery handle the requeue
    
    except Exception as e:
        logger.error(f"Task {task_id} failed with error: {str(e)}")
        self.handle_task_failure(exc=e)
        raise e  # Fatal error, do not retry

    finally:
        try:
            self.cleanup_old_chunks()
        except Exception as e:
            logger.warning(f"Failed to cleanup old chunks: {e}")

        # Cleanup Redis progress tracking
        try:
            r.delete(f"task_progress:{self.request.id}")
        except Exception as e:
            logger.warning(f"Failed to cleanup Redis progress: {e}")





































