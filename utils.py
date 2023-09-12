import random
import string


def generate_random_string(resource_name, length=8):
    random.seed(resource_name)
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))
