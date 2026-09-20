from decimal import Decimal


def auth(client, email, company):
    result=client.post("/api/v1/auth/register",json={"company_name":company,"full_name":"Admin","email":email,"password":"MotDePasseSolide123!"})
    return {"Authorization":f"Bearer {result.json()['access_token']}"}


def category(client, headers, name="Informatique"):
    return client.post("/api/v1/categories",headers=headers,json={"name":name}).json()


def product(client, headers, category_id, stock=10, minimum=3):
    return client.post("/api/v1/products",headers=headers,json={"name":"Lenovo ThinkPad","category_id":category_id,"purchase_price":"250000.00","selling_price":"320000.00","current_stock":stock,"minimum_stock":minimum}).json()


def test_category_crud_and_isolation(client):
    a=auth(client,"a@example.com","Entreprise A"); b=auth(client,"b@example.com","Entreprise B")
    item=category(client,a)
    assert client.get("/api/v1/categories",headers=b).json()==[]
    assert client.get(f"/api/v1/categories/{item['id']}",headers=b).status_code==404
    changed=client.patch(f"/api/v1/categories/{item['id']}",headers=a,json={"description":"Matériel"})
    assert changed.json()["description"]=="Matériel"
    assert client.delete(f"/api/v1/categories/{item['id']}",headers=a).status_code==204
    assert client.get(f"/api/v1/categories/{item['id']}",headers=a).json()["is_active"] is False


def test_product_decimal_filters_deactivation_and_isolation(client):
    a=auth(client,"products-a@example.com","Entreprise A"); b=auth(client,"products-b@example.com","Entreprise B")
    cat=category(client,a); item=product(client,a,cat["id"])
    assert item["purchase_price"]=="250000.00"
    assert len(client.get("/api/v1/products",headers=a,params={"search":"Think"}).json())==1
    assert client.get(f"/api/v1/products/{item['id']}",headers=b).status_code==404
    changed=client.patch(f"/api/v1/products/{item['id']}",headers=a,json={"selling_price":"350000.00"})
    assert changed.json()["selling_price"]=="350000.00"
    assert client.delete(f"/api/v1/products/{item['id']}",headers=a).status_code==204
    assert client.get("/api/v1/products",headers=a,params={"is_active":False}).json()[0]["id"]==item["id"]


def test_stock_entry_exit_adjustment_return_and_alerts(client):
    h=auth(client,"stock@example.com","Stock"); p=product(client,h,category(client,h)["id"],stock=10,minimum=12)
    def move(kind,qty): return client.post("/api/v1/stock/movements",headers=h,json={"product_id":p["id"],"movement_type":kind,"quantity":qty})
    entry=move("ENTRY",5).json(); assert (entry["stock_before"],entry["stock_after"])==(10,15)
    exit=move("EXIT",3).json(); assert (exit["stock_before"],exit["stock_after"])==(15,12)
    adjust=move("ADJUSTMENT",20).json(); assert (adjust["stock_before"],adjust["stock_after"])==(12,20)
    returned=move("RETURN",2).json(); assert returned["stock_after"]==22
    assert client.get("/api/v1/stock/alerts",headers=h).json()==[]
    move("ADJUSTMENT",0) # validation rejected; no state change
    move("ADJUSTMENT",5)
    assert client.get("/api/v1/stock/alerts",headers=h).json()[0]["status"]=="LOW_STOCK"
    move("ADJUSTMENT",1)
    assert client.get("/api/v1/stock/alerts",headers=h).json()[0]["status"]=="LOW_STOCK"


def test_stock_rejects_negative_nonexistent_and_cross_company_product(client):
    a=auth(client,"move-a@example.com","Entreprise A"); b=auth(client,"move-b@example.com","Entreprise B"); p=product(client,a,category(client,a)["id"],stock=3)
    response=client.post("/api/v1/stock/movements",headers=a,json={"product_id":p["id"],"movement_type":"EXIT","quantity":5})
    assert response.status_code==422 and "Stock insuffisant" in response.json()["detail"]
    assert client.get(f"/api/v1/stock/products/{p['id']}",headers=b).status_code==404
    response=client.post("/api/v1/stock/movements",headers=b,json={"product_id":p["id"],"movement_type":"ENTRY","quantity":1})
    assert response.status_code==404
