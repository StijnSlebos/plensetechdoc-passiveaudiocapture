import queue
import threading
import time
import os
from datetime import datetime
from audio_capture import AudioCapture
import soundfile as sf
import numpy as np


# Define hardware devices for ultrasound capture
# Each device represents a different ultrasound sensor
DEVICES = ["hw:CARD=Ultrasound,DEV=0", "hw:CARD=Ultrasound_1,DEV=0"] # , "hw:CARD=Ultrasound_1,DEV=0"

# Path where captured audio data will be stored
LOCAL_STORAGE_PATH = "/home/plense/passive_sensor_data/fetch_test"


class CaptureManager:
    """
    Manages multiple audio capture devices, handling concurrent recording and data storage.
    
    This class coordinates the capture of audio data from multiple ultrasound devices,
    manages temporary storage of raw data, and converts it to WAV format upon completion.
    
    Attributes:
        runtime (float): Duration of capture in seconds (default: 15.0)
    """
    
    def __init__(self, runtime=15.0):
        """
        Initialize the capture manager with specified runtime.
        
        Args:
            runtime (float): Duration of capture in seconds (default: 15.0)
        """
        self.number_of_devices = len(DEVICES)

        self.startup_sync_barrier = threading.Barrier(len(DEVICES)+1)
        
        self.queues = [queue.Queue() for _ in DEVICES]
        self.fetch_threads = [threading.Thread(target=self.capture, args=(i,)) for i in range(len(DEVICES))]

        self.dump_threads = [threading.Thread(target=self.fetch_dump_data, args=(i,)) for i in range(len(DEVICES))]
        self.status_update_thread = threading.Thread(target=self.status_update)

        self.running = False
        self.runtime = runtime

        self.capture_complete = False

        # create temp storage path
        self.temp_raw_storage_path = os.path.join(LOCAL_STORAGE_PATH, "temp_raw")
        os.makedirs(self.temp_raw_storage_path, exist_ok=True)

    def reset(self):
        # how would we do this in modern python?
        self.__init__()

    def capture(self, device_index):
        """
        Captures audio data from a specific device.
        
        Args:
            device_index (int): Index of the device in DEVICES list
        """
        capture = AudioCapture(DEVICES[device_index])
        capture.capture(runtime=self.runtime, data_queue=self.queues[device_index], barrier=self.startup_sync_barrier)

    def is_capture_complete(self):
        return self.capture_complete
    
    def is_capture_running(self):
        return self.running

    def start(self, runtime: int, start_time: int):
        """
        Starts all capture and processing threads.
        Initializes data capture from all devices simultaneously.
        """
        self.runtime = runtime
        self.start_time = start_time
        self.capture_complete = False

        self.running = True
        for thread in self.fetch_threads:
            thread.start()
        for thread in self.dump_threads:
            thread.start()
        self.status_update_thread.start()

        # Wait until the start time
        timer = threading.Timer(self.start_time - time.time(), self.startup_sync_barrier.wait)
        timer.start()
        timer.join()
        # logging.info(f"Capture started at {time.strftime('%H:%M:%S', time.localtime(time.time()))}")

    def stop(self):
        """
        Stops all running threads and performs cleanup operations.
        Converts raw data to WAV format before terminating.
        """
        self.running = False
        for thread in self.fetch_threads:
            thread.join()
        for thread in self.dump_threads:
            thread.join()
        self.status_update_thread.join()

        self.cleanup_raw_to_wav()
        self.capture_complete = True

    def fetch_dump_data(self, device_index):
        """
        Continuously fetches data from device queue and writes to temporary storage.
        
        Args:
            device_index (int): Index of the device queue to monitor
        """
        while self.running:
            q = self.queues[device_index]
            try:
                # Attempt to get data from queue with minimal timeout
                data = q.get(timeout=0.0001)
                try:
                    # Write binary data to temporary raw file
                    with open(f"{self.temp_raw_storage_path}/test_Udev{device_index}.raw", "ab") as f:
                        f.write(data)
                except Exception as e:
                    print(f"Error writing data to file: {e}")
            except queue.Empty:
                # Skip if no data available
                pass
    
    def status_update(self, interval = 5):
        """
        Periodically reports storage status of captured data.
        
        Args:
            interval (int): Time between status updates in seconds (default: 5)
        """
        start_bytes, start_files = self.get_bytes_on_path(self.temp_raw_storage_path)
        while self.running:
            time.sleep(interval)
            try:
                nbytes, nfiles = self.get_bytes_on_path(self.temp_raw_storage_path)
                print(f"Status: {nfiles-start_files} files, {(nbytes-start_bytes)/1024:.1f} KB stored")
            except Exception as e:
                print(f"Error getting status: {e}")
    
    def get_bytes_on_path(self, PATH: str):
        """
        Calculates total storage usage for a given directory.
        
        Args:
            PATH (str): Directory path to analyze
            
        Returns:
            tuple: (total_bytes, number_of_files)
        """
        # Get list of files in storage directory
        files = os.listdir(PATH)
        total_bytes = 0

        if len(files) > 1000:
            return total_bytes, len(files)
        else:
            # Calculate total size
            for file in files:
                file_path = os.path.join(PATH, file)
                total_bytes += os.path.getsize(file_path)
            
            return total_bytes, len(files)
        
    def cleanup_raw_to_wav(self):
        """
        Converts raw captured data to WAV format and performs cleanup.
        
        - Processes raw files for each device separately
        - Creates timestamped WAV files
        - Removes temporary raw files after conversion
        - Attempts to remove temporary directory if empty
        """

        files_in_temp_storage = os.listdir(self.temp_raw_storage_path)
        timestamp_ymd_hm = datetime.fromtimestamp(self.start_time).strftime("%Y_%m_%d_%H_%M_%S")
        for device_index in range(self.number_of_devices):
            device_files = [file for file in files_in_temp_storage if f"Udev{device_index}" in file]
            data = []
            for file in device_files:
                with open(os.path.join(self.temp_raw_storage_path, file), "rb") as f:
                    data.append(f.read())
            data_int16 = np.concatenate([np.frombuffer(d, dtype=np.int16) for d in data])
            # data = np.concatenate(data)

            sf.write(os.path.join(LOCAL_STORAGE_PATH, f"PZOrec_{timestamp_ymd_hm}_Udev{device_index}.wav"), data_int16, 256000, subtype="PCM_16")

            for file in device_files:
                os.remove(os.path.join(self.temp_raw_storage_path, file))
        
        if len(os.listdir(self.temp_raw_storage_path)) == 0:
            os.rmdir(self.temp_raw_storage_path)
        else:
            print(f"Warning: {len(os.listdir(self.temp_raw_storage_path))} files left in temp storage path, could not remove temp storage path")


