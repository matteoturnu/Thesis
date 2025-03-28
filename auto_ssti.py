import asyncio
import re
import random
import signal
import sys
import threading

import aiohttp
import psutil
from pyppeteer import launch
from te_symbols import te_symbols
import subprocess
import os


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


def generate_numbers_for_product():
    # Define the lower and upper bounds for a 10-digit to 18-digit product
    lower_bound = 10 ** 9  # 10 digits
    upper_bound = 10 ** 18  # 18 digits
    # Find two random numbers whose product is within the desired range
    while True:
        num1 = random.randint(10 ** 4, 10 ** 9)  # Random number for num1 (4 to 9 digits)
        num2 = random.randint(10 ** 4, 10 ** 9)  # Random number for num2 (4 to 9 digits)
        product = num1 * num2
        if lower_bound <= product < upper_bound:
            return num1, num2, product


def create_payload(symbols):
    # generate random numbers for the payload product
    num_1, num_2, _ = generate_numbers_for_product()
    operation = f"{num_1}*{num_2}"
    if " " in symbols:
        # replace the space with the actual operation
        payload = symbols.replace(" ", operation)
    else:
        # payload = "#set $num=7*7#$num"
        payload = symbols + operation
    # in the future, return only the payload
    return payload, operation


async def exec_payload(form, payload):
    # find the input text areas
    input_txt_lst = await form.querySelectorAll("input[type=\"text\"]")
    # write the payload inside every input text area of the form
    for input_txt in input_txt_lst:
        await input_txt.type(payload)
    # find the button element and click
    btn = await form.querySelector("input[type='submit'], button[type='submit']")
    await btn.click()


async def scraper(page, url, payload):
    await page.goto(url)
    # search for all the existing forms in the page first
    forms_lst = await page.querySelectorAll("form")
    html_resp = ""
    for form_idx in range(len(forms_lst)):
        curr_form = forms_lst[form_idx]
        try:
            await exec_payload(curr_form, payload)
            # be careful for real web sites: check if the context changes
            await page.waitForNavigation()
            html_resp += await page.content()
            # go back to previous page and look for other forms
            await page.goBack()
            # refresh element references (with button click they are lost)
            forms_lst = await page.querySelectorAll("form")
        except Exception as e:
            print(e)
    return html_resp


def validate_injection(op_res, html_resp):
    success = False
    responses_lst = list()
    res_matches = None
    # match number in scientific notation
    res_matches = list(re.finditer(op_res, html_resp))
    if res_matches:
        success = True
        for match in res_matches:
            start, end = max(0, match.start() - 20), min(len(html_resp), match.end() + 20)
            responses_lst.append(html_resp[start:end])

    return success, responses_lst


def store_symbols(symbols_lst, payloads_lst, new_symbols, new_payload):
    # e.g. avoid to add "{{ }}" if the list already contains successful symbols "{ }"
    symbols_are_contained = False
    for success_symbols in symbols_lst:
        if success_symbols in new_symbols:
            symbols_are_contained = True
            break
        elif new_symbols in success_symbols:
            # e.g. success_symbols = ["{{ }}"] and curr_symbols = "{ }"
            # replace with the simplest form
            symbols_are_contained = True
            idx_success_symbols = symbols_lst.index(success_symbols)
            symbols_lst[idx_success_symbols] = new_symbols
            payloads_lst[idx_success_symbols] = new_payload

    # if the list is still empty or the same symbols have been found in the non-empty list
    if not symbols_lst or not symbols_are_contained:
        symbols_lst.append(new_symbols)
        payloads_lst.append(new_payload)


def find_template_engines(success_symbols):
    target_engines = {}
    engines_by_symbols = {}
    simple_dict = True

    for symbols in success_symbols:
        for te, lang in te_symbols[symbols].items():
            if te not in engines_by_symbols:
                engines_by_symbols[te] = {"symbols": {symbols}, "language": lang}
            else:
                engines_by_symbols[te]["symbols"].add(symbols)

    unique_engines = set(engines_by_symbols.keys())
    for eng in unique_engines:
        if len(engines_by_symbols[eng]["symbols"]) == len(success_symbols):
            target_engines[eng] = engines_by_symbols[eng]["language"]

    if not target_engines:
        simple_dict = False
        possible_engines = {}
        # save the maximum number of symbols a template engine recognises
        max_n_symbols = max(len(data["symbols"]) for data in engines_by_symbols.values())
        for eng in unique_engines:
            if len(engines_by_symbols[eng]["symbols"]) == max_n_symbols:
                possible_engines[eng] = {"symbols": engines_by_symbols[eng]["symbols"],
                                     "language": engines_by_symbols[eng]["language"]}
        return simple_dict, possible_engines,

    return simple_dict, target_engines



async def main():
    url = "http://127.0.0.1:8080"
    # wait until the server is ready to send responses
    await check_server_ready(url)
    # launch browser without GUI
    browser = await launch({"headless": True})
    page = await browser.newPage()

    print("\n-----------------------")
    print("--- DETECTION PHASE ---")
    print("-----------------------")

    success_symbols_lst = []
    success_payloads_lst = []

    for curr_symbols in te_symbols:
        payload, operation = create_payload(curr_symbols)
        print(f"\nTrying symbols '{curr_symbols}' with payload '{payload}'...")

        response = await scraper(page, url, payload)
        result = str(eval(operation))
        success, resp_matches = validate_injection(result, response)
        if success:
            # check if current symbols have to be added or not
            store_symbols(success_symbols_lst, success_payloads_lst, curr_symbols, payload)

            print("Successful injection!")
            for match in resp_matches:
                print(match)
        else:
            print("Failed injection.")

    await browser.close()

    print("\n-----------------------")
    print("------- RESULTS -------")
    print("-----------------------")
    if success_payloads_lst:
        print("\nSome successful payloads have been found:\n", success_payloads_lst)
        print(f"Target template engine(s): ")
        simple_dict, te_dct = find_template_engines(success_symbols_lst)
        if simple_dict:
            [print(f"--> {te} ({lang})") for te, lang in te_dct.items()]
        else:
            [print(f"--> {te} ({symb_lang['language']}), for symbols {list(symb_lang['symbols'])})")
                for te, symb_lang in te_dct.items()]

    else:
        print("No successful payload has been found.")


if __name__ == "__main__":
    ### USE THIS PIECE OF CODE IF YOU ONLY EXECUTE auto_ssti.py ###

    servers_lst = ["latte_tempeng/latte_server.php", "spitfire_tempeng/spitfire_server.py",
                   "plates_tempeng/plates_server.php"]

    for server in servers_lst:
        choice = ""
        server_process = launch_server(server)  # only needed to automatically launch servers from here
        asyncio.run(main())
        shutdown_server(server_process)

        # server_process.wait()

        # allow the user to stop execution before studying new server
        if server != servers_lst[-1]:
            while choice not in ["Y", "N"]:
                choice = input("\nWould you like to go on with the next server? (Y[Yes]/N[No]) ").upper()

        if choice == "N":
            break

    ##### EXECUTING spitfire_server.py FIRST AND THEN auto_ssti.py
    """
    asyncio.run(main())
    """
