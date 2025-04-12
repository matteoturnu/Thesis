import asyncio
import random
import re
import string

from bs4 import BeautifulSoup
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

def get_html_changes(new_html, old_html):
    import difflib
    diff = difflib.ndiff(old_html.splitlines(), new_html.splitlines())
    changes = [line.strip("-+ ") for line in diff if line.startswith('+ ') or line.startswith('- ')]

    diffs = []
    for i in range(0, len(changes), 2):
        new_chars_idx = []
        changed_payload = ""

        old_line = changes[i]
        new_line = changes[i + 1]
        matcher = difflib.SequenceMatcher(None, old_line, new_line)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ('replace', 'insert'):
                new_chars_idx.append([j1, j2])

        prev_end = 0
        """
        for j, (start, end) in enumerate(new_chars_idx):
            while start > prev_end and new_line[start - 1] not in string.whitespace:
                if new_line[start - 1].isalnum() or new_line[start - 1] == '>':
                    break
                start -= 1
            prev_end = end
        """
        prev_end = 0
        for j in range(0, len(new_chars_idx)-1, 2):
            payload_start = new_chars_idx[j][0]
            payload_end = new_chars_idx[j+1][1]

            while payload_start > prev_end and new_line[payload_start - 1] not in string.whitespace:
                if new_line[payload_start - 1].isalnum() or new_line[payload_start - 1] == '>':
                    break
                payload_start -= 1
            prev_end = payload_end

            #start_next = min(new_chars_idx[j + 2][0], len(new_line))
            if j + 2 > len(new_chars_idx) - 1:
                start_next = len(new_line)
            else:
                start_next = new_chars_idx[j+2][0]
            while payload_end < start_next and new_line[payload_end] not in string.whitespace:
                if new_line[payload_end].isalnum() or new_line[payload_end] == '<':
                    break
                payload_end += 1

            changed_payload = new_line[payload_start:payload_end]
            if changed_payload:
                if changed_payload not in diffs and all(d not in changed_payload for d in diffs):
                    # condition 2: needed for "your vehicles" checklists from latte script
                    # as it prints 3 payloads instead of one
                    diffs.append(changed_payload)


            """
            start_next = min(new_chars_idx[j+1][0], len(new_line))
            while end < start_next and new_line[end] not in string.whitespace:
                if new_line[end].isalnum() or new_line[end] == '<':
                    break
                end += 1

            changed_payload = new_line[start:end].strip()
            """


        """
        new_chars_idx = [new_chars_idx[0][0], new_chars_idx[-1][-1]]
        start, end = new_chars_idx[0], new_chars_idx[1]

        while start > 0 and new_line[start-1] not in string.whitespace:
            if new_line[start-1].isalnum() or new_line[start-1] == '>':
                break
            start -= 1

        while end < len(new_line) and new_line[end] not in string.whitespace:
            if new_line[end].isalnum() or new_line[end] == '<':
                break
            end += 1

        changed_payload = new_line[start:end].strip()
        if changed_payload:
            if changed_payload not in diffs and all(d not in changed_payload for d in diffs):
                # condition 2: needed for "your vehicles" checklists from latte script
                # as it prints 3 payloads instead of one
                diffs.append(changed_payload)
                
        """

        """
        prev_end = 0
        for j, (start, end) in enumerate(new_chars_idx):
            if j == 0:
                prev_end = start
            changed_payload += new_line[prev_end:start] + new_line[start:end]

            k = 1
            valid_before = True
            valid_after = True
            while (start - k) >= 0 and (end + k) < len(new_line) and (valid_before or valid_after):
                # as soon as one surrounding char is alphanumeric, stop scanning towards that direction
                if valid_before:
                    before = new_line[start-k]
                    if not before.isalnum():
                        changed_payload = before + changed_payload
                    else:
                        valid_before = False
                if valid_after:
                    after = new_line[end+k]
                    if not after.isalnum():
                        changed_payload += after
                    else:
                        valid_after = False
                k += 1


            prev_end = end
        if changed_payload not in diffs:
            diffs.append(changed_payload)
    """

    """for old_line, new_line in changes:
        matcher = difflib.SequenceMatcher(None, old_line, new_line)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ('replace', 'insert'):
                diffs.append(new_line[j1:j2])
    """
    return diffs


    # find_all() returns all the tags found, not one by one but considering their tree structure
    # e.g.: content = <head></head><body><p></p></body>
    #       it returns [<head></head>, <body><p></p></body>, <p></p>]
    """
    old_soup = BeautifulSoup(old_html, "html.parser").find_all()
    new_soup = BeautifulSoup(new_html, "html.parser").find_all()

    diffs = []
    new_tags = []
    for (old_soup_elem, new_soup_elem) in zip(old_soup, new_soup):
        if old_soup_elem != new_soup_elem:
            # diffs contains the tree structure which includes the new tag
            diffs.append(new_soup_elem)

    # extract only the new tags
    for i, candidate in enumerate(diffs):
        is_common = True  # assume candidate is contained in or equal to all others

        for j, other in enumerate(diffs):
            if j != i:
                if not (str(candidate) in str(other) or str(candidate) == str(other)):
                    is_common = False
                    break  # no need to check further


        if is_common:
            new_tags.append(candidate)
    """


    """
    for i, candidate in enumerate(diffs):
        # all(): returns True if all the conditions inside it are True
        # condition: element is equal to or contained in all the others
        if all(
                str(candidate) in str(other) or str(candidate) == str(other)
                for j, other in enumerate(diffs) if j != i
        ):
            new_tags.append(candidate)
    """

    return new_tags



