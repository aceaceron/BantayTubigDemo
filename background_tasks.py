# background_tasks.py
import time
import threading
from water_quality import train_machine_learning

from threading import Thread, Event
from ml_models.main_processor import run_ml_analysis
from ml_models.feedback_loop import retrain_models_with_feedback

def _train_model_thread_periodic():
    """The actual function that runs in the background."""
    # Run once at the start
    print("Initial model training initiated...")
    train_machine_learning()
    print("Initial model training completed.\n")
    
    # Then, run periodically
    while True:
        # Wait for 30 minutes (1800 seconds) before the next run
        time.sleep(1800)
        print("Periodic model training initiated...")
        train_machine_learning()
        print("Periodic model training completed (if data available).\n")

def start_training_thread():
    """Creates and starts the background training thread."""
    training_thread = threading.Thread(target=_train_model_thread_periodic)
    training_thread.daemon = True # Allows the main app to exit even if this thread is running
    training_thread.start()
    print("Background model training thread has started.")


# --- Assume you have a scheduler setup, like APScheduler or a simple loop ---

def run_background_tasks(stop_event):
    """Main loop for running scheduled tasks."""
    last_ml_run = 0
    ml_run_interval = 3600 # Run every hour (3600 seconds)

    last_retrain_run = 0
    retrain_interval = 86400 # Run once a day

    while not stop_event.is_set():
        now = time.time()

        # HOURLY: Run the main anomaly detection and forecasting
        if now - last_ml_run > ml_run_interval:
            print("BACKGROUND: Triggering hourly ML analysis...")
            try:
                run_ml_analysis()
                last_ml_run = now
            except Exception as e:
                print(f"BACKGROUND ERROR in run_ml_analysis: {e}")

        # DAILY: Run the retraining process with new feedback
        if now - last_retrain_run > retrain_interval:
            print("BACKGROUND: Triggering daily model retraining...")
            try:
                retrain_models_with_feedback()
                last_retrain_run = now
            except Exception as e:
                print(f"BACKGROUND ERROR in retrain_models_with_feedback: {e}")

        time.sleep(60) # Check every minute