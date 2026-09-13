import requests
import os 
import json
# Fetches circuit data from https://formula-timer.com 
# Stores the raw JSON file in sources folder

def store_circuit_metadata():

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) Gecko/20100101 Firefox/155.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://formula-timer.com/',
        'Origin': 'https://formula-timer.com',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Priority': 'u=4',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }

    res = requests.get('https://api.multiviewer.app/api/v1/circuits', headers=headers)
    print(res.text)

    if res.status_code == 200:
        data = res.json()

        os.makedirs("sources/f1_timer", exist_ok=True)

        with open("sources/f1_timer/circuits_f1_timer.json", "w") as f:
            json.dump(data, f, indent=4)

        print("Successfully wrote circuit data to sources/f1_timer/circuits_f1_timer.json")
    else:
        print("Failed to fetch circuit data")
        print(res.text)

def store_circuit_shape(circuit_id , circuit_name) :
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) Gecko/20100101 Firefox/155.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://formula-timer.com/',
        'Origin': 'https://formula-timer.com',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Priority': 'u=4',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }

    res = requests.get(f'https://api.multiviewer.app/api/v1/circuits/{circuit_id}/2026', headers=headers)
    # print(res.text)
    data = res.json()

    if res.status_code == 200:
        data = res.json()

        os.makedirs("sources/f1_timer/circuit_shapes", exist_ok=True)

        with open(f"sources/f1_timer/circuit_shapes/{circuit_name}.json", "w") as f:
            json.dump(data, f, indent=4)

        print(f"Successfully wrote circuit data to sources/f1_timer/{circuit_name}.json")
    else:
        print(f"Failed to fetch circuit shape data for {circuit_name}")
        print(res.text)

def store_circuits_shapes():

    print("Opening circuit metadata file...")
    filepath = "sources/f1_timer/circuits_f1_timer.json"
    with open(filepath, "r") as f:
        circuits_metadata = json.load(f)
    print("Successfully loaded circuit metadata file")
        
    for circuit_key, info in circuits_metadata.items():
        circuit_id = circuit_key
        circuit_name = info["name"]
        circuit_country = info["country"]

        print(f"Storing circuit shape for {circuit_name} ({circuit_id})")
        store_circuit_shape(circuit_id , circuit_name)
        print('success')
    
    print("Stored all circuits shapes")

if __name__ == '__main__':
    # store_circuit_metadata()
    store_circuits_shapes()
