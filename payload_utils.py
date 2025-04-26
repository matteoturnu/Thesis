import asyncio
import difflib
import random
import re
import string
import urllib.parse
import html


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


def on_btn_request(dom_reloaded, obj):
    async def is_request(request):
        if request.isNavigationRequest() and request.method == "POST":
            # submit button case (form)
            if not dom_reloaded.done():
                dom_reloaded.set_result(True)
                await request.continue_()
        elif not dom_reloaded.done():
            # js-navigation button, ajax request
            dom_reloaded.set_result(False)
            obj["request_obj"] = request
        else:
            await request.continue_()

    return lambda request: asyncio.create_task(is_request(request))


def on_link_request(result, obj):
    async def is_request(request):
        if not result.done():
            result.set_result(True)
            obj["request_obj"] = request

    return lambda request: asyncio.create_task(is_request(request))


def get_response_text(resp_future, resp_obj):
    async def on_response(response):
        if not resp_future.done():
            try:
                html_txt = await response.text()
                resp_obj["response"] = html_txt
                resp_future.set_result(True)
            except asyncio.InvalidStateError:
                print("[on_response] InvalidStateError")
            except Exception as e:
                print("[on_response] Error capturing response: ", e)
                resp_future.set_result(False)

    return lambda response: asyncio.create_task(on_response(response))

async def capture_response(future_var, obj):
    resp = ""
    try:
        await asyncio.wait_for(future_var, 3)
    except asyncio.TimeoutError:
        print("[TimeoutError] No response obtained after 3 seconds.")
        future_var = asyncio.Future()

    if future_var.done() and obj["response"]:
        resp = obj["response"]

    return resp

async def compute_request(page, payload, handler_obj, resp_handler, resp_future, resp_obj):
    html_resp = ""
    req_url = handler_obj["request_obj"].url
    if "?" in req_url:
        page.once("response", resp_handler)
        # new url obtained
        new_url = edit_url_query(req_url, payload)
        await handler_obj["request_obj"].continue_({"url": new_url})
        await page.setRequestInterception(False)
        # resp_future may need to be returned! (global)
        html_resp = await capture_response(resp_future, resp_obj)
    else:
        await handler_obj["request_obj"].continue_()
        await page.setRequestInterception(False)

    return html_resp


def backwards_scan(new_line, payload_start, payload_end, prev_end, delimiter_end, del_end_len):

    while payload_start > prev_end and new_line[payload_start - 1] not in string.whitespace:
        if new_line[payload_start - 1].isalnum() or new_line[payload_start - 1] == '>':
            break
        if delimiter_end != "" and (payload_start - del_end_len) > prev_end:
            # look for payload delimiters
            if new_line[payload_start - del_end_len - 1:payload_start - 1] == delimiter_end:
                # met ending delimiters of a previous payload, so stop scanning backwards
                break

        payload_start -= 1
    prev_end = payload_end

    return payload_start, prev_end

def forwards_scan(new_line, payload_end, start_next, delimiter_end, del_start_len, del_end_len):

    while payload_end < start_next and new_line[payload_end] not in string.whitespace:
        if new_line[payload_end] == '<' or new_line[payload_end] == ',':
            break
        if delimiter_end != "" and (payload_end + del_start_len) < start_next:
            # look for payload delimiters
            if new_line[payload_end:payload_end + del_start_len] == delimiter_end:
                # met ending delimiters of the current payload, so add them to payload and exit
                payload_end += del_end_len
                break
        payload_end += 1

    return payload_end



def get_sanitized_payloads(new_html, old_html, symbols, operation):
    # HYPOTHESIS: operation is never sanitized (ex: no 7/*7 or anything similar) but payload is
    # ENHANCEMENT: use a blacklist of symbols for which stopping scan
    # ex: "," and "!" for forward scanning

    changes_minus = []
    changes_plus = []
    diff_iter = difflib.ndiff(old_html.splitlines(), new_html.splitlines())
    for line in diff_iter:
        if line.startswith('+ '):
            changes_plus.append(line.strip("+ "))
        elif line.startswith('- '):
            changes_minus.append(line.strip("- "))

    diffs = []
    last_i_saved = -1
    for i in range(0, len(changes_minus)):
        new_chars_idx = []
        old_line = changes_minus[i]
        new_line = changes_plus[i]
        matcher = difflib.SequenceMatcher(None, old_line, new_line)
        if operation not in new_line or operation not in old_line:
            continue
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ('replace', 'insert', 'delete'):
                new_chars_idx.append([j1, j2])

        # considering only two cases: e.g. symbols "$" and symbols like "${ }"
        if len(symbols) > 1:
            delimiter_start, delimiter_end = symbols.split(" ")
        else:
            delimiter_start = symbols
            delimiter_end = ""

        del_start_len = len(delimiter_start)
        del_end_len = len(delimiter_end)

        prev_end = 0
        for j in range(len(new_chars_idx)):
            payload_start = new_chars_idx[j][0]
            payload_end = new_chars_idx[j][1]

            payload_start, prev_end = backwards_scan(new_line, payload_start, payload_end, prev_end, delimiter_end, del_end_len)

            if j + 1 > len(new_chars_idx) - 1:
                start_next = len(new_line)
            else:
                start_next = new_chars_idx[j + 1][0]
            payload_end = forwards_scan(new_line, payload_end, start_next, delimiter_end, del_start_len, del_end_len)

            changed_payload = new_line[payload_start:payload_end]
            if changed_payload:
                merged_payloads = False
                if operation not in changed_payload and diffs:
                    if i == last_i_saved and changed_payload not in diffs[-1]:
                        # case where both delimiters sanitized: do a merge between this payload
                        # and the last one saved in the list
                        max_overlap = 0
                        for idx in range(1, min(len(diffs[-1]), len(changed_payload)) + 1):
                            if diffs[-1][-idx:] == changed_payload[:idx]:
                                max_overlap = idx
                        changed_payload = diffs[-1] + changed_payload[max_overlap:]
                        merged_payloads = True

                if changed_payload not in diffs:
                    if merged_payloads:
                        diffs[-1] = changed_payload
                        last_i_saved = i
                    elif all(d not in changed_payload and changed_payload not in d for d in diffs):
                        # ensure a list element is not contained in the payload and vice-versa
                        diffs.append(changed_payload)
                        last_i_saved = i

    return diffs


