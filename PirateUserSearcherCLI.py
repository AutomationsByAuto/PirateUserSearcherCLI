"""
A Python tool to search The Pirate Bay for torrents by username and search terms.
Supports searching multiple users at one time, sorting options, and CSV-based configuration storage.

Usage:
    Run the script and follow the prompts to start a fresh search, load a dataset,
    or clean up duplicates.
Note:
    Running in Command Prompt will not generate clickable links. I run this script in Pycharm for better usability.
    For educational purposes only. Respect copyright laws and use legal sources.
"""

# Standard library imports
import os
import platform
import random
import time
from datetime import datetime
from itertools import chain

# Third-party imports
import aiohttp
import asyncio
import pandas as pd
import requests

# Global Variables
PIRATE_URL = ""
USERNAMES = []  # Duplicate entries are handled later to avoid double counting
SEARCH_TERMS = []  # Made global for saving to CSV
STATUS = ''  # Tracks how data saving is handled
CHOSEN_CSV = ''  # Stores the selected CSV filename for amendments

# Constants
MAX_RESULTS_WITH_LINKS = 100  # Limit for displaying relevant links
REQUEST_TIMEOUT = 10  # Seconds to wait before timeout in requests


# Functions
def fresh():
    """Initiate a fresh search by collecting usernames and search terms, checking the proxy, and starting the search."""
    global USERNAMES, SEARCH_TERMS, PIRATE_URL
    proxy_checker()

    # Collect and process usernames
    users_input = input(
        "Input the usernames with the files you would like to search through.\n"
        "Separate each username with a comma: "
    )
    USERNAMES += users_input.split(',')
    USERNAMES = [name.strip() for name in USERNAMES]  # Remove whitespace
    USERNAMES = [name.capitalize() for name in USERNAMES]  # Standardize capitalization

    # Collect and process search terms
    terms_input = input(
        "Which search terms would you like to use?\n"
        "Separate each search term with a comma: "
    ).lower()
    SEARCH_TERMS += terms_input.split(',')
    SEARCH_TERMS = [term.strip() for term in SEARCH_TERMS]  # Remove whitespace

    search(usernames=USERNAMES, search_terms=SEARCH_TERMS)


def get_tasks(item_list, session):
    """
    Create a list of asynchronous tasks for fetching torrent data.

    Args:
        item_list (list): List of dictionaries containing torrent information.
        session (aiohttp.ClientSession): Session object for making HTTP requests.

    Returns:
        list: List of tasks to be executed asynchronously.
    """
    tasks = []
    for item in item_list:
        tasks.append(session.get(f"{PIRATE_URL}/torrent/{item['id']}\n", ssl=False))
    return tasks


async def check_urls(item_list):
    """
    Check the status codes of torrent URLs asynchronously and update the list with results.

    Args:
        item_list (list): List of dictionaries with torrent information.

    Returns:
        list: Updated list with 'code' key added to each dictionary.
    """
    async with aiohttp.ClientSession() as session:
        tasks = get_tasks(item_list, session)
        responses = await asyncio.gather(*tasks)
        codes = [response.status for response in responses]

        for idx, item in enumerate(item_list):
            item["code"] = codes[idx]

    return item_list