if __name__ == "__main__":
    # Example usage when running as script
    capture = CaptureManager()  # Uses default 15 seconds runtime
    
    # Synchronize capture start with the beginning of the next minute
    current_time = time.time()
    print(f"Current time: {time.strftime('%H:%M:%S', time.localtime(current_time))}")
    
    next_minute = (int(current_time // 60) + 1) * 60
    print(f"Waiting until: {time.strftime('%H:%M:%S', time.localtime(next_minute))}")
    
    # Wait loop for not so precise timing
    while time.time() < next_minute:
        time.sleep(0.1)
        
    print(f"Waiting done, starting capture at {time.strftime('%H:%M:%S', time.localtime(time.time()))}")
    capture.start()

    # Run for specified duration
    start_time = time.time()
    while time.time() - start_time < capture.runtime:
        pass
    time.sleep(1)
    capture.stop()

    print("End of Capturing Sequence")


#  Exception in thread Thread-3 (capture):
# Traceback (most recent call last):
#   File "/usr/lib/python3.11/threading.py", line 1038, in _bootstrap_inner
#     self.run()
#   File "/usr/lib/python3.11/threading.py", line 975, in run
#     self._target(*self._args, **self._kwargs)
#   File "/home/plense/contact-edge-code/contact-edge-code/passive_audio_capture/capture_manager.py", line 20, in capture
#     capture = AudioCapture(DEVICES[device_index])
#               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/home/plense/contact-edge-code/contact-edge-code/passive_audio_capture/audio_capture.py", line 10, in __init__
#     self.device = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, device=device_name)
#                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# alsaaudio.ALSAAudioError: No space left on device [hw:CARD=Ultrasound_1,DEV=0]