async def exec_payload_in_inputs(page, button_elem, payload, url):
    # find the input text areas
    input_type_lst = await page.querySelectorAll('input[type]:not([type="reset"])'
                                                 ':not([type="submit"])'
                                                 ':not([type="button"])'
                                                 ':not([type="image"])')
    input_type_lst += await page.querySelectorAll('textarea, select')

    # write the payload inside every input text area of the form
    for input_element in input_type_lst:
        element_type = await page.evaluate('(el) => el.type', input_element)

        if element_type in ["text", "password", "search", "tel", "url", "textarea"]:
            await input_element.type(payload)

        # NOTE: consider select-option, hidden as well...
        elif element_type in ["radio", "checkbox", "hidden"]:
            # old_value = await page.evaluate("(el) => el.value", input_element)
            await page.evaluate("(el, value) => el.value = value", input_element, payload)
            # new_value = await page.evaluate("(el) => el.value", input_element)
            # print(f"Old value: {old_value}; new value: {new_value}")
            if element_type in ["radio", "checkbox"]:
                await input_element.click()

        elif element_type in ["email"]:
            await input_element.type(payload + "@a")
            # check email validity
            if not await page.evaluate("(el) => el.validity.valid", input_element):
                # if invalid, change it with a valid one and leave it
                await page.evaluate("(el, value) => el.value = value", input_element, "a@a")

        elif element_type in ["select-one", "select-multiple"]:
            select_name = await page.evaluate("(el) => el.name", input_element)
            selector = f"select[name='{select_name}']"
            select_options = await page.querySelectorAll('option')
            for option in select_options:
                # change both the option value and the label content
                await page.evaluate("(el, value) => {"
                                    "el.value = value;"
                                    "el.textContent = value }", option, payload)
                # select-one: at the end only the last one will be selected
                await page.select(selector, payload)



    html_resp = ""

    dom_reloaded = asyncio.Future()
    handler_obj = {"request_obj": None}
    req_handler = on_btn_request(dom_reloaded, handler_obj)
    await page.setRequestInterception(True)
    page.on("request", req_handler)

    resp_future = asyncio.Future()
    resp_obj = {"response": None}
    resp_handler = get_response_text(resp_future, resp_obj)

    await button_elem.click()
    try:
        await asyncio.wait_for(dom_reloaded, 3)
    except asyncio.TimeoutError:
        print("No request within 3 seconds")
        # done() happens when the task is completed or if it raised an exception
        # reset variable
        dom_reloaded = asyncio.Future()

    page.remove_listener("request", req_handler)
    if dom_reloaded.done() and dom_reloaded.result() is True:
        page.once("response", resp_handler)
        await page.setRequestInterception(False)
        html_resp = await capture_response(resp_future, resp_obj)

    elif dom_reloaded.done():  # and if it's False
        # ajax or js-nav button
        html_resp = await compute_request(page, payload, handler_obj, resp_handler, resp_future, resp_obj)

    else:
        await page.setRequestInterception(False)

    await page.goto(url)

    return html_resp


def edit_url_query(url, query):
    url, query_params = tuple(url.split("?"))
    query_params = query_params.split("&")
    new_queries = "?"
    for key_value in query_params:
        key = key_value.split("=")[0]
        new_queries += f"{key}={query}&"

    # delete last "&" in the query
    enc_queries = urllib.parse.quote(new_queries[:-1], safe="*?=&")
    new_url = url + enc_queries
    return new_url