def search(usernames, search_terms):
    """
    Search The Pirate Bay for torrents using specified usernames and terms, then process and sort results.

    Args:
        usernames (list): List of usernames to filter results.
        search_terms (list): List of terms to search for.
    """
    print("\nSearching...please wait a moment.\n")
    if len(search_terms) > 50:
        print("This may take a moment if using many search terms.\n")

    combined_data_list = []

    # Fetch data for each search term
    for term in search_terms:
        params = {"q": term}
        response = requests.get("https://apibay.org/q.php", params=params)
        data = response.json()

        # Filter by usernames
        for user in usernames:
            filtered_data = [item for item in data if item["username"] == user]
            combined_data_list.append(filtered_data)

    # Process results
    non_empty_data = [x for x in combined_data_list if x]  # Remove empty lists
    dict_list = list(chain(*non_empty_data))  # Flatten list of lists

    # Convert string values to integers for sorting
    for item in dict_list:
        item["added"] = int(item["added"])
        item["seeders"] = int(item["seeders"])
        item["size"] = int(item["size"])

    # Remove duplicates
    unique_list = []
    [unique_list.append(item) for item in dict_list if item not in unique_list]

    print(f"Found {len(unique_list)} potential results.\n")
    time.sleep(1)
    print("Checking for and removing dead URLs...\n")
    counter = 0
    while True:
        try:
            # Check URLs and filter out broken ones
            if platform.system() == "Windows":
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            unique_list = asyncio.run(check_urls(unique_list))
            working_list = [item for item in unique_list if item["code"] != 404]

            print(f"Found {len(working_list)} working results.\n")
            sorter(working_list)
            break

        except:  # Left bare to catch all possible failures.
            # Eventually it will run correctly and filter dead URLs.
            counter += 1
            if counter > 3:
                print('Could not filter dead URLs.\nCommencing search with all URLS.')
                sorter(unique_list)
                break
            else:
                print(f'Attempt: {counter}/3')
                print(
                    "The server disconnected. Let's try again.\n\nIf the problem persists more than 3 times the search "
                    "will commence with non-filtered URLs:\n\n"
                    "In future if you would like filtered results I recommend:\n\n"
                    "- Disconnect or change your VPN location.\n"
                    "- OR: Reduce the inputted search terms.\n"
                    "\nSearching now...\n")


def sorter(item_list):
    """
    Sort search results based on user preference and pass them to the printer.

    Args:
        item_list (list): List of torrent dictionaries to sort.
    """
    print("How would you like to sort the results?:\n")
    while True:
        choice = input(
            "By newest: (n)\n"
            "By oldest: (o)\n"
            "By most seeded: (s)\n"
            "By largest file: (l)\n"
            "By smallest file: (m)\n"  # Changed 's' to 'm' to avoid conflict
            "By random: (r)\n"
        ).lower()

        if choice == "n":
            sorted_list = sorted(item_list, key=lambda x: x["added"], reverse=True)
            printer(sorted_list)
            break
        elif choice == "o":
            sorted_list = sorted(item_list, key=lambda x: x["added"])
            printer(sorted_list)
            break
        elif choice == "s":
            sorted_list = sorted(item_list, key=lambda x: x["seeders"], reverse=True)
            printer(sorted_list)
            break
        elif choice == "l":
            sorted_list = sorted(item_list, key=lambda x: x["size"], reverse=True)
            printer(sorted_list)
            break
        elif choice == "m":
            sorted_list = sorted(item_list, key=lambda x: x["size"])
            printer(sorted_list)
            break
        elif choice == "r":
            random.shuffle(item_list)
            printer(item_list)
            break
        else:
            print("Please input a valid option.\n")


def printer(results):
    """
    Display search results with formatting and offer re-sorting or saving options.

    Args:
        results (list): List of torrent dictionaries to print.
    """
    print(
        "\nNOTICE:\n"
        "The first 100 results include relevant URLs from the torrent's page (e.g., screenshots).\n"
        "This is limited to the first 100 results.\n"
        "To save time; the relevant URLs have not been checked.\n"
        "Enjoy the results and scroll down for re-sorting and saving options.\n"
    )

    for idx, item in enumerate(results):
        print(item["name"])
        print(f"Uploaded by: {item['username']}")
        print(f"User status: {item['status']}")
        size_gb = item["size"] / 1073741824  # Convert bytes to GB
        print(f"File size: {round(size_gb, 2)} GB")
        upload_date = datetime.fromtimestamp(item["added"])
        print(f"Uploaded: {upload_date}")
        print(f"Number of seeders: {item['seeders']}")
        print(f"Hash: {item['info_hash']}")
        url = f'{PIRATE_URL}/torrent/{item["id"]}\n'
        print(f"Site URL: {url}")

        # Fetch and display relevant links for first 100 results
        if idx < MAX_RESULTS_WITH_LINKS:
            info = requests.get(f"https://apibay.org/t.php?id={item['id']}")
            info_data = info.json()
            description = info_data["descr"]
            print("Relevant links:")
            for line in description.splitlines():
                if "http" in line:
                    print(line)
            print("")

    # Offer re-sorting option
    while True:
        re_sort = input("Would you like to sort the results differently? (y/n): ").lower()
        if re_sort == "y":
            print("\n" * 100)  # Clear screen
            sorter(results)
            break
        elif re_sort == "n":
            print("Ok, let's close down or save the data...\n")
            time.sleep(1)
            save()
            break
        else:
            print("Please input a valid option.\n")


