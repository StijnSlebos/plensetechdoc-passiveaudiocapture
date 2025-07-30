import os


from RPI_pac_tcp_node import RPI_PAC_TCP_Node
from RPI_pac_scp_node import RPI_PAC_SCP_Node 

import logging

class WindowsPACFileHandler:
    def __init__(self, config: dict, logger: logging.Logger):
        self.rpi_pac_nodes: list[RPI_PAC_TCP_Node] = []
        self.rpi_scp_nodes: list[RPI_PAC_SCP_Node] = []
        self.logger = logger
        self.logger.info("~[fileh] Building file handler...")

        self.config = config

        self.local_storage_path = config['local_storage_path']
        self.remote_storage_path = config['remote_storage_path']

    def add_rpi_pac_node(self, rpi_pac_node):
        self.rpi_pac_nodes.append(rpi_pac_node)

    def add_rpi_scp_node(self, rpi_scp_node):
        self.rpi_scp_nodes.append(rpi_scp_node)
        os.makedirs(os.path.join(self.local_storage_path, rpi_scp_node.name), exist_ok=True)
    
    def fetch_audio_files(self, remote_audio_file_paths: dict[str, list[str]] = None, delete_remote_files: bool = True):
        
        remote_audio_file_paths = remote_audio_file_paths or self.get_remote_audio_file_paths()
        
        for rpi_name, remote_audio_file_paths in remote_audio_file_paths.items():
            for remote_audio_file_path in remote_audio_file_paths:
                fetch_success = self.fetch_audio_file([rpi_name, remote_audio_file_path])
                if fetch_success:
                    if delete_remote_files:
                        self.logger.info(f"~[fileh] deleting remote file {remote_audio_file_path}")
                        self.delete_remote_audio_file([rpi_name, remote_audio_file_path])
                    else:
                        self.logger.info(f"~[fileh] not deleting remote file")
                else:
                    self.logger.info(f"~[fileh] failed to fetch audio file {remote_audio_file_path} from {rpi_name}")

    def get_remote_audio_file_paths(self) -> dict[str, list[str]]:
        remote_audio_file_paths = {}
        for rpi_pac_node in self.rpi_pac_nodes:
            files = rpi_pac_node.list_audio_files()
            if files:
                remote_audio_file_paths[rpi_pac_node.name] = files
        # self.logger.info(f"~[fileh] Remote audio file paths: {remote_audio_file_paths}")
        return remote_audio_file_paths
    
    def fetch_audio_file(self, remote_audio_file_path: tuple[str, str]) -> bool:
        self.logger.info(f"~[fileh] Trying to fetch audio file {remote_audio_file_path[1]} from {remote_audio_file_path[0]}")
        success = False

        try:
            for rpi_scp_node in self.rpi_scp_nodes:
                if rpi_scp_node.name == remote_audio_file_path[0]:
                    self.logger.info(f"~[fileh] Fetching audio file {remote_audio_file_path[1]} from {remote_audio_file_path[0]}")
                    node_specific_local_storage_path = os.path.join(self.local_storage_path, rpi_scp_node.name)
                    
                    rpi_scp_node.download_scp_file(node_specific_local_storage_path, self.remote_storage_path, remote_audio_file_path[1])
                    
                    if os.path.exists(os.path.join(node_specific_local_storage_path, remote_audio_file_path[1])):
                        self.logger.info(f"~[fileh] Audio file {remote_audio_file_path[1]} fetched from {remote_audio_file_path[0]}")
                        success = True
                        break
                    else:
                        self.logger.info(f"~[fileh] Audio file {remote_audio_file_path[1]} not found on {remote_audio_file_path[0]}")
                        success = False
                    
                else:
                    self.logger.info(f"~[fileh] No RPI SCP node found for {remote_audio_file_path[0]}")
                    success = False
        except Exception as e:
            self.logger.error(f"~[fileh] Error fetching audio file {remote_audio_file_path[1]} from {remote_audio_file_path[0]}: {e}")
            success = False

        return success

    def delete_remote_audio_file(self, remote_audio_file_path: tuple[str, str]):
        try:
            for rpi_scp_node in self.rpi_scp_nodes:
                if rpi_scp_node.name == remote_audio_file_path[0]:
                    # self.logger.info(f"~[fileh] Deleting audio file {remote_audio_file_path[1]} from {remote_audio_file_path[0]}")
                    rpi_scp_node.delete_scp_file(self.remote_storage_path, remote_audio_file_path[1])
        except Exception as e:
            self.logger.error(f"~[fileh] Error deleting audio file {remote_audio_file_path[1]} from {remote_audio_file_path[0]}: {e}")
