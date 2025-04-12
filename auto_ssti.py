import asyncio
import html
import re
import random
import sys
import threading

import aiohttp
import psutil
from pyppeteer import launch
from te_symbols import te_symbols
import subprocess
import os

from server_utils import *
from payload_utils import *
from engine_utils import *



async def ssti_attack(success_symbols_lst, success_payloads_lst, symbols, page, url):
    # contains sanitized once
    modified_payloads = []

    payload, operation = create_payload(symbols)
    print(f"\nTrying symbols '{symbols}' with payload '{payload}'...")

    response = await inject_payload(page, url, payload)
    # print(response)

    result = str(eval(operation))
    success, resp_matches = validate_injection(result, response)
    if success:
        # check if current symbols have to be added or not
        store_symbols(success_symbols_lst, success_payloads_lst, symbols, payload)

        print("Successful injection!")
        for match in resp_matches:
            print(match)
    else:
        print("Failed injection.")

        # process to find if sanitization occurred
        # now inject legitimate data
        default_input = "abcdefghijklmno"
        legit_response = await inject_payload(page, url, default_input)

        # build the expected html response when payload is used
        expected_response = legit_response.replace(default_input, payload)
        modified_payloads = get_html_changes(response, expected_response)

        # ex: email get changed to "a@a" if the payload is invalid because of a client-side check
        # modified_payloads will contain this value as the old and new html responses are different

        modified_payloads = [mod for mod in modified_payloads if operation in mod]

    return response, modified_payloads


async def main():
    url = "http://127.0.0.1:8080"
    # wait until the server is ready to send responses
    await check_server_ready(url)
    # launch browser without GUI
    browser = await launch({"headless": False})
    page = await browser.newPage()

    print("\n-----------------------")
    print("--- DETECTION PHASE ---")
    print("-----------------------")

    success_symbols_lst = []
    success_payloads_lst = []
    engines_dct = load_engines()
    sanitized_payloads_by_symbols = dict()
    #for symbols in te_symbols:
    for symbols in ["<? ?>", "{ }", "{= }"]:
        response, sanitized_payloads = await ssti_attack(success_symbols_lst, success_payloads_lst, symbols, page, url)
        if sanitized_payloads:
            sanitized_payloads_by_symbols[symbols] = sanitized_payloads
        eng_name = check_te_in_response(response, engines_dct)
        if eng_name != "":
            print(f"\nTemplate engine '{eng_name}' found in the response! ")
            # retrieve the symbols recognized by the engine
            eng_symbols = load_symbols_by_engine(eng_name)
            for tags in eng_symbols:
                if tags not in success_symbols_lst:
                    await ssti_attack(success_symbols_lst, success_payloads_lst, tags, page, url)
            break

    await browser.close()

    print("\n-----------------------")
    print("------- RESULTS -------")
    print("-----------------------")
    if success_payloads_lst:
        print("\nSome successful payloads have been found:\n", success_payloads_lst)
        print(f"Target template engine(s): ")
        simple_dict, te_dct = find_template_engines(success_symbols_lst)
        show_engines(simple_dict, te_dct)
    else:
        print("No successful payload has been found.")

    if sanitized_payloads_by_symbols:
        print("Some payloads seem to have been sanitized:")
        print(sanitized_payloads_by_symbols)


if __name__ == "__main__":
    ### USE THIS PIECE OF CODE IF YOU ONLY EXECUTE auto_ssti.py ###

    servers_lst = ["spitfire_tempeng/spitfire_server.py", "latte_tempeng/latte_server.php", "plates_tempeng/plates_server.php", ]

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
