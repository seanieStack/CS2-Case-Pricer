import csv
import os
import requests
import json
import time
import yaml
import re
from colorama import Fore, Back, Style, init

init(autoreset=True)

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

INVENTORY_FILE = config['settings']['inventory_file']
STEAM_API_URL = config['settings']['steam_api_url']
API_DELAY = config['settings']['api_delay']
CURRENCY = config['settings']['currency']

CASES = config['cases']

CURRENCY_SYMBOLS = {
    1: '$',      # USD (US Dollar)
    2: '£',      # GBP (British Pound)
    3: '€',      # EUR (Euro)
    4: 'CHF',    # CHF (Swiss Franc)
    5: '₽',      # RUB (Russian Ruble)
    6: 'zł',     # PLN (Polish Złoty)
    7: 'R$',     # BRL (Brazilian Real)
    8: 'kr',     # NOK (Norwegian Krone)
    9: 'kr',     # SEK (Swedish Krona)
    10: 'Rp',    # IDR (Indonesian Rupiah)
    11: 'RM',    # MYR (Malaysian Ringgit)
    12: '₱',     # PHP (Philippine Peso)
    13: 'S$',    # SGD (Singapore Dollar)
    14: '฿',     # THB (Thai Baht)
    15: '₫',     # VND (Vietnamese Dong)
    16: '₩',     # KRW (South Korean Won)
    17: '₺',     # TRY (Turkish Lira)
    18: '₴',     # UAH (Ukrainian Hryvnia)
    19: 'MX$',   # MXN (Mexican Peso)
    20: 'CA$',   # CAD (Canadian Dollar)
    21: 'A$',    # AUD (Australian Dollar)
    22: 'NZ$',   # NZD (New Zealand Dollar)
    23: '¥',     # CNY (Chinese Yuan)
    24: '₹',     # INR (Indian Rupee)
    25: 'CLP',   # CLP (Chilean Peso)
    26: 'S/',    # PEN (Peruvian Sol)
    27: 'COL$',  # COP (Colombian Peso)
    28: 'R',     # ZAR (South African Rand)
    29: 'HK$',   # HKD (Hong Kong Dollar)
    30: 'NT$',   # TWD (Taiwan Dollar)
    31: '﷼',     # SAR (Saudi Riyal)
    32: 'د.إ',   # AED (UAE Dirham)
    34: 'AR$',   # ARS (Argentine Peso)
    35: '₪',     # ILS (Israeli Shekel)
    37: '₸',     # KZT (Kazakhstani Tenge)
    38: 'د.ك',   # KWD (Kuwaiti Dinar)
    39: '﷼',     # QAR (Qatari Riyal)
    40: '₡',     # CRC (Costa Rican Colón)
    41: 'UY$',   # UYU (Uruguayan Peso)
}

CURRENCY_SYMBOL = CURRENCY_SYMBOLS[int(CURRENCY)]

def main():
    print_header()
    inventory = load_or_create_inventory()
    sync_inventory_with_cases(inventory)
    
    while True:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}=== CS2 Case Inventory Manager ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}1. Check Current Prices{Style.RESET_ALL}")
        print(f"{Fore.CYAN}2. Update Case Quantities{Style.RESET_ALL}")
        print(f"{Fore.CYAN}3. View Inventory{Style.RESET_ALL}")
        print(f"{Fore.RED}4. Exit{Style.RESET_ALL}")
        
        choice = get_menu_choice(1, 4)
        
        if choice == 1:
            check_prices(inventory)
        elif choice == 2:
            update_quantities(inventory)
        elif choice == 3:
            display_inventory(inventory)
        elif choice == 4:
            break

