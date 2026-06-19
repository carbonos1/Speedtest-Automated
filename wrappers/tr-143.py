'''
Wrapper for testing with TR-143 HTML based Servers.
This will fetch a file, as well as uploading a file. This is similar to what is done with speedtest Servers in something like TP-Link's TAUC.

NOTE: This is ChatGPT written at the moment, this will have to be refined.

'''
import time
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from ping3 import ping

class TR143Tester:
    def __init__(self, download_url, upload_url, upload_file_path, ping_host='google.com'):
        self.download_url = download_url
        self.upload_url = upload_url
        self.upload_file_path = upload_file_path
        self.ping_host = ping_host

    def download_test(self):
        start_time = time.time()
        response = requests.get(self.download_url, stream=True)
        response.raise_for_status()

        total_data = 0
        for chunk in response.iter_content(chunk_size=4096):
            if chunk:
                total_data += len(chunk)

        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time == 0:
            return 0.0
        download_speed_mbps = (total_data * 8) / (elapsed_time * 1_000_000)
        return download_speed_mbps

    def upload_test(self):
        with open(self.upload_file_path, 'rb') as f:
            m = MultipartEncoder(fields={'file': ('filename', f)})
            start_time = time.time()
            response = requests.post(self.upload_url, data=m, headers={'Content-Type': m.content_type})
            response.raise_for_status()
            end_time = time.time()

            elapsed_time = end_time - start_time
            total_data = m.len
            if elapsed_time == 0:
                return 0.0
            upload_speed_mbps = (total_data * 8) / (elapsed_time * 1_000_000)
        return upload_speed_mbps

    def measure_latency(self):
        latency = ping(self.ping_host)
        if latency is None:
            return None
        return latency * 1000

    def run_tests(self):
        print("Starting TR-143 compliant speed test...")

        download_speed = self.download_test()
        print(f"Download Speed: {download_speed:.2f} Mbps")

        upload_speed = self.upload_test()
        print(f"Upload Speed: {upload_speed:.2f} Mbps")

        latency = self.measure_latency()
        if latency is not None:
            print(f"Latency to {self.ping_host}: {latency:.2f} ms")
        else:
            print(f"Latency to {self.ping_host}: failed (host unreachable)")

# Example usage:
if __name__ == '__main__':
    download_url = "http://your-server.com/path/to/download/file"
    upload_url = "http://your-server.com/path/to/upload/endpoint"
    upload_file_path = "path/to/your/upload/file"

    tester = TR143Tester(download_url, upload_url, upload_file_path)
    tester.run_tests()
