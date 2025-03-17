import asyncio
import re
import random
from pyppeteer import launch
from decimal import Decimal

def generate_number(min_digits, max_digits):
    # generate a value with a number of digits in a certain range
    n_digits = random.randint(10, 15)
    return int("".join(random.choices("0123456789", k=n_digits)))

def create_payload(symbols):
    # generate random numbers for the payload product
    min_digits = 10
    max_digits = 15
    num_1 = generate_number(10, 15)
    num_2 = generate_number(10, 15)


    #operation = f"int({num_1}*{num_2})"
    operation = f"{num_1}*{num_2}"
    # in a real scenario, we use values directly instead of variables like num_1 and num_2
    # like this: operation = "int(2*2)"
    #print(f"Numbers: {num_1}, {num_2}; result: {eval(operation)}")

    if " " in symbols:
        # replace the space with the actual operation
        if "_" in symbols:
            # this case is used only for Plates so far
            payload = symbols.replace("_", operation)
        else:
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
    #print(f"{len(forms_lst)} form(s) found.")

    html_resp = ""
    for form_idx in range(len(forms_lst)):
        curr_form = forms_lst[form_idx]
        try:
            await exec_payload(curr_form, payload)
            await page.waitForNavigation()
            #await page.waitFor(2000)
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
        res_matches = list(re.finditer(op_res, html_resp))
        if res_matches:
            success = True
            for match in res_matches:
                start, end = max(0, match.start() - 20), min(len(html_resp), match.end() + 20)
                responses_lst.append(html_resp[start:end])

    return success, responses_lst


async def main():
    url = "http://127.0.0.1:8080"
    # only starting tags for now
    # for python and php template engines
    # maybe, if the simple (7*7) doesn't work, as in  Spitfire case, try with int() and other functions
    symbols_lst = ["$", "#", "< >", "{ }", "{{ }}", "<? ?>", "{{= }}", "{% %}", "${ }", "@! !@", "#{ }",
                   "$int( )", "${eval('echo _;')}"]
    # symbols_lst = ["${ }", "$int( )"]

    # launch browser without GUI
    browser = await launch({"headless": True})
    page = await browser.newPage()

    success_payloads = []
    for symbols in symbols_lst:

        payload, operation = create_payload(symbols)
        print(f"\nTrying symbols '{symbols}' with payload '{payload}'...")

        response = await scraper(page, url, payload)
        #print(response)

        result = str(eval(operation))
        #print("Operation result: ", result)

        success, resp_matches = validate_injection(result, response)
        if success:
            success_payloads.append(payload)
            print("Successful injection!")
            for match in resp_matches:
                print(match)
        else:
            print("Failed injection.")


    await browser.close()

    if success_payloads:
        print("Some successful payloads have been found:\n", success_payloads)
    else:
        print("No successful payload has been found.")


if __name__ == "__main__":
    asyncio.run(main())