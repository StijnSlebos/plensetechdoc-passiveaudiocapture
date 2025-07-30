import paramiko
import time
import os
import socket
from datetime import datetime
import json

from RPI_pac_tcp_node import RPI_PAC_TCP_Node

import logging

COMMAND_SEPARATOR = "#"

class WindowsPACScheduler:
    def __init__(self, config: dict, logger: logging.Logger):
        self.rpi_pac_nodes: list[RPI_PAC_TCP_Node] = []
        self.config = config
        self.start_time = None
        self.runtime = 0.0
        self.logger = logger
        self.logger.info("~[sched] Building scheduler...")

        self.capture_tries_counter: int = 0
        self.capture_complete_status: list[bool] = []


    def add_rpi_pac_node(self, rpi_pac_node: RPI_PAC_TCP_Node):
        self.rpi_pac_nodes.append(rpi_pac_node)

    def update_rpi_pac_nodes(self, tries: int = 3):
        for rpi_pac_node in self.rpi_pac_nodes:
            for _ in range(tries):
                rpi_pac_node.test_tcp_connection(output=False)
                if rpi_pac_node.is_responsive():
                    break
                else:
                    self.logger.info(f"~[sched] tcpnode:{rpi_pac_node.ip_address}:{rpi_pac_node.port} - RPI_PAC_Node not active, trying again...")
                    time.sleep(1)
                    continue


    def schedule_capture(self, record_time_in_seconds: int) -> list[str]:
        self.update_rpi_pac_nodes()
        self.capture_tries_counter = 0

        current_time = datetime.now()
        # Find next 10 second interval at least 5s away
        self.start_time = ((int(current_time.timestamp()) // 10) + 1) * 10
        if self.start_time - current_time.timestamp() < 5:
            self.start_time += 10
        
        self.runtime = record_time_in_seconds
        self.logger.info(f"~[sched] Scheduling capture of {self.runtime} seconds at {self.start_time}") # <-------- LOGGER

        active_nodes_names = []
        for rpi_pac_node in self.rpi_pac_nodes:
            response = rpi_pac_node.start_recording(self.runtime, self.start_time)
            if not response.startswith("REC_START"):
                self.logger.error(f"~[sched] tcpnode:{rpi_pac_node.ip_address}:{rpi_pac_node.port} - Error starting recording; response: {response}") # <-------- LOGGER
            else:
                _, timestamp, waittime = response.split(COMMAND_SEPARATOR)
                rpi_pac_node.set_isactive(True)
                self.logger.info(f"~[sched] tcpnode:{rpi_pac_node.ip_address}:{rpi_pac_node.port} - Recording planned at {timestamp} in {waittime} seconds") # <-------- LOGGER
                active_nodes_names.append(rpi_pac_node.name)

        self.logger.info(f"~[sched] Active nodes: {active_nodes_names}")
        return active_nodes_names

    def schedule_calibration(self):
        # Same as schedule_capture, but with a different runtime and command.
        pass

    def is_capture_complete(self, active_nodes_names: list[str], tries: int = 10) -> bool:
        if self.capture_tries_counter == 0:
            self.capture_complete_status = [False] * len(active_nodes_names)

            if self.start_time is None or datetime.now().timestamp() < self.start_time + self.runtime:
                self.logger.info(f"~[sched] Capture not complete yet, returning False {datetime.now().timestamp()} < {self.start_time} + {self.runtime}")
                return False

        if self.capture_tries_counter < tries:
            active_rpi_pac_nodes = [rpi_pac_node for rpi_pac_node in self.rpi_pac_nodes if rpi_pac_node.name in active_nodes_names]
            self.logger.info(f"~[sched] polling active nodes: {active_rpi_pac_nodes}, attempt {self.capture_tries_counter} of {tries}")
            self.capture_tries_counter += 1

            for i, rpi_pac_node in enumerate(active_rpi_pac_nodes):
                if not rpi_pac_node.is_capture_complete():
                    self.logger.info(f"~[sched] tcpnode:{rpi_pac_node.ip_address}:{rpi_pac_node.port} - Capture not complete yet, RPI_PAC_Node returning False")
                    self.capture_complete_status[i] = False
                else:
                    self.capture_complete_status[i] = True

            if all(self.capture_complete_status):
                self.logger.info("~[sched] Capture complete!")
                return True
            else:
                self.logger.info(f"~[sched] Capture not complete yet, returning False {[f'{self.capture_complete_status[i]}:{rpi_pac_node.name}' for i, rpi_pac_node in enumerate(active_rpi_pac_nodes)]}")
                return False
        else:
            self.logger.info("~[sched] capture timeout, returning True")
            return True
    
    def is_calibration_complete(self) -> bool:
        # Same as is_capture_complete, but with a different runtime and command.
        pass




# if __name__ == "__main__":
#     config = json.load(open(os.path.join(os.path.dirname(__file__), 'config.json')))
#     scheduler = WindowsPACScheduler(config)

#     # for rpi_node in config['rpi_nodes']:
#     #     rpi_pac_node = RPI_PAC_Node(rpi_node['ip_address'], rpi_node['port'], config)
#     #     scheduler.add_rpi_pac_node(rpi_pac_node)
#     rpi_demo_node_config = config['rpi_demo_node']
#     rpi_demo_node = RPI_PAC_Node(rpi_demo_node_config['ip_address'], rpi_demo_node_config['port'], config)
#     # logging.info(f"{datetime.now()} - Adding RPI_PAC_Node {rpi_demo_node_config['ip_address']}:{rpi_demo_node_config['port']}")
#     scheduler.add_rpi_pac_node(rpi_demo_node)

#     scheduler.schedule_capture(10)
