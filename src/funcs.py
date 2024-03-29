import requests
import pandas as pd


class WrongIdKey(Exception):
    pass


class WrongFile(Exception):
    pass


class Goods:
    def __init__(self):
        self.oz_goods = None
        self.shop_stock = None


stock_dict = dict()
key_id = dict()

headers = {
    "Host": "api-seller.ozon.ru",
    "Client-Id": None,
    "Api-Key": None,
    "Content-Type": "application/json"
}

orders = {
    "dir": "ASC",
    "filter": {
        "since": None,
        "status": "awaiting_packaging",
        "to": None,
        "warehouse_id": [
            "1020000673766000"
        ]
    },
    "limit": 1000,
    "offset": 0
}


def load_ozon_stock(id_code):
    """Выгрузка товаров из ЛК Ozon-Seller"""
    while True:
        resp_data = requests.post("https://api-seller.ozon.ru/v1/report/info", headers=headers,
                                  json=id_code["result"]).json()
        if resp_data['result']['status'] == 'success':
            break

    xl_file = pd.read_excel(resp_data["result"]["file"], header=0)

    xl_file['article'] = xl_file.pop('Unnamed: 2') if 'Unnamed: 2' in xl_file else xl_file.pop('Артикул')
    xl_file['count'] = xl_file.pop('Unnamed: 4') if 'Unnamed: 4' in xl_file \
        else xl_file.pop('Доступно на моем складе, шт')

    goods = dict()
    for art, count in zip(xl_file['article'], xl_file['count']):
        if art.startswith(needed_art) and not art.endswith('_'):
            goods[art] = count
    return goods


def get_sales_data(func):
    """Возвращает товары, участвующие в акции. Подсчитывает скидку по акции."""
    get_url = 'https://api-seller.ozon.ru/v1/actions'
    id_code = requests.get(get_url, headers=headers).json()
    sale_id = {sale['id']: sale['participating_products_count'] for sale in id_code['result']}
    get_url = 'https://api-seller.ozon.ru/v1/actions/products'
    goods_in_sale = set() if func == 'check_sale' else dict()
    for id_, count in sale_id.items():
        json_data = {
            "action_id": id_,
            "limit": min(count, 1000),
            "offset": 0
        }
        id_code = requests.post(get_url, headers=headers, json=json_data).json()
        for good in id_code['result']['products']:
            if func == 'check_profit':
                goods_in_sale[good['id']] = (good['price'] - good['action_price']) / good['price'] * 100
            else:
                goods_in_sale.add(good['id'])

    get_url = 'https://api-seller.ozon.ru/v1/report/products/create'
    json_data = {
        "language": "DEFAULT",
        "offer_id": [],
        "search": "",
        "sku": [],
        "visibility": "ALL"
    }
    id_code = requests.post(get_url, headers=headers, json=json_data).json()
    while True:
        resp_data = requests.post("https://api-seller.ozon.ru/v1/report/info", headers=headers,
                                  json=id_code["result"]).json()
        if resp_data['result']['status'] == 'success':
            break

    xl_file = pd.read_csv(resp_data["result"]["file"], on_bad_lines='skip', delimiter=';')
    goods_with_id = dict()

    for art, id_ in zip(xl_file['Артикул'], xl_file['Ozon Product ID']):
        if art[1:].startswith(needed_art):
            goods_with_id[id_] = art[1:]
    return goods_with_id, goods_in_sale


def upload_excel(file, contents):
    try:
        if not file.filename.endswith(('xls', 'xlsx')):
            raise WrongFile('Not Excel file')

        shop_stock = pd.read_excel(contents, header=5)
        if 'Катал. номер' not in shop_stock or 'НГЛ' not in shop_stock or 'ОПТ' not in shop_stock:
            raise WrongFile('Wrong Excel File')
        shop_stock['article'] = shop_stock.pop('Катал. номер')
        shop_stock['count'] = shop_stock.pop('НГЛ')
        shop_stock['price'] = shop_stock.pop('ОПТ')
        try:
            stock = stock_dict['goods']
        except KeyError:
            stock = Goods()

        stock.shop_stock = dict()
        for art, count, price in zip(shop_stock['article'], shop_stock['count'], shop_stock['price']):
            if str(art).startswith(needed_art) and len(art) <= 10:
                stock.shop_stock[art] = (count, price)
    except Exception as e:
        return {'status': 403, 'error': str(e)}
    return stock.shop_stock


needed_art = ('JSL', 'JBP', 'JAA', 'JAS', 'JDW', 'JSB', 'JDA', 'JFM', 'JPP', 'JDK', 'JBS', 'JSR', 'JPS')
