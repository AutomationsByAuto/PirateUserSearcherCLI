# Pirate User Searcher CLI

A command-line Python script to search for files on Pirate Bay, targeting specific users and search terms. It uses a Pirate Bay API to fetch results efficiently, allowing searches across multiple users.

## Features
- Search for torrents uploaded by specific users on Pirate Bay using the apibay.org API.
- Support multiple usernames and search terms in a single query for efficient searching.
- Display detailed torrent information, including name, size (in GB), upload date, seeders, and URLs (e.g., screenshot links from torrent descriptions, limited to the first 100 results).
- Sort results by various criteria, including newest, oldest, most seeded, largest/smallest file size, or random, with an option to re-sort after viewing.
- Save search configurations (URL, usernames, search terms) to a CSV file for reuse, with options to overwrite or save as a new dataset.
- Load previous search configurations from CSV files to skip manual re-entry of data.
- Amend existing CSV datasets by adding/removing usernames or search terms, or updating the Pirate Bay URL.
- Remove duplicate usernames and search terms from saved datasets for cleaner configurations.
- Validate Pirate Bay proxy URLs, prompting for a new URL if the current one is unresponsive.
- Filter out dead torrent URLs to ensure only working results are displayed.


## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/AutomationsByAuto/PirateUserSearcherCLI.git
   ```
2. Navigate to the project directory:
   ```bash
   cd PirateUserSearcherCLI
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the script in a terminal or IDE like PyCharm:
```bash
python PirateUserSearcherCLI.py
```

- Enter usernames and search terms when prompted.
- Results include torrent names, URLs, and other details.
- **Note**: URLs are not clickable in Windows CMD. Use an IDE like PyCharm for better usability.

## Requirements
See [requirements.txt](requirements.txt) for dependencies (e.g., `aiohttp`, `pandas`, `requests`).

## Motivation
Having noticed that the Pirate Bay did not support this feature I decided to make it my next project.  

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Feel free to submit issues or pull requests to improve the project.

## Disclaimer
This tool is for educational purposes only. Ensure compliance with local laws and respect intellectual property rights.
