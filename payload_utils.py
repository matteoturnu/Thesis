import asyncio
import re
import string
import urllib.parse
import html

import pyppeteer.errors

from simple_utils import *
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def create_payload(symbols):
    # generate random numbers for the payload product
    num_1, num_2, _ = generate_numbers_for_product()
    operation = f"{num_1}*{num_2}"

    if " " in symbols:
        # start splitting from right
        parts = symbols.rsplit(' ', 1)  # needed for #set $num= #$num" (Spitfire) since there are two spaces
        payload = operation.join(parts)
    else:
        print("No place to insert payload operation. Exiting...")
        exit()
    # in the future, return only the payload
    return payload, operation


def on_btn_request(dom_reloaded, obj):
    async def is_request(request):
        if request.isNavigationRequest() and request.method == "POST":
            # ex: submit button case (form)
            if not dom_reloaded.done():
                dom_reloaded.set_result(True)
                await request.continue_()
        elif not dom_reloaded.done():
            # ex: js-navigation button, ajax request
            dom_reloaded.set_result(False)
            obj["request_obj"] = request
        else:
            await request.continue_()

    return lambda request: asyncio.create_task(is_request(request))


def on_link_request(result, obj):
    # TODO: change function name as it's used also for GET requests (url request)
    async def is_request(request):
        print("[Request]", request.method, request.url)
        try:
            if not result.done():
                obj["request_obj"] = request
                result.set_result(True)
        except Exception as e:
            print(f"[ERROR] Exception inside is_request: {e}")

    return lambda request: asyncio.create_task(is_request(request))

def get_response_text(resp_future, resp_obj):
    async def on_response(response):
        print("[Response]", response.status, response.url)
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
        print("New link for injection: ", new_url)
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


def merge_overlapping_payloads(payload1, payload2):
    max_overlap = 0
    for idx in range(1, min(len(payload1), len(payload2)) + 1):
        if payload1[-idx:] == payload2[:idx]:
            max_overlap = idx

    return payload1 + payload2[max_overlap:]



def get_sanitized_payloads(new_html, old_html, symbols, operation):
    # HYPOTHESIS: operation is never sanitized (ex: no 7/*7 or anything similar) but payload is
    # ENHANCEMENT: use a blacklist of symbols for which stopping scan
    # ex: "," and "!" for forward scanning

    changes_plus, changes_minus = get_html_diffs(new_html, old_html)


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

        if len(symbols) > 1:
            delimiter_start, delimiter_end = symbols.rsplit(' ', 1)
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
                        changed_payload = merge_overlapping_payloads(diffs[-1], changed_payload)
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

    try:
        # execute instructions concurrently
        # wait until both are completed
        await asyncio.gather(
            # page.evaluate('(el) => el.click()', button_elem),
            button_elem.click(),
            asyncio.wait_for(dom_reloaded, 5)
        )
    except asyncio.TimeoutError:
        print("[TimeoutError] No request within 5 seconds")
        # done() happens when the task is completed or if it raised an exception
        # reset variable
        dom_reloaded = asyncio.Future()
        await page.setRequestInterception(False)

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


def edit_url_query(url, new_query_value, target_parameter=None):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    if target_parameter:
        query_params[target_parameter] = [new_query_value]
    else:
        for param_name in query_params:
            query_params[param_name] = [new_query_value]

    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params,
                          new_query, parsed_url.fragment))

    return new_url

    # The row below is needed to test with Craft CMS since it doesn't allow encoded urls
    # but it doesn't work with CVE related to CMS Made Simple with symbols like "#" and so on
    # return urllib.parse.unquote(new_url)


