import os, subprocess, threading
import sys
import psutil
import aiohttp, asyncio

def read_output(stream, prefix):
    """Reads output from a stream and prints it with a prefix."""
    while True:
        line = stream.readline()
        if not line:
            break
        # print(f"[{prefix}] {line.strip()}")


def launch_server(server_relpath):
    # set the correct working directory when launching the subprocess of spitfire_server.py
    server_directory = os.path.dirname(os.path.abspath(server_relpath))
    server_file = server_relpath.split("/")[1]
    if server_relpath.split(".")[1] == "php":
        args = ["php", "-S", "127.0.0.1:8080", server_file]
    else:
        # we suppose it's Python then
        args = [sys.executable, "-u", server_file]  # `-u` ensures unbuffered output

    server_process = subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        cwd=server_directory
    )

    # Start separate threads for stdout and stderr
    threading.Thread(target=read_output, args=(server_process.stdout, server_file), daemon=True).start()
    threading.Thread(target=read_output, args=(server_process.stderr, server_file + "-ERROR"), daemon=True).start()

    return server_process


def shutdown_server(process):
    """ shutdown the main process and all its children"""
    parent_process = psutil.Process(process.pid)
    for child in parent_process.children(recursive=True):
        child.kill()
    parent_process.kill()


async def check_server_ready(url):
    # Wait for the server to be available
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # wait for a POST request handled correctly
                async with session.post(url, data={"test": "value"}) as response:
                    if response.status == 200:
                        print(f"Server is up at {url}")
                        return True
            except:
                pass
            print("Waiting for server to be ready...")
            await asyncio.sleep(1)  # Check every second

