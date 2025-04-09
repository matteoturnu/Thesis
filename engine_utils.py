import re
from te_symbols import te_symbols

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


def check_te_in_response(response, eng_lang_dct):
    engine_found = ""
    for eng, lang in eng_lang_dct.items():
        if re.search(eng, response, re.IGNORECASE):
            engine_found = eng
            break

    return engine_found



def show_engines(simple_dict, te_dct):
    if simple_dict:
        [print(f"--> {te} ({lang})") for te, lang in te_dct.items()]
    else:
        [print(f"--> {te} ({symb_lang['language']}), for symbols {list(symb_lang['symbols'])})")
         for te, symb_lang in te_dct.items()]