import logging
import threading
from celery import Celery
from celery.signals import after_setup_logger, worker_ready
from app.settings import chunk_cleanup_timeout
from app.src.utils import cleanup_tmp

# -- Celery Worker App --

app = Celery("whisper_worker")      

app.config_from_object(f"app.celeryconfig") 
 
# Task auto-discovery   
app.conf.include = [ f"app.src.transcribe" ]  

@worker_ready.connect
def at_worker_start(
        **kwargs
    ) -> None:
    """Signal handler that runs when the worker is ready.
    This function starts a background thread to clean up temporary files.
    It uses the `cleanup_tmp` function defined in `app/src/utils.py`.
    """
    threading.Thread(
        target=cleanup_tmp,
        args=(chunk_cleanup_timeout,),
        name="cleanup_tmp_thread",
        daemon=True
    ).start()


@after_setup_logger.connect
def setup_loggers(
        logger, 
        *args, 
        **kwargs
    ) -> None:
    """Set up the logger for the worker.
    This function is called after the logger is set up.
    It clears existing handlers and sets a new StreamHandler with a specific format.
    """
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)