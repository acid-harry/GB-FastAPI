from fastapi import FastAPI, HTTPException, Depends, status
from tortoise import Tortoise, fields
from tortoise.contrib.fastapi import register_tortoise
from tortoise.models import Model
from typing import List
from fastapi import Query

# Инициализация FastAPI
app = FastAPI()

# Подключение к базе данных (SQLite)
Tortoise.init(
    db_url='sqlite://db.sqlite3',
    modules={'models': ['main']},
)
Tortoise.generate_schemas()

# Модель для пользователей
class User(Model):
    id = fields.IntField(pk=True)
    first_name = fields.CharField(max_length=255)
    last_name = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255)
    password = fields.CharField(max_length=255)

# Модель для товаров
class Product(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField()
    price = fields.FloatField()

# Модель для заказов
class Order(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='orders')
    product = fields.ForeignKeyField('models.Product', related_name='orders')
    order_date = fields.DatetimeField(auto_now_add=True)
    status = fields.CharField(max_length=255)

class UserUpdate(BaseModel):
    first_name: str = None
    last_name: str = None
    email: str = None
    password: str = None

class ProductUpdate(BaseModel):
    name: str = None
    description: str = None
    price: float = None

class OrderUpdate(BaseModel):
    user_id: int = None
    product_id: int = None
    status: str = None

# Регистрация моделей Tortoise
Tortoise.register_model(User)
Tortoise.register_model(Product)
Tortoise.register_model(Order)

# Модели Pydantic для валидации данных
from pydantic import BaseModel

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float

class OrderCreate(BaseModel):
    user_id: int
    product_id: int
    status: str

# Роуты для CRUD операций
@app.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    user_obj = await User.create(**user.dict())
    return user_obj

@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int):
    user = await User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/products/", response_model=Product)
async def create_product(product: ProductCreate):
    product_obj = await Product.create(**product.dict())
    return product_obj

@app.get("/products/{product_id}", response_model=Product)
async def read_product(product_id: int):
    product = await Product.get(id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/orders/", response_model=Order)
async def create_order(order: OrderCreate):
    order_obj = await Order.create(**order.dict())
    return order_obj

@app.get("/orders/{order_id}", response_model=Order)
async def read_order(order_id: int):
    order = await Order.get(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: UserUpdate):
    existing_user = await User.get(id=user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in user.dict(exclude_unset=True).items():
        setattr(existing_user, field, value)
    await existing_user.save()
    return existing_user

@app.delete("/users/{user_id}", response_model=dict)
async def delete_user(user_id: int):
    deleted_count = await User.filter(id=user_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@app.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: int, product: ProductUpdate):
    existing_product = await Product.get(id=product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in product.dict(exclude_unset=True).items():
        setattr(existing_product, field, value)
    await existing_product.save()
    return existing_product

@app.delete("/products/{product_id}", response_model=dict)
async def delete_product(product_id: int):
    deleted_count = await Product.filter(id=product_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

@app.put("/orders/{order_id}", response_model=Order)
async def update_order(order_id: int, order: OrderUpdate):
    existing_order = await Order.get(id=order_id)
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")

    for field, value in order.dict(exclude_unset=True).items():
        setattr(existing_order, field, value)
    await existing_order.save()
    return existing_order

@app.delete("/orders/{order_id}", response_model=dict)
async def delete_order(order_id: int):
    deleted_count = await Order.filter(id=order_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}

@app.get("/users/", response_model=List[User])
async def list_users():
    return await User.all()

@app.get("/products/", response_model=List[Product])
async def list_products():
    return await Product.all()

@app.get("/users/{user_id}/orders/", response_model=List[Order])
async def list_user_orders(user_id: int):
    user = await User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await Order.filter(user=user)

# Роут для подсчета общей суммы заказов пользователя
@app.get("/users/{user_id}/total-order-amount/", response_model=dict)
async def total_order_amount(user_id: int):
    user = await User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_amount = await Order.filter(user=user).aggregate(fields.Sum('product__price'))
    return {"total_amount": total_amount["product__price__sum"] or 0}

# Роут для сортировки и фильтрации товаров
@app.get("/products/sorted/", response_model=List[Product])
async def list_sorted_products(
    min_price: float = Query(None, gt=0, description="Minimum price filter"),
    max_price: float = Query(None, gt=0, description="Maximum price filter"),
    sort_by: str = Query(None, description="Field to sort by"),
    desc: bool = Query(False, description="Sort in descending order")
):
    query = Product.all()

    if min_price is not None:
        query = query.filter(price__gte=min_price)
    if max_price is not None:
        query = query.filter(price__lte=max_price)
    if sort_by:
        query = query.order_by(f"{sort_by}{' DESC' if desc else ''}")

    return await query

@app.get("/orders/", response_model=List[Order])
async def list_orders():
    return await Order.all()