def save():
    """Save the current search configuration to a CSV file based on the STATUS."""
    global STATUS, USERNAMES, SEARCH_TERMS, PIRATE_URL, CHOSEN_CSV

    if STATUS == "f":  # Fresh start
        while True:
            to_save = input(
                "Would you like to save this URL, usernames, and search terms for later use? (y/n): ").lower()
            if to_save == "y":
                name = input("Please input a name for this collection: ").lower()
                if name.endswith(".csv"):
                    name = name.replace(".csv", "")
                name += ".csv"
                columns = ["URL", "Usernames", "Search_Terms"]
                df = pd.DataFrame(columns=columns)
                df.at[0, "URL"] = PIRATE_URL
                df.at[0, "Usernames"] = USERNAMES
                df.at[0, "Search_Terms"] = SEARCH_TERMS
                df.to_csv(name, index=False)
                print("Your data set has been saved.\nHave a great day!")
                break
            elif to_save == 'n':
                print("Ok! Have a great day. Exiting program.")
                break
            else:
                print("Please input a valid option.\n")

    elif STATUS == "s":  # Search as is
        print("Since you made no changes...\nClosing down the program.\nHave a great day!")

    elif STATUS == "a":  # Amend
        df = pd.read_csv(CHOSEN_CSV)
        while True:
            choice = input(
                "Would you like to:\n"
                "- Overwrite your CSV with the new dataset: (o)\n"
                "- Save as a new dataset: (s)\n"
                "- View changes with options to combine, revert, or overwrite: (v)\n"
                "- Exit without saving: (e) \n"
            ).lower()

            if choice == "o":  # Overwrite existing CSV
                df.at[0, "URL"] = PIRATE_URL
                df.at[0, "Usernames"] = USERNAMES
                df.at[0, "Search_Terms"] = SEARCH_TERMS
                df.to_csv(CHOSEN_CSV, index=False)
                print("Your data set has been saved.\nHave a great day!")
                break

            elif choice == "s":  # Save as new CSV
                name = input("Please input a name for this collection: ").lower()
                if name.endswith(".csv"):
                    name = name.replace(".csv", "")
                name += ".csv"
                columns = ["URL", "Usernames", "Search_Terms"]
                df = pd.DataFrame(columns=columns)
                df.at[0, "URL"] = PIRATE_URL
                df.at[0, "Usernames"] = USERNAMES
                df.at[0, "Search_Terms"] = SEARCH_TERMS
                df.to_csv(name, index=False)
                print("Your data set has been saved.\nHave a great day!")
                break

            elif choice == "e":
                print('Exiting the program...\nHave a great day')
                break

            elif choice == "v":  # View and manage changes
                # URL comparison
                if df.at[0, "URL"] == PIRATE_URL:
                    print("You did not change the URL")
                    time.sleep(1)
                else:
                    print(f"You changed the URL: \nOld: {df.at[0, 'URL']}\nNew: {PIRATE_URL}")
                    while True:
                        overwrite = input("Would you like to overwrite the old URL? (y/n): ").lower()
                        if overwrite == "y":
                            df.at[0, "URL"] = PIRATE_URL
                            print("The URL has been changed\n")
                            time.sleep(1)
                            break
                        elif overwrite == "n":
                            break
                        else:
                            print("Please input a valid option.\n")

                # Username comparison
                old_users = eval(df.at[0, "Usernames"])
                if old_users == USERNAMES:
                    print("You did not change the usernames")
                    time.sleep(1)
                else:
                    print(f"\nThe targeted users have been changed.\nOld: {old_users}\nNew: {USERNAMES}")
                    while True:
                        action = input(
                            "Would you like to:\n"
                            "- Keep the original users: (k)\n"
                            "- Overwrite with new users: (o)\n"
                            "- Combine all users (skipping duplicates): (c)\n"
                        ).lower()
                        if action == "k":
                            break
                        elif action == "o":
                            df.at[0, "Usernames"] = USERNAMES
                            break
                        elif action == "c":
                            combined = list(set(old_users + USERNAMES))
                            df.at[0, "Usernames"] = combined
                            break
                        else:
                            print("Please input a valid option.\n")

                # Search term comparison
                old_terms = eval(df.at[0, "Search_Terms"])
                if old_terms == SEARCH_TERMS:
                    print("You did not change the search terms")
                    time.sleep(1)
                else:
                    while True:
                        print(f"\nThe search terms have been changed.\nOld: {old_terms}\nNew: {SEARCH_TERMS}")
                        action = input(
                            "Would you like to:\n"
                            "- Keep the original terms: (k)\n"
                            "- Overwrite with new terms: (o)\n"
                            "- Combine all terms (skipping duplicates): (c)\n"
                        ).lower()
                        if action == "k":
                            break
                        elif action == "o":
                            df.at[0, "Search_Terms"] = SEARCH_TERMS
                            break
                        elif action == "c":
                            combined = list(set(old_terms + SEARCH_TERMS))
                            df.at[0, "Search_Terms"] = combined
                            break
                        else:
                            print("Please input a valid option.\n")

                # Final save options
                while True:
                    save_choice = input(
                        "- Overwrite the current dataset: (o)\n"
                        "- Save as a new dataset: (s)\n"
                        "- Make no changes (m)\n"
                    ).lower()
                    if save_choice == "o":
                        df.to_csv(CHOSEN_CSV, index=False)
                        print("Your data set has been saved.\nHave a great day!")
                        break
                    elif save_choice == "s":
                        name = input("Please input a name for this collection: ").lower()
                        if name.endswith(".csv"):
                            name = name.replace(".csv", "")
                        name += ".csv"
                        df.to_csv(name, index=False)
                        print("Your data set has been saved.\nHave a great day!")
                        break
                    elif save_choice == "m":
                        print("Nothing has been changed.\nHave a great day!")
                        break
                    else:
                        print("Please input a valid option.")
                        time.sleep(1)
            else:
                print("Please input a valid option.\n")


