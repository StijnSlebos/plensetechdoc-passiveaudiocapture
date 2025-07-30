import logging
import time
import os
import socket
from datetime import datetime

COMMAND_SEPARATOR = '#'


class RPI_PAC_TCP_Node:
    def __init__(self, name: str, ip_address: str, port: int, config: dict, logger: logging.Logger = None):
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.fetched_audio_files = []

        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        self.config = config
        self.username = config['username']
        self.password = config['password']
        self.audio_file_prefix = config['audio_file_prefix']
        self.command_separator = COMMAND_SEPARATOR

        self.isresponsive = False
        self.isactive = False
        self.test_tcp_connection()

    def test_tcp_connection(self, output: bool = True):
        try:
            with socket.create_connection((self.ip_address, self.port), timeout=5) as s:
                if output:
                    self.logger.info(f"~[tcp] tcpnode:{self.ip_address}:{self.port} - Successfully connected to RPI_PAC_Node")
                self.isresponsive = True
        except Exception as e:
            if output:
                self.logger.error(f"~[tcp] tcpnode:{self.ip_address}:{self.port} - Error connecting to RPI_PAC_Node: {e}")
            self.isresponsive = False

    def start_recording(self, record_time_in_seconds: int, start_time: int):
        try:
            command = "START_RECORDING" + self.command_separator + str(record_time_in_seconds) + self.command_separator + str(start_time)
            response = RPI_PAC_TCP_Node.send_tcp_command(self.ip_address, self.port, command)

            return response
        except Exception as e:
            self.logger.error(f"~[tcp] tcpnode:{self.ip_address}:{self.port} - Error starting recording: {e}")
            self.isresponsive = False
            return f"ERROR: {e}"

    def set_isresponsive(self, isresponsive: bool):
        self.isresponsive = isresponsive

    def is_responsive(self) -> bool:
        return self.isresponsive
    
    def set_isactive(self, isactive: bool):
        self.isactive = isactive

    def is_active(self) -> bool:
        return self.isactive
    
    def start_calibration(self):
        command = "START_CALIBRATION"
        response = RPI_PAC_TCP_Node.send_tcp_command(self.ip_address, self.port, command)
        return response

    def is_capture_complete(self) -> bool:
        # request the status of the recording
        command = "IS_CAPTURE_COMPLETE"
        response = RPI_PAC_TCP_Node.send_tcp_command(self.ip_address, self.port, command)
        if response == "CAPTURE_COMPLETE":
            return True
        else:
            return False

    def is_calibration_complete(self) -> bool:
        # request the status of the calibration
        command = "IS_CALIBRATION_COMPLETE"
        response = RPI_PAC_TCP_Node.send_tcp_command(self.ip_address, self.port, command)
        if response == "CALIBRATION_COMPLETE":
            return True
        else:
            return False
    
    def list_audio_files(self):
        # dont think this is needed
        command = "LIST_AUDIO_FILES"
        response = RPI_PAC_TCP_Node.send_tcp_command(self.ip_address, self.port, command)
        if response.startswith("FILES"):
            files = response.split(self.command_separator)[2:]
            return files
        else:
            self.logger.error(f"~[tcp] tcpnode:{self.ip_address}:{self.port} - Error listing audio files: {response}")
            return []

    @staticmethod
    def send_tcp_command(ip_address: str, port: int, command: str):
        try:
            with socket.create_connection((ip_address, port), timeout=5) as s:
                s.sendall(command.encode())
                received_data = s.recv(1024).decode()
                logging.info(f"~[@st tcp] tcpnode:{ip_address}:{port} - Received data: {received_data}")
                return received_data
        except Exception as e:
            logging.error(f"~[@st tcp] tcpnode:{ip_address}:{port} - Error sending command: {e}")
            return f"ERROR: {e}"
