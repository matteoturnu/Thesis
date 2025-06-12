import json
from urllib.parse import urlparse, parse_qs

from pyppeteer import launch
from server_utils import *
from payload_utils import *
from engine_utils import *


async def ssti_attack(success_symbols_lst, success_payloads_lst, symbols, page, url, injection_point, param_to_attack):
    # contains sanitized once
    modified_payloads = []

    payload, operation = create_payload(symbols)
    print(f"\nTrying symbols '{symbols}' with payload '{payload}'...")

    response = await inject_payload(page, url, payload, injection_point, param_to_attack)
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
        # print("Response: ", response)
        # process to find if sanitization occurred
        # now inject legitimate data
        default_input = ""
        if injection_point == "URL":
            query_params = parse_qs(urlparse(url).query)
            default_input = query_params.get(param_to_attack, [None])[0]
        elif injection_point == "PAGE":
            default_input = "abcdefghijklmno"

        legit_response = await inject_payload(page, url, default_input, injection_point, param_to_attack)
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



def add_template_engine(new_engine, new_language, te_symbols_dct):
    supported_symbols = []
    print(f"Template engine to add: {new_engine} ({new_language})")
    user_input = ""
    print("Type the symbols supported by the new template engine (press 0 to finish)")
    print("Include a space where the string should be inserted. Ex: '{ }' for symbols '{}'")
    i = 0
    while user_input != "0":
        user_input = input(f"Symbols ({i + 1}): ")
        if user_input != 0 and " " in user_input:
            supported_symbols.append(user_input)
            i += 1

    for new_symbs in supported_symbols:
        if new_symbs in te_symbols_dct:
            # just add the engine in the already-existing symbols dict
            te_symbols_dct[new_symbs][new_engine] = new_language
        else:
            # add dictionary with new symbols and new template engine
            te_symbols_dct[new_symbs] = {new_engine: new_language}

    if not supported_symbols:
        print(f"No symbols added. Engine has not been added.")
    else:
        write_to_json("te_symbols.json", te_symbols_dct)
        print(f"Engine '{new_engine}' ({new_language}) added!")


async def main(url, injection_point, param_to_attack):
    # launch browser without GUI
    browser = await launch({"headless": True})
    page = await browser.newPage()

    print("\n-----------------------")
    print("--- DETECTION PHASE ---")
    print("-----------------------")

    te_symbols = read_from_json("te_symbols.json")
    engines_dct = load_engines(te_symbols)

    symbols_to_test = te_symbols

    success_symbols_lst = []
    old_success_syms_lst = []
    scanned_symbols = set()
    success_payloads_lst = []
    sanitized_payloads_by_symbols = dict()
    engines_tested = []
    # break_from_symbols_for = False

    lang_names_lst = set()
    for symbols in symbols_to_test:
        # for symbols in ["string:{ }", "{ }"]:
        if symbols in scanned_symbols:
            continue

        # if symbols == "{{ }}":
            # print("Hi")

        scanned_symbols.add(symbols)
        response, sanitized_payloads = await ssti_attack(success_symbols_lst, success_payloads_lst,
                                                         symbols, page, url, injection_point, param_to_attack)

        if sanitized_payloads:
            sanitized_payloads_by_symbols[symbols] = sanitized_payloads

        # eng_names_lst = check_te_in_response(response, engines_dct, engines_tested)
        # not so reliable: used in the end to see if we can reduce the template engines found
        eng_names_lst, lang_names_lst = check_te_in_response(response, engines_dct, engines_tested)
        # if lang_names_lst:
            # print(f"\nLanguage(s) found in the response! Language(s): {lang_names_lst}")

        # eng_names_lst = []  # uncomment to disable TE recognition in response
        if eng_names_lst:
            print(f"\nTemplate engine name(s) found in the response! Engine(s): {eng_names_lst}")


            old_success_syms_lst = success_symbols_lst[:]

            for eng_name in eng_names_lst:
                engines_tested.append(eng_name)
                eng_symbols = load_symbols_by_engine(eng_name)
                for tags in eng_symbols:
                    if tags not in scanned_symbols:
                        scanned_symbols.add(tags)
                        response, new_sanit_payloads = await ssti_attack(success_symbols_lst, success_payloads_lst,
                                                                         tags, page, url, injection_point,
                                                                         param_to_attack)
                        if new_sanit_payloads:
                            sanitized_payloads_by_symbols[tags] = new_sanit_payloads

        if eng_names_lst and len(old_success_syms_lst) == len(success_symbols_lst):
            print("No new successful symbols after finding engine name keyword. Continuing with remaining symbols...")
            # remaining_symbols_to_scan = [sym for sym in te_symbols if sym not in scanned_symbols]
        else:
            # MAYBE BREAK ONLY WHEN 80/90% OF SUCCESSFUL PAYLOADS ASSOCIATED TO A CERTAIN ENGINE, WHOSE NAME HAS BEEN FOUND
            # IN THE RESPONSE PAGE, ARE FOUND. OTHERWISE, GO BACK TO SCAN THE SYMBOLS OF ANY TEMPLATE ENGINE.
            break



    await browser.close()

    print("\n-----------------------")
    print("------- RESULTS -------")
    print("-----------------------")
    if success_payloads_lst:
        print("\nSome successful payloads have been found:\n", success_payloads_lst)
        print(f"Target template engine(s): ")
        # simple_dict, te_dct = find_template_engines(success_symbols_lst)
        simple_dict, te_dct = find_template_engines(success_symbols_lst, lang_names_lst)
        show_engines(simple_dict, te_dct)
    else:
        print("No successful payload has been found.")

    if sanitized_payloads_by_symbols:
        print("Some payloads seem to have been sanitized:")
        print(sanitized_payloads_by_symbols)