def print_header():
    lines = [
        " ▄████▄    ██████     ▄████▄   ▄▄▄        ██████ ▓█████     ██▓███   ██▀███   ██▓ ▄████▄  ▓█████  ██▀███  ",
        "▒██▀ ▀█  ▒██    ▒    ▒██▀ ▀█  ▒████▄    ▒██    ▒ ▓█   ▀    ▓██░  ██▒▓██ ▒ ██▒▓██▒▒██▀ ▀█  ▓█   ▀ ▓██ ▒ ██▒",
        "▒▓█    ▄ ░ ▓██▄      ▒▓█    ▄ ▒██  ▀█▄  ░ ▓██▄   ▒███      ▓██░ ██▓▒▓██ ░▄█ ▒▒██▒▒▓█    ▄ ▒███   ▓██ ░▄█ ▒",
        "▒▓▓▄ ▄██▒  ▒   ██▒   ▒▓▓▄ ▄██▒░██▄▄▄▄██   ▒   ██▒▒▓█  ▄    ▒██▄█▓▒ ▒▒██▀▀█▄  ░██░▒▓▓▄ ▄██▒▒▓█  ▄ ▒██▀▀█▄  ",
        "▒ ▓███▀ ░▒██████▒▒   ▒ ▓███▀ ░ ▓█   ▓██▒▒██████▒▒░▒████▒   ▒██▒ ░  ░░██▓ ▒██▒░██░▒ ▓███▀ ░░▒████▒░██▓ ▒██▒",
        "░ ░▒ ▒  ░▒ ▒▓▒ ▒ ░   ░ ░▒ ▒  ░ ▒▒   ▓▒█░▒ ▒▓▒ ▒ ░░░ ▒░ ░   ▒▓▒░ ░  ░░ ▒▓ ░▒▓░░▓  ░ ░▒ ▒  ░░░ ▒░ ░░ ▒▓ ░▒▓░",
        "  ░  ▒   ░ ░▒  ░ ░     ░  ▒     ▒   ▒▒ ░░ ░▒  ░ ░ ░ ░  ░   ░▒ ░       ░▒ ░ ▒░ ▒ ░  ░  ▒    ░ ░  ░  ░▒ ░ ▒░",
        "░        ░  ░  ░     ░          ░   ▒   ░  ░  ░     ░      ░░         ░░   ░  ▒ ░░           ░     ░░   ░ ",
        "░ ░            ░     ░ ░            ░  ░      ░     ░  ░               ░      ░  ░ ░         ░  ░   ░     ",
        "░                    ░                                                           ░                        "
    ]
    
    print()
    for i, line in enumerate(lines):
        if i < 5:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + line + Style.RESET_ALL)
        else:
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + line + Style.RESET_ALL)
    print()

def load_or_create_inventory():
    if os.path.exists(INVENTORY_FILE):
        return load_inventory()
    else:
        return create_inventory()


def load_inventory():
    with open(INVENTORY_FILE, "r") as f:
        return list(csv.DictReader(f))


def create_inventory():
    inventory = []
    
    print(f"{Fore.YELLOW}{Style.BRIGHT}Creating new inventory...{Style.RESET_ALL}")
    for case_name in CASES:
        amount = get_valid_amount(f"{Fore.MAGENTA}Number of {case_name}: {Style.RESET_ALL}")
        inventory.append({'name': case_name, 'amount': str(amount)})
    
    save_inventory(inventory)
    print(f"{Fore.GREEN}Inventory created successfully!{Style.RESET_ALL}")
    return inventory


def sync_inventory_with_cases(inventory):
    inv_names = {item['name'] for item in inventory}
    new_cases = [case for case in CASES if case not in inv_names]
    
    if new_cases:
        print(f"\n{Fore.YELLOW}Found {len(new_cases)} new case(s) to add:{Style.RESET_ALL}")
        for case_name in new_cases:
            amount = get_valid_amount(f"{Fore.MAGENTA}Number of {case_name}: {Style.RESET_ALL}")
            inventory.append({'name': case_name, 'amount': str(amount)})
        save_inventory(inventory)
        print(f"{Fore.GREEN}New cases added to inventory!{Style.RESET_ALL}")


def save_inventory(inventory):
    with open(INVENTORY_FILE, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'amount'])
        writer.writeheader()
        writer.writerows(inventory)


def check_prices(inventory):    
    items_to_check = [item for item in inventory if int(item['amount']) > 0]
    
    if not items_to_check:
        print(f"{Fore.RED}No items in inventory to check prices for.{Style.RESET_ALL}")
        input(f"\n{Fore.WHITE}Press Enter to continue...{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}Fetching Steam Market Prices...{Style.RESET_ALL}")
    prices = {}
    total_value = 0.0
    
    for i, item in enumerate(items_to_check, 1):
        print(f"{Fore.CYAN}Fetching price {i}/{len(items_to_check)}: {Fore.WHITE}{item['name']}{Style.RESET_ALL}", end="")
        price = fetch_steam_price(item['name'])
        prices[item['name']] = price
        
        if price:
            print(f"{Fore.GREEN}: {CURRENCY_SYMBOL}{price:.2f}{Style.RESET_ALL}")
        
        if i < len(items_to_check):
            time.sleep(API_DELAY)

    print(f"\n{Fore.YELLOW}{Style.BRIGHT}Price Summary:{Style.RESET_ALL}")
    for item in inventory:
        quantity = int(item['amount'])
        if quantity > 0:
            price = prices.get(item['name'])
            if price is not None:
                item_total = price * quantity
                total_value += item_total
                print(f"{Fore.WHITE}{item['name']:<40}{Style.RESET_ALL} | {Fore.CYAN}{quantity:>3}{Style.RESET_ALL} x {Fore.GREEN}{CURRENCY_SYMBOL}{price:>6.2f}{Style.RESET_ALL} = {Fore.YELLOW}{CURRENCY_SYMBOL}{item_total:>8.2f}{Style.RESET_ALL}")
            else:
                print(f"{Fore.WHITE}{item['name']:<40}{Style.RESET_ALL} | {Fore.CYAN}{quantity:>3}{Style.RESET_ALL} x {Fore.RED}[Price unavailable]{Style.RESET_ALL}")
    
    print(f"{Fore.MAGENTA}-{Style.RESET_ALL}"*60)
    print(f"{Fore.YELLOW}{Style.BRIGHT}{'TOTAL VALUE:':<40}{Style.RESET_ALL} | {'':<15} {Fore.GREEN}{Style.BRIGHT}{CURRENCY_SYMBOL}{total_value:>8.2f}{Style.RESET_ALL}")
    input(f"\n{Fore.WHITE}Press Enter to continue...{Style.RESET_ALL}")


