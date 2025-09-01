import os
import re


def fix_linting_errors(directory):
    """
    This script automatically fixes some of the most common and repetitive
    linting errors reported by ruff.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    content = f.read()

                # E712: == False -> is False (safer than `not`)
                content = re.sub(r" == False", " is False", content)
                # E712: == True -> implicit True
                content = re.sub(r" == True", "", content)
                # E722: bare except -> except Exception
                content = re.sub(r"except:", "except Exception:", content)
                # E711: == None -> is None
                content = re.sub(r" == None", " is None", content)
                # E721: type() == -> isinstance()
                content = re.sub(
                    r"type\((.*?)\) == str", r"isinstance(\1, str)", content
                )
                content = re.sub(
                    r"type\((.*?)\) == list", r"isinstance(\1, list)", content
                )

                with open(filepath, "w") as f:
                    f.write(content)


if __name__ == "__main__":
    fix_linting_errors("eeauditor")
    fix_linting_errors("integrations")
    fix_linting_errors("scripts")
    print("Linting fixes applied.")