if __name__ == "__main__":

    """
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
        """

    supported_args = ["--url", "--param", "--add-engine"]
    # ex: auto_ssti.py --url ... --param ...
    # print(len(sys.argv))
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print(f"Usage: {sys.argv[0]} {supported_args[0]} <url> [{supported_args[1]} <param>]")
        print(f"\t{sys.argv[0]} {supported_args[2]} <engine>:<language>")
        sys.exit()

    # --url
    if sys.argv[1] == supported_args[0]:
        url = sys.argv[2]
        if len(sys.argv) == 5:
            param_to_attack = sys.argv[4]
            if param_to_attack not in url:
                print(f"URL does not include the parameter '{param_to_attack}'")
                sys.exit()

            injection_point = "URL"
        else:
            injection_point = "PAGE"
            param_to_attack = None

        print(f"Scanning URL '{url}' for injection in {injection_point} elements...")
        if param_to_attack is not None:
            print(f"Url parameter to test: {param_to_attack}")

        asyncio.run(main(url, injection_point, param_to_attack), debug=True)

    # --add-engine
    if sys.argv[1] == supported_args[2]:
        allowed_languages = ["Java", "C", "C#", "VB.NET", "PHP", "Python", ".NET", "Perl", "CFML", "JavaScript",
                             "Ruby", "Go", "Rust", "F#", "Golang"]
        eng_lang = sys.argv[2]
        if ":" not in eng_lang:
            print(f"\t{sys.argv[0]} --add-engine <engine>:<language>")
            sys.exit(1)

        new_eng_lang = eng_lang.split(":")
        if len(new_eng_lang) != 2:
            print(f"\t{sys.argv[0]} --add-engine <engine>:<language>")
            sys.exit(2)

        new_eng, new_lang = new_eng_lang
        te_symbols = read_from_json("te_symbols.json")
        engines = load_engines(te_symbols)
        # map key lowercase to key case saved in json
        engine_key_map = {k.lower(): k for k in engines}

        if new_eng.lower() in engine_key_map:
            # get the original case of the engine name saved in json file
            new_eng = engine_key_map[new_eng.lower()]
            lang = engines[new_eng]
            print(f"Template engine '{new_eng}' ({lang}) is already supported.")
            sys.exit(3)

        lang_key_map = {e.lower(): e for e in allowed_languages}
        if new_lang.lower() not in lang_key_map:
            print(f"Programming language '{new_lang}' is not supported.")
            sys.exit(4)

        add_template_engine(new_eng, new_lang, te_symbols)

    ######################

    """
    tests_lst = [{"request_type": "GET",
                  "url": "http://127.0.0.1:8000/index.php?mact=News,cntnt01,detail,0&cntnt01articleid=1&cntnt01detailtemplate=Simplex%20News%20Detail&cntnt01returnid=1",
                  "attacked_parameter": "cntnt01detailtemplate"},
                 {"request_type": "GET",
                  "url": "http://127.0.0.1:8000/?any_par=something",
                  "attacked_parameter": "any_par"},
                {"request_type": "POST",
                  "url": "http://127.0.0.1:8000/index.php?mact=News,cntnt01,detail,0&cntnt01articleid=1&cntnt01detailtemplate=Simplex%20News%20Detail&cntnt01returnid=1",
                  },

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