async def exec_payload_in_inputs(page, button_elem, payload, url):
    # find the input text areas
    input_type_lst = await page.querySelectorAll('input[type]:not([type="reset"])'
                                                 ':not([type="submit"])'
                                                 ':not([type="button"])'
                                                 ':not([type="image"])')
    input_type_lst += await page.querySelectorAll('textarea')

    # write the payload inside every input text area of the form
    for input_element in input_type_lst:
        element_type = await page.evaluate('(el) => el.type', input_element)

        if element_type in ["text", "password", "search", "tel", "url", "textarea"]:
            # mimick user typing: the text may be altered by a client-side validation mechanism
            await input_element.type(payload)

        # NOTE: consider select-option, hidden as well...
        elif element_type in ["radio", "checkbox", "hidden"]:
            # old_value = await page.evaluate("(el) => el.value", input_element)
            await page.evaluate("(el, value) => el.value = value", input_element, payload)
            # new_value = await page.evaluate("(el) => el.value", input_element)
            # print(f"Old value: {old_value}; new value: {new_value}")
            if element_type in ["radio", "checkbox"]:
                await input_element.click()

        # PROBLEM: some characters like @ and () are not allowed for emails!
        elif element_type in ["email"]:
            await input_element.type(payload + "@a")
            # check email validity
            if not await page.evaluate("(el) => el.validity.valid", input_element):
                # if invalid, change it with a valid one and leave it
                print("The email is invalid.")
                await page.evaluate("(el, value) => el.value = value", input_element, "a@a")

    html_resp = ""
    dom_reloaded = asyncio.Future()
    handler_obj = {"request_obj": None}

    req_handler = on_btn_request(dom_reloaded, handler_obj)
    await page.setRequestInterception(True)
    page.on("request", req_handler)

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
        await page.setRequestInterception(False)
        # submit button
        html_resp = await page.content()
        #print("Submit button")

    elif dom_reloaded.done():  # and if it's False
        # ajax or js-nav button
        req_url = handler_obj["request_obj"].url
        if "?" in req_url:
            # new url obtained
            new_url = edit_url_query(req_url, payload)
            await handler_obj["request_obj"].continue_({"url": new_url})
            await page.setRequestInterception(False)
            html_resp = await page.content()
        else:
            await handler_obj["request_obj"].continue_()
            await page.setRequestInterception(False)

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

    new_url = url + new_queries[:-1]  # delete last "&"
    return new_url


async def exec_payload_in_link(page, link_elem, payload, url):
    """
    href = await page.evaluate("(el) => el.href", link_elem)
    # discard links without query parameters
    if "?" not in href:
        return ""

    new_href = edit_url_query(href, payload)
    await page.evaluate("(el, new_value) => el.href=new_value", link_elem, new_href)
    await link_elem.click()

    await page.waitForNavigation({'waitUntil': 'domcontentloaded'})
    html_resp = await page.content()
    """

    html_resp = ""
    result = asyncio.Future()
    handler_obj = {"request_obj": None}

    req_handler = on_link_request(result, handler_obj)
    await page.setRequestInterception(True)
    page.on("request", req_handler)

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
        req_url = handler_obj["request_obj"].url
        if "?" in req_url:
            # new url obtained
            new_url = edit_url_query(req_url, payload)
            # let the request continue but with a new url
            await handler_obj["request_obj"].continue_({"url": new_url})
            await page.setRequestInterception(False)
            html_resp = await page.content()
        else:
            await handler_obj["request_obj"].continue_()
            await page.setRequestInterception(False)

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
    res_matches = None
    res_matches = list(re.finditer(re.escape(op_res), html_resp))
    if res_matches:
        success = True
        for match in res_matches:
            start, end = max(0, match.start() - 20), min(len(html_resp), match.end() + 20)
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
