import alsaaudio
import sys
import time
import queue



class AudioCapture:
    """
    A class to handle audio capture from ALSA devices, specifically designed for ultrasound capture.
    
    This class provides functionality to capture audio data from a specified ALSA device
    with configurable parameters such as sample rate, format, and buffer sizes.
    """
    
    def __init__(self, device_name="hw:CARD=Ultrasound,DEV=0"):
        """
        Initialize the audio capture device with specific ALSA parameters.
        
        Args:
            device_name (str): ALSA device identifier. Defaults to Ultrasound device.
        """
        self.device = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, 
                                    device=device_name, 
                                    channels=1,          # Mono audio capture
                                    rate=256000,         # 256kHz sample rate
                                    format=alsaaudio.PCM_FORMAT_S16_LE,  # 16-bit little-endian
                                    periodsize=1024*4,   # Buffer size for each period
                                    periods=4)           # Number of periods in the buffer

    def capture(self, runtime=1, data_queue=None, barrier=None):
        """
        Capture audio data for a specified duration.
        
        Args:
            runtime (float): Duration to capture audio in seconds. Defaults to 1 second.
            data_queue (Queue, optional): Queue to store captured audio data. If None,
                                        data is only printed to console.
            barrier (threading.Barrier, optional): Synchronization barrier for coordinated
                                                 start across multiple captures.
        """
        # Wait for synchronization if barrier is provided
        if barrier:
            barrier.wait()
        
        self.start_time = time.time()
        print(f"Starting capture at {self.start_time}")
        
        while time.time() - self.start_time < runtime:
            # Read data from the device
            # l: number of frames read (negative indicates buffer overflow)
            # data: the actual audio data
            l, data = self.device.read()
            
            if l > 0:
                # Successfully read data
                if data_queue:
                    data_queue.put(data)
                else:
                    print(f"Captured {l} bytes")
            elif l == 0:
                # No data available, continue to next iteration
                pass
            else:
                # Buffer overflow occurred
                print(f"Buffer overflow ({l})")
                
        self.stop_time = time.time()
        print(f"Stopping capture at {self.stop_time}")



if __name__ == "__main__":
    capture = AudioCapture()
    capture.capture()