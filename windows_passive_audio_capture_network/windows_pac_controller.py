import json
import os
import threading
import logging
from datetime import datetime
import time

import queue


from RPI_pac_tcp_node import RPI_PAC_TCP_Node
from RPI_pac_scp_node import RPI_PAC_SCP_Node
from windows_pac_scheduler import WindowsPACScheduler
from windows_pac_file_handler import WindowsPACFileHandler
from windows_pac_plotter import WindowsPACPlotter
import windows_pac_logger as logger_


class WindowsPACController:
    """
    This class is responsible for coordinating the passive audio capture process.
    It schedules captures, fetches audio files, processes them, and updates the dashboard.
    """
    def __init__(self, config: dict, demo_mode: bool = False):
        self.config = config
        logger_.configure_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("~[pac-ctrl] Building controller...") # TODO: add logger to all classes

        self.scheduler = WindowsPACScheduler(config, self.logger)
        self.file_handler = WindowsPACFileHandler(config, self.logger)

        self.rpi_pac_nodes = []
        self.rpi_pac_scp_nodes = []

        if demo_mode:
            config_nodes = [config['rpi_demo_node']]
        else:
            config_nodes = config['rpi_nodes']

        for rpi_pac_node in config_nodes:
        # for rpi_pac_node in [config['rpi_demo_node']]:
            self.rpi_pac_nodes.append(RPI_PAC_TCP_Node(
                rpi_pac_node['name'],
                rpi_pac_node['ip_address'],
                rpi_pac_node['port'],
                config,
                self.logger
            ))
            self.rpi_pac_scp_nodes.append(RPI_PAC_SCP_Node(
                rpi_pac_node['name'],
                rpi_pac_node['ip_address'],
                config,
                self.logger
            ))

        for rpi_pac_node in self.rpi_pac_nodes:
            self.file_handler.add_rpi_pac_node(rpi_pac_node)
            self.scheduler.add_rpi_pac_node(rpi_pac_node)
        for rpi_pac_scp_node in self.rpi_pac_scp_nodes:
            self.file_handler.add_rpi_scp_node(rpi_pac_scp_node)
            
        self.plotter = WindowsPACPlotter()

    def passive_audio_capture(self, runtime=15.0, calibrate=False):
        # print(self.config)

        # 0. Check if calibration is needed, if so, schedule calibration
        if calibrate:
            self.logger.info("~[pac-ctrl] Scheduling calibration...")
            self.scheduler.schedule_calibration()

        # 1. Schedule capture
        self.logger.info(f"~[pac-ctrl] Scheduling capture of {runtime} seconds")
        self.scheduler.schedule_capture(runtime)

        # 3. Poll/Wait for capture to complete
        while True:
            time.sleep(5)
            self.logger.info("~[pac-ctrl] Polling for capture to complete...")
            if self.scheduler.is_capture_complete():
                self.logger.info("~[pac-ctrl] Capture complete!")
                break

        # 4. Find audio files + fetch them over scp & save to folder
        self.logger.info("~[pac-ctrl] Fetching audio files...")
        self.file_handler.fetch_audio_files()


        # 5. process audio files

        # 6. plot results in html

        # 7. update dashboard

        pass

    def run_sequence(self, runtime=15.0, repetitions=1, calibrate=False):
        self.running = True

        file_path_queue = queue.Queue()
        process_audio_files_thread = threading.Thread(target=self.process_audio_files_thread, args=(file_path_queue,))
        process_audio_files_thread.start()

        passive_audio_capture_thread = threading.Thread(target=self.passive_audio_capture_thread, args=(file_path_queue, runtime, repetitions, calibrate))
        passive_audio_capture_thread.start()

        while self.running:
            time.sleep(1)

        passive_audio_capture_thread.join()
        process_audio_files_thread.join()

    def passive_audio_capture_thread(self, file_path_queue: queue.Queue, runtime=15.0, repetitions=1, calibrate=False):
        try:
            for _ in range(repetitions):
                self.logger.info(f"~[pac-ctrl] Running passive audio capture {_ + 1} of {repetitions}")
                
                active_nodes_names = self.scheduler.schedule_capture(runtime)
                
                if not active_nodes_names:
                    self.logger.info("~[pac-ctrl] No active nodes, skipping capture")
                    continue

                while True:
                    time.sleep(10)
                    self.logger.info("~[pac-ctrl] Polling for capture to complete...")
                    if self.scheduler.is_capture_complete(active_nodes_names):
                        self.logger.info("~[pac-ctrl] Capture complete!")
                        break
                
                self.logger.info("~[pac-ctrl] polling for audio files...")
                remote_audio_file_paths = self.file_handler.get_remote_audio_file_paths()
                        
                file_path_queue.put(remote_audio_file_paths)
        except Exception as e:
            self.logger.error(f"~[pac-ctrl] Error in passive audio capture thread: {e}")
        finally:
            self.logger.info("~[pac-ctrl] Passive audio capture thread finished, setting running to False")
            self.running = False

    def process_audio_files_thread(self, file_path_queue):
        while self.running or not file_path_queue.empty():
            try:
                remote_audio_file_paths = file_path_queue.get()
                if remote_audio_file_paths is None:
                    self.logger.info("~[pac-ctrl] No audio files to process")
                    time.sleep(10)
                    continue
                else:
                    self.logger.info(f"~[pac-ctrl] Processing audio files: {remote_audio_file_paths}")
                    self.file_handler.fetch_audio_files(remote_audio_file_paths)
            except Exception as e:
                self.logger.error(f"~[pac-ctrl] Error processing audio files: {e}")
                time.sleep(10)


if __name__ == "__main__":
    config = json.load(open(os.path.join(os.path.dirname(__file__), 'config.json')))
    controller = WindowsPACController(config, demo_mode=True)
    controller.run_sequence(runtime=10.0, repetitions=2, calibrate=False)