def fetch_steam_price(market_hash_name):
    params = {
        'currency': CURRENCY,
        'appid': 730,
        'market_hash_name': market_hash_name
    }
    
    try:
        response = requests.get(STEAM_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success') and data.get('median_price'):
            return parse_price(data['median_price'])
        else:
            return None
            
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"{Fore.RED}Error fetching price for {market_hash_name}: {e}{Style.RESET_ALL}")
        return None


def parse_price(price_str):
    try:
        cleaned = re.sub(r'[^\d.,+-]', '', price_str)
        cleaned = cleaned.replace(',', '.').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


def update_quantities(inventory):
    while True:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}Current Inventory:{Style.RESET_ALL}")
        for i, item in enumerate(inventory, 1):
            amount = int(item['amount'])
            color = Fore.GREEN if amount > 0 else Fore.RED
            print(f"{Fore.CYAN}{i:2d}.{Style.RESET_ALL} {Fore.WHITE}{item['name']}{Style.RESET_ALL}: {color}{item['amount']}{Style.RESET_ALL}")
        
        print(f"{Fore.MAGENTA}{len(inventory)+1:2d}. Update All{Style.RESET_ALL}")
        print(f"{Fore.RED}{len(inventory)+2:2d}. Back to Main Menu{Style.RESET_ALL}")
        
        choice = get_menu_choice(1, len(inventory) + 2)
        
        if choice <= len(inventory):
            item = inventory[choice - 1]
            print(f"\n{Fore.YELLOW}Updating: {Fore.WHITE}{item['name']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Current amount: {Fore.WHITE}{item['amount']}{Style.RESET_ALL}")
            new_amount = get_valid_amount(f"{Fore.MAGENTA}Enter new amount: {Style.RESET_ALL}")
            item['amount'] = str(new_amount)
            save_inventory(inventory)
            print(f"{Fore.GREEN}Updated {item['name']} to {new_amount}{Style.RESET_ALL}")
            break
            
        elif choice == len(inventory) + 1:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}Updating all cases:{Style.RESET_ALL}")
            for item in inventory:
                print(f"\n{Fore.CYAN}Current: {Fore.WHITE}{item['name']}{Style.RESET_ALL} = {Fore.WHITE}{item['amount']}{Style.RESET_ALL}")
                new_amount = get_valid_amount(f"{Fore.MAGENTA}New amount for {item['name']}: {Style.RESET_ALL}")
                item['amount'] = str(new_amount)
            save_inventory(inventory)
            print(f"{Fore.GREEN}{Style.BRIGHT}All cases updated!{Style.RESET_ALL}")
            break
            
        else:
            break


def display_inventory(inventory):
    total_items = sum(int(item['amount']) for item in inventory)
    
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}Inventory Overview:{Style.RESET_ALL}")
    for item in inventory:
        amount = int(item['amount'])
        if amount > 0:
            print(f"{Fore.WHITE}{item['name']:<40}{Style.RESET_ALL} | {Fore.GREEN}{amount:>3}{Style.RESET_ALL}")
    
    print(f"{Fore.MAGENTA}-{Style.RESET_ALL}"*60)
    print(f"{Fore.YELLOW}{Style.BRIGHT}{'Total Items:':<40}{Style.RESET_ALL} | {Fore.GREEN}{Style.BRIGHT}{total_items:>3}{Style.RESET_ALL}")
    input(f"\n{Fore.WHITE}Press Enter to continue...{Style.RESET_ALL}")


def get_valid_amount(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value >= 0:
                return value
            print(f"{Fore.RED}Please enter a non-negative number.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")


def get_menu_choice(min_val, max_val):
    while True:
        try:
            choice = int(input(f"\n{Fore.MAGENTA}Select an option ({min_val}-{max_val}): {Style.RESET_ALL}"))
            if min_val <= choice <= max_val:
                return choice
            print(f"{Fore.RED}Please enter a number between {min_val} and {max_val}.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()