async def exec_payload_in_link(page, link_elem, payload, url):
    html_resp = ""

    result = asyncio.Future()
    handler_obj = {"request_obj": None}
    req_handler = on_link_request(result, handler_obj)
    await page.setRequestInterception(True)
    page.on("request", req_handler)

    resp_future = asyncio.Future()
    resp_obj = {"response": None}
    resp_handler = get_response_text(resp_future, resp_obj)

    await link_elem.click()
    try:
        await asyncio.wait_for(result, 3)
    except asyncio.TimeoutError:
        print("No request within 3 seconds")
        # done() happens when the task is completed or if it raised an exception
        # reset variable
        result = asyncio.Future()

    page.remove_listener("request", req_handler)
    if result.done():
        html_resp = await compute_request(page, payload, handler_obj, resp_handler, resp_future, resp_obj)

    await page.goto(url)
    return html_resp


async def inject_payload(page, url, payload):
    await page.goto(url)
    html_resp = ""

    buttons_lst = await page.querySelectorAll("input[type='submit'], button")
    for button_idx in range(len(buttons_lst)):
        button_elem = buttons_lst[button_idx]
        # print("Current button: ", await page.evaluate('(btn)=>btn.id', button_elem))
        current_html = await exec_payload_in_inputs(page, button_elem, payload, url)
        html_resp += current_html
        buttons_lst = await page.querySelectorAll("input[type='submit'], button")

    links_lst = await page.querySelectorAll("a[href]")
    for link_idx in range(len(links_lst)):
        link_elem = links_lst[link_idx]
        # print("Current link: ", await page.evaluate('(link)=>link.id', link_elem))
        current_html = await exec_payload_in_link(page, link_elem, payload, url)
        html_resp += current_html
        links_lst = await page.querySelectorAll("a[href]")

    return html_resp


def validate_injection(op_res, html_resp):
    success = False
    responses_lst = list()
    res_matches = list(re.finditer(re.escape(op_res), html_resp))
    if res_matches:
        success = True
        prev_end = 0
        for match in res_matches:
            start, end = match.start(), match.end()
            while start > prev_end and html_resp[start - 1] != ">":
                start -= 1
            while end < len(html_resp) and html_resp[end] != "<":
                end += 1
            prev_end = end

            # start, end = max(0, match.start() - 20), min(len(html_resp), match.end() + 20)
            # print(f"Match: {html_resp[start:end]}")
            responses_lst.append(html_resp[start:end])

    return success, responses_lst


def check_if_sanitized(payload, content):
    # 1) html escaping
    escaped_payload = html.escape(payload)
    if escaped_payload != payload and escaped_payload in content:
        return True, escaped_payload

    return False, escaped_payload


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


############### TEST ##################
if __name__ == "__main__":
    """
    old_html_lst = ["<p>Hello, <?7*7?></p>", "<p>Hello, <?7*7?>, <?7*7?></p>", "<p>Hello, <?7*7?>, <?7*7?>, <?7*7?></p>",
                    "<p>Hello, <?7*7?>, <?7*7?>, <?7*7?></p>",
                    "<p>Hello, <?7*7?>, <?7*7?>, <?7*7?></p>",
                    "<p>Hello, ${7*7}, ${7*7}, ${7*7}</p>",
                    "<p>Hello, ${7*7}</p>",
                    "<p>Hello, ${7*7}, ${7*7}</p>",
                    "<p>Hello, ${7*7}, ${7*7}, ${7*7}</p>",
                    "<p>Hello, ${7*7}, ${7*7}, ${7*7}</p>"
                    ]
    new_html_lst = ["<p>Hello, <!--?7*7?--></p>", "<p>Hello, <!--?7*7?-->, <!--?7*7?--></p>", "<p>Hello, <!--?7*7?-->, <!--?7*7?-->, <!--?7*7?--></p>",
                    "<p>Hello, &lt;?7*7?&gt;, &lt;?7*7?&gt;, &lt;?7*7?&gt;</p>",
                    "<p>Hello, &lt;?7*7?>, &lt;?7*7?>, &lt;?7*7?></p>",
                    "<p>Hello, /{7*7}, \{7*7}, \{7*7}</p>",
                    "<p>Hello, {7*7}</p>",
                    "<p>Hello, {7*7}, {7*7}</p>",
                    "<p>Hello, {7*7}, {7*7}, {7*7}</p>",
                    "<p>Hello, 7*7, 7*7, 7*7</p>"
                    ]
    symbols = ["<? ?>", "<? ?>", "<? ?>", "<? ?>", "<? ?>", "${ }", "${ }", "${ }", "${ }", "${ }"]

    for old, new, symbols in zip(old_html_lst, new_html_lst, symbols):
        print(f"Old html: {old}\nNew html: {new}\nSymbols: {symbols}")
        diffs = get_sanitized_payloads(new, old, symbols, "7*7")
        print(diffs)
########################################
"""
    # print(get_sanitized_payloads("<p>Hello, 7*7, 7*7</p>", "<p>Hello, $7*7, $7*7</p>", "$", "7*7"))