def proxy_checker(**kwargs):
    """
    Verify the Pirate Bay proxy URL and allow updates if necessary.

    Args:
        **kwargs: Optional keyword arguments, including 'dataset' for CSV filename.
    """
    global PIRATE_URL, STATUS
    if STATUS == "f":  # Fresh start
        while True:
            PIRATE_URL = input("Please paste in a working Pirate Bay URL or proxy. \n"
                               "The official URL leads to cleanest results: thepiratebay.org\n")
            if PIRATE_URL.startswith('www.'):
                PIRATE_URL = PIRATE_URL.replace('www.', '')
            if not PIRATE_URL.startswith("https://"):
                PIRATE_URL = "https://" + PIRATE_URL
            if PIRATE_URL.endswith("index.html"):
                PIRATE_URL = PIRATE_URL.replace("index.html", "")
            try:
                response = requests.get(PIRATE_URL, timeout=REQUEST_TIMEOUT)
                if response.ok:
                    return
            except requests.RequestException:
                print(f"Cannot connect to {PIRATE_URL}\nPlease try a different URL.")

    elif STATUS == "s":  # Search as is
        try:
            response = requests.get(PIRATE_URL, timeout=REQUEST_TIMEOUT)
            if response.ok:
                print(f"Your Pirate URL is still working: {PIRATE_URL}")
                return
        except requests.RequestException:
            print(f"Cannot connect to {PIRATE_URL}. Please provide a new URL.")
            while True:
                new_url = input("Input a different URL: ")
                if not new_url.startswith("https://"):
                    new_url = "https://" + new_url
                if new_url.endswith("index.html"):
                    new_url = new_url.replace("index.html", "")
                try:
                    response = requests.get(new_url, timeout=REQUEST_TIMEOUT)
                    if response.ok:
                        print(f"This URL works: {new_url}")
                        if "dataset" in kwargs:
                            df = pd.read_csv(kwargs["dataset"])
                            df.at[0, "URL"] = new_url
                            df.to_csv(kwargs["dataset"], index=False)
                        PIRATE_URL = new_url
                        return
                except requests.RequestException:
                    print("This URL does not work. Try again.")

    elif STATUS == "a":  # Amend
        try:
            response = requests.get(PIRATE_URL, timeout=REQUEST_TIMEOUT)
            if response.ok:
                print(f"Your Pirate URL is still working: {PIRATE_URL}")
                while True:
                    change = input("Would you like to change it anyway? (y/n): ").lower()
                    if change == "n":
                        break

                    elif change == "y":
                        break
                    else:
                        print("Please input a valid option.")
                if change == 'n':
                    return
                if change == 'y':
                    pass

        except requests.RequestException:
            print("URL is not working. Please provide a new one.")
        while True:
            new_url = input("Please input a working Pirate URL.\nThe official URL leads to cleanest"
                            " results: thepiratebay.org\n")
            if not new_url.startswith("https://"):
                new_url = "https://" + new_url
            if new_url.endswith("index.html"):
                new_url = new_url.replace("index.html", "")
            try:
                response = requests.get(new_url, timeout=REQUEST_TIMEOUT)
                if response.ok:
                    print(f"This URL works: {new_url}")
                    PIRATE_URL = new_url
                    return
            except requests.RequestException:
                print("This URL does not work. Try again.")
    time.sleep(5)


