# CS2 Case Pricer

 ## Features
 - Track all base in game cases
 - Real-time Steam market prices
 - Calculate total case value
 - Stores inventory for future price checks

## Installation

 1. Clone the repository
```bash
git clone https://github.com/seanieStack/CS2-Case-Pricer.git
cd CS2-Case-Pricer
```
2. Create and activate virtual enviroment
- Linux:
```bash
python -m venv venv
source venv/bin/activate
```
- Windows: 
```bash
python -m venv venv
venv\Scripts\activate
```
3. Install dependencies
 ```bash
 pip install -r requirements.txt
 ```
4. Run the program
```bash
python main.py
```

## Configuration
You can edit your preferred currency in `config.yaml`:
```yaml
settings:
  currency: 3  # Change this number for different currencies, these are listed in the config file
```

## Requirements
- Python 3.13.5

