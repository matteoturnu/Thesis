import re
import json5
from te_symbols import te_symbols
from simple_utils import get_html_diffs

def load_engines(te_dct):
    te_lst = dict()
    for _, engines in te_dct.items():
        te_lst.update(engines)
    return te_lst


def load_symbols_by_engine(engine):
    eng_symbols = []
    for tags, engines in te_symbols.items():
        if engine in engines:
            eng_symbols.append(tags)
    return eng_symbols

def filter_engines_by_language(simple_dict, engines, languages):
    most_likely_engines = dict()
    if simple_dict:
        for eng_name, eng_lang in engines.items():
            for lang in languages:
                if lang == eng_lang:
                    most_likely_engines[eng_name] = eng_lang
    else:
        for eng, sym_lang in engines.items():
            for lang in languages:
                if lang == sym_lang["language"]:
                    most_likely_engines[eng] = sym_lang

    return most_likely_engines



def find_template_engines(success_symbols, lang_names_lst):
    target_engines = {}
    engines_by_symbols = {}
    simple_dict = True

    # load all the existing engines based on the successful symbols
    # shape: {"<eng_name>": {"symbols": <symbols>, "language": <lang>}, ...}
    for symbols in success_symbols:
        for te, lang in te_symbols[symbols].items():
            if te not in engines_by_symbols:
                engines_by_symbols[te] = {"symbols": {symbols}, "language": lang}
            else:
                engines_by_symbols[te]["symbols"].add(symbols)

    unique_engines = set(engines_by_symbols.keys())
    most_likely_engines = dict()
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

        """
        if lang_names_lst:
            most_likely_engines = filter_engines_by_language(simple_dict, possible_engines, lang_names_lst)
        else:
            most_likely_engines = possible_engines
         return False, most_likely_engines
        """
        return simple_dict, possible_engines

    """
    if lang_names_lst:
        most_likely_engines = filter_engines_by_language(simple_dict, target_engines, lang_names_lst)
    else:
        most_likely_engines = target_engines
    return True, most_likely_engines
    """
    return simple_dict, target_engines


def check_te_in_response(response, eng_lang_dct, engines_tested):
    eng_strings_found = list()
    lang_strings_found = set()
    for eng, lang in eng_lang_dct.items():
        if eng != "Any" and re.search(eng, response, re.IGNORECASE):
            # engine_found = eng
            if eng not in engines_tested:
                eng_strings_found.append(eng)
        if lang != "Any" and re.search(lang, response, re.IGNORECASE):
            lang_strings_found.add(lang)


    return eng_strings_found, lang_strings_found

"""
def check_te_in_response(response, eng_lang_dct, engines_tested):
    # TODO: usually problematic with words like "templates" and the supported engine "Plates"
    eng_strings_found = list()
    # engine_found = ""
    for eng, lang in eng_lang_dct.items():
        if eng != "Any" and re.search(eng, response, re.IGNORECASE):
            # engine_found = eng
            if eng not in engines_tested:
                eng_strings_found.append(eng)

    return eng_strings_found
"""


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