from math import ceil

from fastapi import FastAPI, UploadFile, File, Depends
from fastapi_users import FastAPIUsers

from auth.auth import auth_backend
from database import User
from auth.manager import get_user_manager
from auth.schemas import UserRead, UserCreate
from funcs import *

from operations.router import router as router_operation
from operations.orders import order as order_operation


app = FastAPI(
    title='Ozon'
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(router_operation)
app.include_router(order_operation)
current_user = fastapi_users.current_user()


@app.get("/protected-route")
def protected_route(user: User = Depends(current_user)):
    return f"Hello, {user.username}"


@app.get("/unprotected-route")
def unprotected_route():
    return f"Hello, anonym"


@app.post('/home')
def enter_key(key: str, client_id: str):
    """Функция требует ввода id и ключа для подключения к Ozon-Api."""
    try:
        headers["Client-Id"] = client_id
        headers["Api-Key"] = key
        get_url = "https://api-seller.ozon.ru/v1/report/warehouse/stock"
        json_data = {"language": "DEFAULT",
                     "warehouseId": ["1020000673766000"]}

        id_code = requests.post(get_url, headers=headers, json=json_data).json()
        if 'code' in id_code:
            raise WrongIdKey('Wrong Id or Key')
        goods = Goods()
        goods.oz_goods = load_ozon_stock(id_code)
        stock_dict['goods'] = goods
    except WrongIdKey:
        return {'status': 403, 'error': 'Неправильный Id или ключ'}
    return {'status': 200, 'data': goods}


@app.post('/home/load_stock')
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    upload_excel(file, contents)
    return {'status': 200, 'data': stock_dict.shop_stock}


@app.get('/honme/out_of_stock_shop')
def out_of_stock_shop():
    """Проверяет, какие товары отсутсвуют на складе поставщика"""
    oz_goods = stock_dict['goods'].oz_goods
    shop_stock = stock_dict['goods'].shop_stock
    oz_goods = {key: val for key, val in oz_goods.items() if val != 0 and not key.endswith(('_1', '_2', '_3', '_4'))}
    zero_stock = set(oz_goods.keys()) - set(shop_stock.keys())

    return {'status': 200, 'data': zero_stock if zero_stock else ['Отсутствующих товаров нет']}


@app.get('/honme/out_of_stock_ozon')
def out_of_stock_ozon():
    """Проверяет, какие товары отсутствуют на озн-складе"""
    oz_goods = stock_dict['goods'].oz_goods
    shop_stock = stock_dict['goods'].shop_stock
    empty_stock = {key: val for key, val in oz_goods.items() if val == 0}
    not_empty = set(empty_stock.keys()) & set(shop_stock.keys())
    return {'status': 200, 'data': not_empty if not_empty else ['Отсутствующих товаров нет']}


@app.get('/home/goods_not_in_sale')
def not_int_sale():
    """Выводит артикулы товаров, не учавствующих в акциях"""
    goods_with_id, goods_in_sale = get_sales_data('check_sale')
    not_in_sale_id = set(goods_with_id.keys()) - goods_in_sale
    not_in_sale_article = set()
    not_zero_stock = {key for key, val in stock_dict['goods'].oz_goods.items() if val != 0}
    for val in not_in_sale_id:
        if goods_with_id[val] in not_zero_stock:
            not_in_sale_article.add(goods_with_id[val])
    return {'status': 200, 'data': not_in_sale_article if not_in_sale_article else ['Все товары в акции']}


@app.get('/home/bad_price_in_sale')
def no_profit_price():
    """Выводит артикулы товаров с невыгодной ценой"""
    goods_with_id, goods_in_sale = get_sales_data('check_profit')

    bad_profit = dict()

    for good, discount in goods_in_sale.items():
        if not 39.99 < discount < 45.01 and good in goods_with_id:
            bad_profit[goods_with_id[good]] = round(discount, 2)

    return {'status': 200, 'data': bad_profit if bad_profit else ['Все цены выгодны']}


@app.post('/home/update_prices')
async def update_prices(file: UploadFile = File(...)):
    """Обновляет цены на товары, новые цены берутся из файла-каталога поставщика"""
    try:
        contents = await file.read()
        if not file.filename.endswith(('xls', 'xlsx')):
            raise WrongFile('Not Excel file')
        shop_stock = pd.read_excel(contents, header=5)
        if 'Катал. номер' not in shop_stock or 'ОПТ' not in shop_stock:
            raise WrongFile('Wrong Excel File')
        shop_stock['article'] = shop_stock.pop('Катал. номер')
        shop_stock['price'] = shop_stock.pop('ОПТ')

        shop_prices = dict()
        for art, price in zip(shop_stock['article'], shop_stock['price']):
            if str(art).startswith(needed_art):
                if str(art).startswith("JPS"):
                    shop_prices[str(art) + '_1'] = ceil(price)
                    shop_prices[str(art) + '_2'] = ceil(price) * 2
                    shop_prices[str(art) + '_4'] = ceil(price) * 4
                else:
                    shop_prices[str(art)] = ceil(price)

        json_data = {
            "prices": []
        }

        articles = set(stock_dict['goods'].oz_goods.keys())

        for art, price in shop_prices.items():
            if art in articles:
                json_data['prices'].append(
                    {
                        "auto_action_enabled": "UNKNOWN",
                        "currency_code": "RUB",
                        "offer_id": str(art),
                        "price": str(ceil((1.3 * price + 100) / (0.75 * 0.65))),
                        "price_strategy_enabled": "UNKNOWN"
                    }
                )
        get_url = 'https://api-seller.ozon.ru/v1/product/import/prices'
        requests.post(get_url, headers=headers, json=json_data)
    except Exception as e:
        return {'status': 403, 'error': str(e)}
    return {'status': 200, 'data': 'Цены обновлены'}