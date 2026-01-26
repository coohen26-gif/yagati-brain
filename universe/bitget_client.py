import requests

class BitgetClient:
    def __init__(self):
        self.base_url = 'https://api.bitget.com'
        self.api_key = 'your_api_key'
        self.secret = 'your_api_secret'
        self.passphrase = 'your_api_passphrase'

    def get_product_info(self):
        url = f'{self.base_url}/api/v1/products'
        params = {"productType": "umcbl"}
        response = requests.get(url, params=params)
        return response.json()