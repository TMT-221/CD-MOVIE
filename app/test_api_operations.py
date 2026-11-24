"""Integration tests C.3-C.4; run only on the fresh disposable CI database."""
import os
from decimal import Decimal

from fastapi.testclient import TestClient
from api import app
from write_data import transaction, fetch_one, check


def main():
    admin = os.environ['DB_ADMIN_PASSWORD']
    manager = os.environ['DB_MANAGER_PASSWORD']
    sales = ('sales', os.environ['API_SALES_PASSWORD'])
    boss = ('manager', os.environ['API_MANAGER_PASSWORD'])
    assert os.environ['API_SALES_EMPLOYEE_ID'] == '90102', 'CI identity mismatch'
    product, scarce = 99031, 99032
    invoice, draft = 99033, 99034
    def read(sql, params=()):
        return fetch_one('cd_manager', manager, sql, params)
    def stock(pid):
        return read('SELECT SoLuongTon FROM DIA_CD WHERE MaDia=%s', (pid,))[0]
    def state(iid):
        return read('SELECT TrangThai FROM HOA_DON WHERE MaHD=%s', (iid,))
    if any(read('SELECT MaDia FROM DIA_CD WHERE MaDia=%s', (p,)) for p in (product, scarce)) or any(state(i) for i in (invoice, draft)):
        raise RuntimeError('C.3-C.4 reserved test IDs already exist')
    with transaction('cd_admin', admin) as cur:
        cur.executemany('INSERT INTO DIA_CD (MaDia,MaPhim,PhienBan,GiaBan,SoLuongTon) VALUES (%s,90201,%s,%s,%s)',
                        [(product, 'C4 test', 50000, 10), (scarce, 'C4 scarce', 30000, 1)])
    try:
        with TestClient(app) as client:
            def request(method, path, status, auth=None, **kwargs):
                response = client.request(method, path, auth=auth, **kwargs)
                check(response.status_code == status, f'{method} {path}: expected {status}, got {response.status_code}')
                return response
            def case(num, label, condition=True):
                check(condition, f'C{num:02d} {label}')
            def report(auth=boss, start='2000-01-01', end='2100-12-31', status=200):
                return request('GET', '/reports/revenue', status, auth,
                               params={'start_date':start,'end_date':end})
            def totals():
                data = report().json()
                return sum(r['SoHoaDon'] for r in data), sum((Decimal(r['DoanhThu']) for r in data), Decimal(0))
            base_count, base_amount = totals()
            case(13, 'Unauthenticated rejected', request('GET','/customers',401).headers.get('www-authenticate') == 'Basic')
            request('GET','/customers',401,('sales','wrong-ci-password')); case(14,'Wrong credentials rejected')
            customers = request('GET','/customers',200,sales).json()
            case(15,'Sales customer view: 33 rows, limited columns',len(customers)==33 and all(set(r)=={'MaPerson','HoTen'} for r in customers))
            case(16,'Manager customer view',len(request('GET','/customers',200,boss).json())==33)
            request('GET','/employees',403,sales); case(17,'Sales cannot view employees')
            employees = request('GET','/employees',200,boss).json()
            case(18,'Manager employee list: 11 rows, no salary',len(employees)==11 and all(set(r)=={'MaPerson','HoTen','TrangThaiLamViec','MaQuanLy','LoaiNhanVien'} for r in employees))
            body={'MaHD':invoice,'MaKhachHang':90101}
            request('POST','/invoices',403,boss,json=body); case(19,'Manager cannot create invoice',state(invoice) is None)
            request('POST','/invoices',422,sales,json={**body,'MaNhanVien':10101}); case(20,'Employee impersonation field rejected',state(invoice) is None)
            data=request('POST','/invoices',201,sales,json=body).json()
            case(21,'Create draft; employee bound on server',data=={'MaHD':invoice,'TrangThai':'DangTao'} and read('SELECT MaNhanVien FROM HOA_DON WHERE MaHD=%s',(invoice,))==(90102,))
            request('POST','/invoices',409,sales,json=body); case(22,'Duplicate invoice rejected')
            path=f'/invoices/{invoice}'
            request('POST',path+'/complete',409,sales); case(23,'Empty invoice rejected',state(invoice)==('DangTao',))
            request('POST',path+'/items',422,sales,json={'MaDia':product,'SoLuong':0}); case(24,'Invalid quantity rejected')
            request('POST',path+'/items',201,sales,json={'MaDia':product,'SoLuong':2}); case(25,'Add items without deducting stock',stock(product)==10)
            request('POST',path+'/items',409,sales,json={'MaDia':product,'SoLuong':2}); case(26,'Duplicate line rejected')
            case(27,'Invoice total 100000',Decimal(request('GET',path+'/total',200,sales).json()['TongTien'])==Decimal(100000))
            for method, suffix, kwargs in [('GET','/total',{}),('POST','/complete',{}),('POST','/items',{'json':{'MaDia':product,'SoLuong':1}})]:
                request(method,'/invoices/23001'+suffix,404,sales,**kwargs)
            case(28,'Other employee invoice inaccessible')
            data=request('POST',path+'/complete',200,sales).json(); case(29,'Complete invoice and deduct stock',data['TrangThai']=='HoanTat' and state(invoice)==('HoanTat',) and stock(product)==8)
            request('POST',path+'/complete',409,sales); case(30,'No double stock deduction',stock(product)==8)
            request('POST','/invoices',201,sales,json={'MaHD':draft,'MaKhachHang':90101})
            for pid in (product,scarce):
                request('POST',f'/invoices/{draft}/items',201,sales,json={'MaDia':pid,'SoLuong':2})
            request('POST',f'/invoices/{draft}/complete',409,sales)
            case(31,'Insufficient stock rolls back both products',stock(product)==8 and stock(scarce)==1 and state(draft)==('DangTao',))
            request('PATCH',f'/products/{product}',403,sales,json={'GiaBan':'65000.00'}); case(32,'Sales cannot change price')
            data=request('PATCH',f'/products/{product}',200,boss,json={'GiaBan':'65000.00'}).json()
            case(33,'Manager partial update preserves stock',Decimal(data['GiaBan'])==Decimal(65000) and data['SoLuongTon']==8 and read('SELECT GiaBan,SoLuongTon FROM DIA_CD WHERE MaDia=%s',(product,))==(Decimal(65000),8))
            case(34,'Historical invoice price unchanged',Decimal(request('GET',path+'/total',200,sales).json()['TongTien'])==Decimal(100000))
            request('PATCH',f'/products/{product}',422,boss,json={'GiaBan':'-1'}); case(35,'Negative price rejected')
            request('PATCH','/products/2147483647',404,boss,json={'SoLuongTon':5}); case(36,'Missing product rejected')
            case(37,'Revenue counts completed invoice only',totals()==(base_count+1,base_amount+Decimal(100000)))
            report(auth=sales,status=403); case(38,'Sales cannot view revenue')
            report(start='2026-12-31',end='2026-01-01',status=422); case(39,'Invalid date range rejected')
    finally:
        with transaction('cd_admin',admin) as cur:
            cur.execute('DELETE FROM CHI_TIET_HOA_DON WHERE MaHD IN (%s,%s)',(invoice,draft))
            cur.execute('DELETE FROM HOA_DON WHERE MaHD IN (%s,%s)',(invoice,draft))
            cur.execute('DELETE FROM DIA_CD WHERE MaDia IN (%s,%s)',(product,scarce))
    check(not any(state(i) for i in (invoice,draft)) and not any(read('SELECT MaDia FROM DIA_CD WHERE MaDia=%s',(p,)) for p in (product,scarce)), 'Test fixtures removed')
    print('C.3-C.4: all 27 API operations test cases PASS.')


if __name__=='__main__':
    main()