async def exec_payload_in_link(page, link_elem, payload, url):
    html_resp = ""

    req_future = asyncio.Future()
    req_obj = {"request_obj": None}
    req_handler = on_link_request(req_future, req_obj)
    await page.setRequestInterception(True)
    page.on("request", req_handler)

    resp_future = asyncio.Future()
    resp_obj = {"response": None}
    resp_handler = get_response_text(resp_future, resp_obj)

    try:
        # execute instructions concurrently
        # wait until both are completed
        await asyncio.gather(
            page.evaluate('(el) => el.click()', link_elem),
            asyncio.wait_for(req_future, 5)
        )
    except asyncio.TimeoutError:
        print("[TimeoutError] No request within 5 seconds")
        # done() happens when the task is completed or if it raised an exception
        # reset variable
        req_future = asyncio.Future()
        await page.setRequestInterception(False)

    page.remove_listener("request", req_handler)
    if req_future.done():
        html_resp = await compute_request(page, payload, req_obj, resp_handler, resp_future, resp_obj)

    # go back to main page
    await page.goto(url)

    return html_resp


async def exec_payload_in_url(page, param_to_attack, payload, url):
    html_resp = ""
    new_url = edit_url_query(url, payload, param_to_attack)

    # setting response listener
    resp_result = asyncio.Future()
    resp_obj = {"response": None}
    resp_handler = get_response_text(resp_result, resp_obj)

    def filtered_handler(response):
        if new_url in response.url and response.request.resourceType == "document":
            resp_handler(response)

    # page.once("response", one_time_handler)
    page.on("response", filtered_handler)

    await page.goto(new_url, waitUntil="domcontentloaded")
    html_resp = await capture_response(resp_result, resp_obj)

    page.remove_listener("response", filtered_handler)
    return html_resp


async def inject_payload(page, url, payload, injection_point, param_to_attack):
    try:
        await page.goto(url)
        html_resp = ""

        if injection_point == "PAGE":
            processed_elements = []
            button_idx = 0
            while True:
                buttons_lst = await page.querySelectorAll("input[type='submit'], button")
                if button_idx >= len(buttons_lst):
                    break

                button_elem = buttons_lst[button_idx]
                button_outer_html = await page.evaluate('(el) => el.outerHTML', button_elem)
                # avoid considering previous scanned buttons again
                if button_outer_html not in processed_elements:
                    processed_elements.append(button_outer_html)
                    print("Button number ", button_idx)
                    print("Current button: ", button_outer_html)
                    current_html = await exec_payload_in_inputs(page, button_elem, payload, url)
                    html_resp += current_html

                button_idx += 1


            processed_elements = []
            link_idx = 0
            while True:
                links_lst = await page.querySelectorAll("a[href]")
                if link_idx >= len(links_lst):
                    break

                link_elem = links_lst[link_idx]
                link_outer_html = await page.evaluate('(el) => el.outerHTML', link_elem)
                # avoid considering previous scanned links again
                if link_outer_html not in processed_elements:
                    processed_elements.append(link_outer_html)
                    print("Link number ", link_idx)
                    print("Current link: ", link_outer_html)
                    current_html = await exec_payload_in_link(page, link_elem, payload, url)
                    html_resp += current_html

                link_idx += 1

        elif injection_point == "URL":
            html_resp = await exec_payload_in_url(page, param_to_attack, payload, url)

        return html_resp

    except pyppeteer.errors.NetworkError as e:
        print("[NetworkError]: ", e)



def validate_injection(op_res, html_resp, symbols):
    success = False
    responses_lst = list()

    #symbols_split = symbols.split(" ")

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
        # condition 1) add " " if successful but don't prefer it to the others
        # condition 2) if " " and "( )" are both successful, it's likely we are in a code context: don't save "( )"
        if ((success_symbols in new_symbols and success_symbols != " ")
                or (success_symbols == " " and new_symbols == "( )")):
            symbols_are_contained = True
            break
        elif ((new_symbols in success_symbols and new_symbols != " ")
              or (success_symbols == "( )" and new_symbols == " ")):
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
    url = "http://127.0.0.1:8000/index.php?mact=News,cntnt01,detail,0&cntnt01articleid=1&cntnt01detailtemplate=Simplex%20News%20Detail&cntnt01returnid=1"
    new_url = edit_url_query(url, "string:{7*7}", "cntnt01detailtemplate")
    print("New url: ", new_url)

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
