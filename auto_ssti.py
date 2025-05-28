from urllib.parse import urlparse, parse_qs

from pyppeteer import launch
from server_utils import *
from payload_utils import *
from engine_utils import *




async def ssti_attack(success_symbols_lst, success_payloads_lst, symbols, page, url, request_type, attacked_parameter):
    # contains sanitized once
    modified_payloads = []

    payload, operation = create_payload(symbols)
    print(f"\nTrying symbols '{symbols}' with payload '{payload}'...")

    response = await inject_payload(page, url, payload, request_type, attacked_parameter)
    # print(response)

    result = str(eval(operation))
    success, resp_matches = validate_injection(result, response, symbols)
    if success:
        symb_start, symb_end = symbols.rsplit(" ", 1)
        symbols_in_response = False
        if symbols != " ":
            for match in resp_matches:
                if symb_start in match and symb_end in match:
                    symbols_in_response = True
                    break
            if not symbols_in_response:
                # check if current symbols have to be added or not
                store_symbols(success_symbols_lst, success_payloads_lst, symbols, payload)
        else:
            store_symbols(success_symbols_lst, success_payloads_lst, symbols, payload)

        print("Successful injection!")
        for match in resp_matches:
            print(match)
        print("Stored payload: ", success_payloads_lst)
    else:
        print("Failed injection.")
        # process to find if sanitization occurred
        # now inject legitimate data
        if request_type == "GET":
            query_params = parse_qs(urlparse(url).query)
            default_input = query_params.get(attacked_parameter, [None])[0]
        elif request_type == "POST":
            default_input = "abcdefghijklmno"

        legit_response = await inject_payload(page, url, default_input, request_type, attacked_parameter)
        # build the expected html response when payload is used

        exception_in_legit = find_exception_in_response(legit_response)
        if exception_in_legit:
            print("EXCEPTION in LEGIT response.", legit_response)
            # print("Response after payload injection: ", response)
            return response, []

        expected_response = legit_response.replace(default_input, payload)
        exception = check_if_exception(response, expected_response, symbols)
        if exception:
            print("EXCEPTION FOUND.")
            # print("Response after payload injection: ", response)
            return response, []

        modified_payloads = get_sanitized_payloads(response, expected_response, symbols, operation)
        modified_payloads = [mod for mod in modified_payloads]

    return response, modified_payloads


async def main(url, request_type, attacked_parameter):
    """
    url = "http://127.0.0.1:8080"
    # wait until the server is ready to send responses
    await check_server_ready(url)
    """
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
    break_from_symbols_for = False
    for symbols in te_symbols:
    # for symbols in ["string:{ }", "{ }"]:
        response, sanitized_payloads = await ssti_attack(success_symbols_lst, success_payloads_lst,
                                                         symbols, page, url, request_type, attacked_parameter)

        if sanitized_payloads:
            sanitized_payloads_by_symbols[symbols] = sanitized_payloads

        eng_names_lst = check_te_in_response(response, engines_dct)

        # eng_names_lst = []  # uncomment to disable TE recognition in response
        if eng_names_lst:
            print(f"\nTemplate engine name(s) found in the response! Engine(s): {eng_names_lst}")
            scanned_symbols = get_previous_keys(te_symbols, symbols, include_current=True)
            for eng_name in eng_names_lst:
                eng_symbols = load_symbols_by_engine(eng_name)
                for tags in eng_symbols:
                    if tags not in scanned_symbols:
                        scanned_symbols.append(tags)
                        response, new_sanit_payloads = await ssti_attack(success_symbols_lst, success_payloads_lst,
                                                                         tags, page, url, request_type, attacked_parameter)
                        if new_sanit_payloads:
                            sanitized_payloads_by_symbols[tags] = new_sanit_payloads
            break_from_symbols_for = True
        # no need to consider sanitized payloads in a response with exception
        if break_from_symbols_for:
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

    # """
    servers_lst = ["latte_tempeng/latte_server.php",
                   "raintpl_tempeng/raintpl.php",
                    "kajiki_tempeng/kajiki_server.py",
                    "spitfire_tempeng/spitfire_server.py",
                    "plates_tempeng/plates_server.php",
                    "quik_tempeng/server.py",
                    "evoque_tempeng/server.py",
                   ]

    for server in servers_lst:
        choice = ""
        server_process = launch_server(server)  # only needed to automatically launch servers from here

        print(f"SCANNING URL '{server}' ...")
        # asyncio.run(main(), debug=True)
        asyncio.run(main("http://127.0.0.1:8080", "POST", None), debug=True)
        # TODO: solve problems with same PHP engine being run repeatedly (PHP process to be killed)
        shutdown_server(server_process)
        # allow the user to stop execution before studying new server
        if server != servers_lst[-1]:
            while choice not in ["Y", "N"]:
                choice = input("\nWould you like to go on with the next server? (Y[Yes]/N[No]) ").upper()

        if choice == "N":
            break
        # """


    """
    # attacked_parameter = None in POST requests (maybe)
    tests_lst = [{"request_type": "POST",
                  "url": "http://127.0.0.1:8000/index.php?mact=News,cntnt01,detail,0&cntnt01articleid=1&cntnt01detailtemplate=Simplex%20News%20Detail&cntnt01returnid=1",
                  },
                 {"request_type": "GET",
                  "url": "http://127.0.0.1:8000/index.php?mact=News,cntnt01,detail,0&cntnt01articleid=1&cntnt01detailtemplate=Simplex%20News%20Detail&cntnt01returnid=1",
                  "attacked_parameter": "cntnt01detailtemplate"},
                 ]
    for test in tests_lst:
        choice = ""
        url = test["url"]
        request_type = test["request_type"]
        if request_type == "GET":
            attacked_parameter = test["attacked_parameter"]
        else:
            attacked_parameter = None

        print(f"SCANNING URL '{url}' for a {request_type} request ...")
        if attacked_parameter is not None:
            print(f"Url parameter to test: {test['attacked_parameter']}")

        asyncio.run(main(url, request_type, attacked_parameter), debug=True)

        # allow the user to stop execution before studying new server
        if test != tests_lst[-1]:
            while choice not in ["Y", "N"]:
                choice = input("\nWould you like to go on with the next url? (Y[Yes]/N[No]) ").upper()

        if choice == "N":
            break
        """

