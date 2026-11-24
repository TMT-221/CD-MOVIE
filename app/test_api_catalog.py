"""Integration tests: run against the fresh Lab 01 demo + Lab 02 sample DB."""
from decimal import Decimal

from fastapi.testclient import TestClient
from api import app


def check(condition, name):
    if not condition:
        raise RuntimeError(f"FAIL: {name}")
    print(f"PASS: {name}")


def main():
    with TestClient(app) as client:
        def get(path, status=200, **kwargs):
            response = client.get(path, **kwargs)
            if response.status_code != status:
                raise RuntimeError(f"GET {path}: expected {status}, got {response.status_code}")
            return response

        check(get('/').json()['service'] == 'Movie CD Store API', 'C01 Home: 200')
        check(get('/health').json() == {'status': 'ok', 'database': 'connected'}, 'C02 Database health: 200')
        check(len(get('/movies').json()) == 21, 'C03 Movies: 21 records')
        result = get('/movies/search', params={'keyword': 'Avengers'}).json()
        check({row['MaPhim'] for row in result} == {20003, 20006}, 'C04 Search: 2 Avengers movies')
        check(get('/movies/search', params={'keyword': 'ZZZ_NOT_A_MOVIE_789'}).json() == [], 'C05 No matching movies: []')
        check(get('/movies/search', status=422, params={'keyword': ''}).status_code == 422, 'C06 Empty keyword: 422')
        check(len(get('/movies/genres').json()) == 64, 'C07 Movie-genre links: 64')
        check(len(get('/products').json()) == 41, 'C08 Products: 41 records')
        product = get('/products/22001').json()
        check(product['MaDia'] == 22001 and product['TenPhim'] == 'Avatar'
              and Decimal(str(product['GiaBan'])) == Decimal('60000')
              and product['SoLuongTon'] == 8, 'C09 Product 22001: 200, correct data')
        check(get('/products/2147483647', status=404).status_code == 404, 'C10 Missing product: 404')
        check(get('/products/-1', status=422).status_code == 422, 'C11 Invalid product ID: 422')
        schema = get('/openapi.json').json()
        check('/movies' in schema['paths'] and '/products/{product_id}' in schema['paths']
              and get('/docs').status_code == 200, 'C12 OpenAPI and Swagger UI: 200')
    print('C.1-C.2: all 12 catalog API test cases PASS.')


if __name__ == '__main__':
    main()
