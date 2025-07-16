from datetime import datetime
import logging
import threading
import socket
import time
import os
from pac_capture_manager import CaptureManager
from pac_file_manager import FileManager
from pac_calibration_manager import CalibrationManager
import pac_logger as logger_

TCP_HOST = '0.0.0.0'  # Listen on all interfaces
TCP_PORT = 5001       # Arbitrary port (can be changed)

COMMAND_SEPARATOR = '#'

# Path where captured audio data will be stored
LOCAL_STORAGE_PATH = "/home/plense/passive_sensor_data/fetch_test"


class PACController:
    def __init__(self):
        self.capture_manager: CaptureManager = CaptureManager()
        self.file_manager: FileManager = FileManager(directory=LOCAL_STORAGE_PATH)
        self.calibration_manager: CalibrationManager = CalibrationManager()

        logger_.configure_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Building controller...")

    def start_tcp_server(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((TCP_HOST, TCP_PORT))
                s.listen()
                self.logger.info(f"[INFO] Server listening on {TCP_HOST}:{TCP_PORT}")
                while True:
                    conn, addr = s.accept()
                    self.handle_client(conn, addr)
        except Exception as e:
            self.logger.error(f"[ERROR] Error starting server: {e}")
        # finally:
        #     s.close()
        #     self.logger.info(f"[INFO] Server closed")

    def handle_client(self, conn, addr):
        self.logger.info(f"[INFO] Connection with {addr} established")
        try:
            with conn:
                while True:
                    data = conn.recv(1024).decode()

                    if not data:
                        break
                    self.logger.info(f"[RECV] Received: {data}")

                    # Callback: respond based on the command
                    if data == "IS_CAPTURE_COMPLETE":
                        response = "CAPTURE_COMPLETE" if self.capture_manager.is_capture_complete() else "False"
                        self.logger.info(f"[INFO] request for capture complete: {response}")
                    elif data == "START_CALIBRATION":
                        pass
                        # response = self.calibration_manager.start_calibration()
                    elif data == "IS_CALIBRATION_COMPLETE":
                        pass
                        # response = self.calibration_manager.is_calibration_complete()
                    elif data == "LIST_AUDIO_FILES":
                        files = self.file_manager.return_new_files()
                        response = f"FILES{COMMAND_SEPARATOR}{len(files)}"
                        for file in files:
                            response += f"{COMMAND_SEPARATOR}{file}"
                    elif data == "FETCH_AUDIO_FILE":
                        pass
                    elif data == "RESET":
                        self.capture_manager.reset()
                        self.file_manager.reset()
                        response = "RESET"
                    elif data.startswith("START_RECORDING"):
                        if self.capture_manager.is_capture_running():
                            response = "Capture already running"
                        else:
                            # Parse the command
                            _, record_time_fstr, start_time_fstr = data.split(COMMAND_SEPARATOR)
                            current_time = time.time()
                            record_time = float(record_time_fstr)
                            start_time = float(start_time_fstr)
                            self.recording_thread = threading.Thread(target=self.CMD_start_recording, args=(record_time, start_time))
                            self.recording_thread.start()
                            response = f"REC_START{COMMAND_SEPARATOR}{datetime.fromtimestamp(start_time).strftime('%Y-%m-%d_%H-%M-%S')}{COMMAND_SEPARATOR}{start_time - current_time:.1f}"
                    else:
                        response = "Unknown command"
                        self.logger.info(f"[CONF] Unknown Content in command: {data}")

                    conn.sendall(response.encode())
        except Exception as e:
            self.logger.error(f"[ERROR] Error handling client: {e}, {data}")
        finally:
            conn.close()
            self.logger.info(f"[INFO] Connection with {addr} closed")

    def CMD_start_recording(self, record_time, start_time):
        self.logger.info(f"[INFO] Starting recording for {record_time} seconds at {start_time}")
        self.file_manager.update_files()

        cleanup = False
        try:
            self.capture_manager.reset()
            self.capture_manager.start(record_time, start_time)

            time.sleep(record_time)
            self.logger.info(f"[INFO] Stopping recording")

            self.capture_manager.stop()
            self.file_manager.update_new_files()
            cleanup = True
        except Exception as e:
            self.logger.error(f"[ERROR] Error during recording: {e}")
        finally:
            # Ensure cleanup happens even if an error occurs
            if not cleanup:
                self.capture_manager.stop()

            # Delete old files after new recording is complete
            self.file_manager.delete_old_files(hours=3.0) # leave in for now, log if used
            self.file_manager.update_files()


if __name__ == "__main__":
    pac_controller = PACController()
    pac_controller.start_tcp_server()