def amend():
    """Allow users to modify an existing dataset (URL, usernames, search terms) and proceed to search."""
    global PIRATE_URL, USERNAMES, SEARCH_TERMS, CHOSEN_CSV
    print("Let's make some changes.\n")
    csv_files = [file for file in os.listdir() if file.endswith(".csv")]

    print("Available data sets:")
    for file in csv_files:
        print(file)

    choice = input("Input the set you would like to change: ").lower()
    if not choice.endswith(".csv"):
        choice += ".csv"
    CHOSEN_CSV = choice

    if choice in csv_files:
        df = pd.read_csv(choice)
        PIRATE_URL = df.at[0, "URL"]
        USERNAMES = eval(df.at[0, "Usernames"])
        SEARCH_TERMS = eval(df.at[0, "Search_Terms"])

        # Check and update URL if needed
        proxy_checker()

        # Modify usernames
        print("\nCurrent usernames:")
        for name in USERNAMES:
            print(name)
        while True:
            choice = input("Remove any users? (y/n): ").lower()
            if choice == "y":
                remove = input("Input usernames to remove (comma-separated): ").split(",")
                remove = [name.strip().capitalize() for name in remove]
                USERNAMES = [name for name in USERNAMES if name not in remove]
                break
            elif choice == "n":
                break
            else:
                print("Please input a valid option.")
        while True:
            choice = input("Add new users? (y/n): ").lower()
            if choice == "y":
                new_users = input("Input new usernames (comma-separated): ").split(",")
                new_users = [name.strip().capitalize() for name in new_users]
                USERNAMES += new_users
                print(f"\nUpdated usernames: {USERNAMES}\n")
                time.sleep(2)
                break
            elif choice == "n":
                break
            else:
                print("Please input a valid option.")

        # Modify search terms
        print("Current search terms:")
        for term in SEARCH_TERMS:
            print(term)

        while True:
            choice = input("Remove any search terms? (y/n): ").lower()
            if choice == "y":
                remove = input("Input terms to remove (comma-separated): ").split(",")
                remove = [term.strip().lower() for term in remove]
                SEARCH_TERMS = [term for term in SEARCH_TERMS if term not in remove]
                break
            elif choice == "n":
                break
            else:
                print("Please input a valid option.")
        while True:
            choice = input("Add new search terms? (y/n): ").lower()
            if choice == "y":
                new_terms = input("Input new terms (comma-separated): ").lower().split(",")
                new_terms = [term.strip() for term in new_terms]
                SEARCH_TERMS += new_terms
                break
            elif choice == "n":
                break
            else:
                print("Please input a valid option.")

        print(f"\nCurrent search terms: {SEARCH_TERMS}\n")

        while True:
            choice = input(
                "- Make further changes: (a)\n"
                "- Continue to search: (s)\n"
            ).lower()
            if choice == "s":
                search(USERNAMES, SEARCH_TERMS)
                break
            elif choice == "a":
                amend()
                break
            else:
                print("Please input a valid option.")

    else:
        print("File not found. Please input a correct filename.")
        time.sleep(1)
        amend()


