import asyncio
import re
import random
from pyppeteer import launch


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
            html_resp += await page.content()
            # go back to previous page and look for other forms
            await page.goBack()
            # refresh element references (with button click they are lost)
            forms_lst = await page.querySelectorAll("form")
        except Exception as e:
            print(e)

    return html_resp


async def main():
    url = "http://127.0.0.1:8080"
    # only starting tags for now
    # for python and php template engines
    # maybe, if the simple (7*7) doesn't work, as in  Spitfire case, try with int() and other functions
    symbols_lst = ["$", "#", "< >", "{ }", "{{ }}", "<? ?>", "{{= }}", "{% %}", "${ }", "@! !@", "#{ }", "$int( )"]
    # maybe use replace() to replace the space character with the operation

    # launch browser without GUI
    browser = await launch({"headless": True})
    page = await browser.newPage()

    success_payloads = []
    for symbols in symbols_lst:

        payload, operation = create_payload(symbols)
        print(f"\nTrying symbols '{symbols}' with payload '{payload}'...")

        response = await scraper(page, url, payload)

        result = str(eval(operation))
        res_matches = list(re.finditer(result, response))
        if res_matches:
            print("Successful injection.")
            success_payloads.append(payload)
            for match in res_matches:
                start, end = max(0, match.start() - 20), min(len(response), match.end() + 20)
                print(response[start:end])
        else:
            print("Failed injection.")

    await browser.close()

    if success_payloads:
        print("Some successful payloads have been found:\n", success_payloads)
    else:
        print("No successful payload has been found.")


if __name__ == "__main__":
    asyncio.run(main())