import paramiko
import logging
import time

import os
import socket

from datetime import datetime
import json

COMMAND_SEPARATOR = '#'


class RPI_PAC_SCP_Node:
    def __init__(self, name: str, ip_address: str, config: dict, logger: logging.Logger):
        self.name = name
        self.ip_address = ip_address
        self.port = 22
        self.fetched_audio_files = []
        self.logger = logger
        self.logger.info(f"~[scp] Building SCP node for {self.name} at {self.ip_address}")

        self.config = config
        self.username = config['username']
        self.password = config['password']
        self.audio_file_prefix = config['audio_file_prefix']
        self.command_separator = COMMAND_SEPARATOR

    def test_scp_connection(self):
        try:
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.ip_address, port=self.port, username=self.username, password=self.password)
                self.logger.info(f"~[scp] Successfully connected to RPI_PAC_Node")
                return True
        except Exception as e:
            self.logger.error(f"~[scp] Error connecting to RPI_PAC_Node: {e}")
            return False

    def download_scp_file(self, local_directory_path: str, remote_directory_path: str, filename: str = None):
        try:
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.ip_address, port=self.port, username=self.username, password=self.password)
                self.logger.info(f"~[scp] Successfully connected to RPI_PAC_Node")

                with ssh.open_sftp() as sftp:
                    self.logger.info(f"~[scp] Successfully opened sftp connection to RPI_PAC_Node")

                    if not os.path.exists(local_directory_path):
                        os.makedirs(local_directory_path)

                    if filename is not None and filename in sftp.listdir(remote_directory_path):

                        remote_file_path = remote_directory_path + "/" + filename # linux style path
                        local_file_path = os.path.join(local_directory_path, filename) # windows style path
                        # try:
                        self.logger.info(f"~[scp] Downloading file {filename} from {remote_file_path} to {local_file_path}")
                        sftp.get(remote_file_path, local_file_path)
                        self.fetched_audio_files.append(filename)
                        self.logger.info(f"~[scp] Downloaded file {filename}")
                        # except Exception as e:
                        #     logging.error(f"{datetime.now()} - RPI_PAC_Node {self.ip_address}:{self.port} - [SCP] Error downloading file {filename}: {e}")
                    else:
                        self.logger.info(f"~[scp] File {filename} not found on RPI_PAC_Node")

                    # for file in sftp.listdir(remote_directory_path):
        except paramiko.AuthenticationException as e:
            self.logger.error(f"~[scp] Authentication failed: {str(e)}")
        except paramiko.SSHException as e:
            self.logger.error(f"~[scp] SSH error: {str(e)}")
        except Exception as e:
            self.logger.error(f"~[scp] Error downloading files: {e}")

    def delete_scp_file(self, remote_directory_path: str, filename: str):
        try:
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.ip_address, port=self.port, username=self.username, password=self.password)
                self.logger.info(f"~[scp] Successfully connected to RPI_PAC_Node")

                with ssh.open_sftp() as sftp:
                    self.logger.info(f"~[scp] Successfully opened sftp connection to RPI_PAC_Node")

                    remote_file_path = remote_directory_path + "/" + filename # linux style path
                    sftp.remove(remote_file_path)
                    self.logger.info(f"~[scp] Deleted file {filename}")

        except Exception as e:
            self.logger.error(f"~[scp] Error deleting file {filename}: {e}")


if __name__ == "__main__":
    config = json.load(open(os.path.join(os.path.dirname(__file__), 'config.json')))
    rpi_pac_scp_node = RPI_PAC_SCP_Node(config['rpi_demo_node']['ip_address'], config['rpi_demo_node']['port'], config)
    
    local_path = r"C:\Users\StijnSlebos\Downloads\run4_scp"
    remote_path = "/home/plense/passive_sensor_data/fetch_test"
    filename = "PZOrec_2025_04_02_16_42_Udev1.wav"

    rpi_pac_scp_node.download_scp_file(local_path, remote_path, filename)



