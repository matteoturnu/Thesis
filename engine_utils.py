import re
from te_symbols import te_symbols
from simple_utils import get_html_diffs

def load_engines():
    te_lst = dict()
    for _, engines in te_symbols.items():
        te_lst.update(engines)
    return te_lst


def load_symbols_by_engine(engine):
    eng_symbols = []
    for tags, engines in te_symbols.items():
        if engine in engines:
            eng_symbols.append(tags)
    return eng_symbols


def find_template_engines(success_symbols):
    target_engines = {}
    engines_by_symbols = {}
    simple_dict = True

    # load all the existing engines based on the successful symbols
    # shape: {"<eng_name>": {"symbols": <symbols>, "language": <lang>}, ...}
    for symbols in success_symbols:
        #include_te = True  <-- part of code in the comments
        for te, lang in te_symbols[symbols].items():

            """
            for syms, engines in te_symbols.items():
                # PROBLEM: it should skip the code context version of the same symbols too! 
                # ex: symbols = syms = "{ }", then skip "}{ " as well
                if syms == symbols:
                    continue
                if te in engines and syms not in success_symbols:
                    # te is compatible with symbols found to be non-useful for injection
                    include_te = False
                    break

            if include_te:
            """
            if te not in engines_by_symbols:
                engines_by_symbols[te] = {"symbols": {symbols}, "language": lang}
            else:
                engines_by_symbols[te]["symbols"].add(symbols)

    unique_engines = set(engines_by_symbols.keys())
    for eng in unique_engines:
        # check which engines support ALL the successful symbols found
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
        return simple_dict, possible_engines

    return simple_dict, target_engines


def check_te_in_response(response, eng_lang_dct):
    eng_strings_found = list()
    # engine_found = ""
    for eng, lang in eng_lang_dct.items():
        if eng != "Any" and re.search(eng, response, re.IGNORECASE):
            # engine_found = eng
            eng_strings_found.append(eng)

    return eng_strings_found


def find_exception_in_response(response):
    # TODO: consider response codes and headers as well!
    resp_lowercase = response.lower()
    error_keywords = ["traceback", "exception", "error"]
    for keyword in error_keywords:
        if keyword in resp_lowercase:
            return True
    return False



def check_if_exception(actual_resp, exp_resp, delimiters):
    # first simple check through error keywords
    if find_exception_in_response(actual_resp):
        return True

    # other checks: length of the two responses and finding symbols
    # changes_minus, changes_plus = get_html_diffs(actual_resp, exp_resp)
    changes_plus, changes_minus = get_html_diffs(actual_resp, exp_resp)
    if len(changes_minus) != len(changes_plus):
        return True

    for exp, actual in zip(changes_minus, changes_plus):
        delimiter_start = delimiters.split(" ")[0]
        try:
            idx_end = exp.index(delimiter_start)
            # safer: consider idx_end-1
            # a@a default input for email gives problems otherwise
            # take the static html before delimiter_start
            exp_substr = exp[:idx_end-1]
            if exp_substr not in actual:
                return True
        except ValueError:
            # TODO: consider this case too for exceptions!
            print("[ValueError] Symbols may have been escaped!")

    return False




def show_engines(simple_dict, te_dct):
    if simple_dict:
        [print(f"--> {te} ({lang})") for te, lang in te_dct.items()]
    else:
        [print(f"--> {te} ({symb_lang['language']}), for symbols {list(symb_lang['symbols'])})")
         for te, symb_lang in te_dct.items()]