def sai():
    """Load a previous search set from a CSV and initiate a search with those parameters."""
    global PIRATE_URL, USERNAMES, SEARCH_TERMS
    csv_files = [file for file in os.listdir() if file.endswith(".csv")]

    print("Available search sets:")
    for file in csv_files:
        print(file)
    while True:
        choice = input("Input the set to load: ").lower()
        if not choice.endswith(".csv"):
            choice += ".csv"
        if choice in csv_files:
            df = pd.read_csv(choice)
            PIRATE_URL = df.at[0, "URL"]
            proxy_checker(dataset=choice)
            USERNAMES = eval(df.at[0, "Usernames"])
            SEARCH_TERMS = eval(df.at[0, "Search_Terms"])
            search(usernames=USERNAMES, search_terms=SEARCH_TERMS)
            break
        else:
            print("File not found. Please input a correct filename.")


def clean_up():
    """Remove duplicate entries from usernames and search terms in a specified CSV."""
    print("Let's clean up duplicates.\n")
    csv_files = [file for file in os.listdir() if file.endswith(".csv")]

    print("Available data sets:")
    for file in csv_files:
        print(file)
    while True:
        choice = input("Input the set to clean: ").lower()
        if not choice.endswith(".csv"):
            choice += ".csv"

        if choice in csv_files:
            df = pd.read_csv(choice)
            usernames = eval(df.at[0, "Usernames"])
            search_terms = eval(df.at[0, "Search_Terms"])

            # Remove duplicates
            unique_users = list(set(usernames))
            unique_terms = list(set(search_terms))

            df.at[0, "Usernames"] = unique_users
            df.at[0, "Search_Terms"] = unique_terms
            df.to_csv(choice, index=False)
            print("Duplicates removed from users and terms.\n")
            break
        else:
            print("File not found. Please input a correct filename.")


def init():
    """Initialize the script, offering options based on existing datasets."""
    global STATUS
    csv_files = [file for file in os.listdir() if file.endswith(".csv")]

    if csv_files:
        print("Welcome back!\n")
        print('If you are finding utility from this script consider buying me a coffee:'
              '\nhttps://ko-fi.com/massauto\n')
        while True:
            choice = input(
                "Would you like to:\n"
                "Start fresh: (f)\n"
                "Load a previous search: (l)\n"
                "Clean up a dataset: (c)\n"
            ).lower()
            if choice == "f":
                STATUS = "f"
                fresh()
                break
            elif choice == "l":
                sub_choice = input(
                    "Would you like to:\n"
                    "- Amend a search set: (a)\n"
                    "- Search as is: (s)\n"
                ).lower()
                if sub_choice == "s":
                    STATUS = "s"
                    sai()
                    break
                elif sub_choice == "a":
                    STATUS = "a"
                    amend()
                    break
                else:
                    print('Please input a valid option.\n')
            elif choice == "c":
                clean_up()
            else:
                print("Please choose a valid option.")
    else:
        print('Welcome to Pirate User Searcher.\n'
              'There are currently no datasets in this folder so we will start fresh.\n'
              'If You have created datasets in the past, please paste them into the folder'
              ' containing this script or exe.\n')
        time.sleep(4)
        STATUS = 'f'
        fresh()


# Entry point
if __name__ == "__main__":
    init()
