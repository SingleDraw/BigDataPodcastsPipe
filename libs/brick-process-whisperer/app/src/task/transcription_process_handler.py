import os
import logging
import sys
import traceback
from multiprocessing import Process, Queue
from celery.exceptions import SoftTimeLimitExceeded
from app.src.broker import broker as r  # Redis client for tracking progress
from app.src.helpers import (
    parse_timestamp, get_audio_duration, 
    progress_bar_callback
)
from typing import Optional

_max_duration = float(os.getenv("CHUNK_MAX_DURATION", 600))
_task_soft_time_limit = float(os.getenv("TASK_SOFT_TIME_LIMIT", 600))   # soft timeout: raises SoftTimeLimitExceeded

# Set up logging for the module
logger = logging.getLogger("whisperer")

import psutil

class TranscriptionProcessHandler:
    def __init__(
            self,
            task_id: str = None,
            chunked_source: list = None,
            local_input: str = None,
            local_output: str = None,
            _local_output: str = None,
            max_duration: float = _max_duration,
            language: Optional[str] = None,
            use_gpu: bool = False,
    ):
        self.task_id = task_id
        self.chunked_source = chunked_source or []
        self.local_input = local_input
        self.local_output = local_output
        self._local_output = _local_output or f"/tmp/{task_id}_output.txt"
        self.max_duration = max_duration
        self.language = language
        self.use_gpu = use_gpu
        self.chunk_pattern = f"/tmp/chunk_*.{task_id}.txt"

    def run_transcription(
            self,
            kwargs: dict
    ):
        """
        Run the transcription process in a separate managed process.
        This is used to handle SoftTimeLimitExceeded properly.
        """
                # Multiprocessing with function reference (for CPU-bound tasks)
                # For SoftTimeLimitExceeded, we need to use multiprocessing and join on timeout
                # NOTE: celery worker pool must be set to "solo" or "threading" to use this method,
                # prefably "threading" for better performance and flower compatibility
        queue = Queue()
        proc = Process(
            target=TranscriptionProcessHandler._transcribe_wrapper,
            args=(queue,),
            kwargs=kwargs
        )
        proc.start()
        proc.join(_task_soft_time_limit)

        if proc.is_alive():
            """
            If the process is still alive after the timeout,
            we need to kill the process tree and raise a SoftTimeLimitExceeded exception.
            This makes SoftTimeLimitExceeded work as expected.
            """
            msg = f"Task {self.task_id} exceeded soft time limit of {_task_soft_time_limit}s"
            logger.warning(msg)
            self.kill_process_tree(proc.pid)
            proc.join()
            raise SoftTimeLimitExceeded(msg)
        else:
            """
            Process completed successfully in time.
            We can safely get the result from the queue.
            """
            result = queue.get()
            return result  # Return the result from the queue


    def kill_process_tree(
            self,
            pid
        ):
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            parent.kill()
        except psutil.NoSuchProcess:
            pass
        finally:
            logger.warning(
                f"Process tree with PID {pid} killed "
                f"due to defined timeout of {_task_soft_time_limit}s"
            )

    @staticmethod
    def _transcribe_wrapper(
            queue, 
            *args, 
            **kwargs
        ):
        """
        Wrapper function for the transcription worker.
        This is needed to avoid issues with multiprocessing and method references.
        It runs in a separate process and puts the result into the queue.
        """
        try:
            result: str = TranscriptionProcessHandler.transcribe_worker_function(*args, **kwargs)
            queue.put(result)
        except Exception as e:
            queue.put(traceback.format_exc())



    @staticmethod
    def transcribe_worker_function(
        chunk_files: list,
        task_id: str = None,
        local_input: str = None,
        local_output: str = None,
        _local_output: str = None,
        max_duration: float = _max_duration,
        language: Optional[str] = None,
        use_gpu: bool = False,
    ) -> str:
        """
        Worker function that runs in separate process.
        Must be static or pure function to avoid issues with multiprocessing.
        This function handles the transcription of audio chunks using the Faster Whisper model.
        """
        
        logger.info(f"Worker process started for task {task_id}")
        
        try:
            # whisper import moved here to avoid issues with multiprocessing
            from faster_whisper import WhisperModel
            
            r.set(f"task_progress:{task_id}", "Preparing model...")
            model = WhisperModel(
                "tiny", 
                compute_type="int8", 
                device="cuda" if use_gpu else "cpu"
            )

            last_reported_progress = -1

            for i, chunk_file in enumerate(chunk_files):

                chunk_result = f"/tmp/chunk_{i}_{task_id}.txt"
                chunk_duration = get_audio_duration(chunk_file)
                """
                whisper transcribe method returns a generator of segments.
                Each segment contains start and end timestamps, and the transcribed text.
                """
                segments_generator, _ = model.transcribe(chunk_file)

                # Write to ephemeral chunk result
                with open(chunk_result, "w", encoding="utf-8") as cf:
                    # yield segments and write them to the file
                    for segment in segments_generator:
                        cf.write(
                            f"[{parse_timestamp(segment.start + i * max_duration)} --> "
                            f"{parse_timestamp(segment.end + i * max_duration)}] "
                            f"{segment.text.strip()}\n"
                        )

                        progress = min(int(((i + segment.end / chunk_duration) / len(chunk_files)) * 100), 100)

                        if progress > last_reported_progress:
                            r.set(f"task_progress:{task_id}", f"Transcribing... {progress}%")
                            progress_bar_callback(f"Transcribing... {progress}%")
                            last_reported_progress = progress

                # Append to final output only after chunk success
                with open(_local_output, "a", encoding="utf-8") as f:
                    with open(chunk_result, "r", encoding="utf-8") as cf:
                        f.write(cf.read())
                    # Cleanup chunk result after appending
                    os.remove(chunk_result)

                # Cleanup
                os.remove(chunk_file)

            # Final rename when done
            os.rename(_local_output, local_output)

            # Delete model after use
            del model

            return f"Transcription completed for task {task_id}"
            
        except Exception as e:
            logger.error(f"Worker process failed for task {task_id}: {e}")
            raise e


