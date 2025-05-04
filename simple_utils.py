import random
import difflib

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

def get_html_diffs(new_content, old_content):
    changes_plus = []
    changes_minus = []
    diff_iter = difflib.ndiff(old_content.splitlines(), new_content.splitlines())
    for line in diff_iter:
        if line.startswith('+ '):
            changes_plus.append(line.strip("+ "))
        elif line.startswith('- '):
            changes_minus.append(line.strip("- "))

    return changes_plus, changes_minus