from pydantic import BaseModel, EmailStr
from fastapi import FastAPI, HTTPException, Query, status
from tortoise import Tortoise, fields
from tortoise.contrib.fastapi import register_tortoise
from tortoise.models import Model
from typing import List

app = FastAPI()

# Функция для инициализации и подключения к базе данных
async def init():
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['main']},
    )
    await Tortoise.generate_schemas()

# Событийный цикл для вызова асинхронных функций
@app.on_event("startup")
async def startup_event():
    await init()

@app.on_event("shutdown")
async def shutdown_event():
    await Tortoise.close_connections()

# Модели Pydantic для валидации данных
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class UserPydantic(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float

class ProductPydantic(BaseModel):
    id: int
    name: str
    description: str
    price: float

class OrderCreate(BaseModel):
    user_id: int
    product_id: int
    status: str

class OrderPydantic(BaseModel):
    id: int
    user_id: int
    product_id: int
    order_date: str
    status: str

# Модели 
class User(Model):
    id = fields.IntField(pk=True)
    first_name = fields.CharField(max_length=255)
    last_name = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255)
    password = fields.CharField(max_length=255)

class Product(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField()
    price = fields.FloatField()

class Order(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='orders')
    product = fields.ForeignKeyField('models.Product', related_name='orders')
    order_date = fields.DatetimeField(auto_now_add=True)
    status = fields.CharField(max_length=255)

# Регистрация моделей
register_tortoise(
    app,
    db_url='sqlite://db.sqlite3',
    modules={'models': ['main']},
    generate_schemas=True,
    add_exception_handlers=True,
)

class UserUpdate(BaseModel):
    first_name: str = None
    last_name: str = None
    email: EmailStr = None
    password: str = None

class ProductUpdate(BaseModel):
    name: str = None
    description: str = None
    price: float = None

class OrderUpdate(BaseModel):
    user_id: int = None
    product_id: int = None
    status: str = None

# Роуты для CRUD операций
@app.post("/users/", response_model=UserPydantic)
async def create_user(user: UserCreate):
    user_obj = await User.create(**user.dict())
    return await UserPydantic.from_tortoise_orm(user_obj)

@app.get("/users/{user_id}", response_model=UserPydantic)
async def read_user(user_id: int):
    user = await User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await UserPydantic.from_tortoise_orm(user)

@app.post("/products/", response_model=ProductPydantic)
async def create_product(product: ProductCreate):
    product_obj = await Product.create(**product.dict())
    return await ProductPydantic.from_tortoise_orm(product_obj)

@app.get("/products/{product_id}", response_model=ProductPydantic)
async def read_product(product_id: int):
    product = await Product.get(id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return await ProductPydantic.from_tortoise_orm(product)

@app.post("/orders/", response_model=OrderPydantic)
async def create_order(order: OrderCreate):
    order_obj = await Order.create(**order.dict())
    return await OrderPydantic.from_tortoise_orm(order_obj)

@app.get("/orders/{order_id}", response_model=OrderPydantic)
async def read_order(order_id: int):
    order = await Order.get(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return await OrderPydantic.from_tortoise_orm(order)

@app.get("/users/", response_model=List[UserPydantic])
async def list_users():
    users = await User.all()
    return [await UserPydantic.from_tortoise_orm(user) for user in users]

@app.get("/products/", response_model=List[ProductPydantic])
async def list_products():
    products = await Product.all()
    return [await ProductPydantic.from_tortoise_orm(product) for product in products]

@app.get("/users/{user_id}/orders/", response_model=List[OrderPydantic])
async def list_user_orders(user_id: int):
    user = await User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    orders = await Order.filter(user=user)
    return [await OrderPydantic.from_tortoise_orm(order) for order in orders]

# Роут для подсчета общей суммы заказов пользователя
@app.get("/users/{user_id}/total-order-amount/", response_model=dict)
async def total_order_amount(user_id: int):
    user = await User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_amount = await Order.filter(user=user).aggregate(fields.Sum('product__price'))
    return {"total_amount": total_amount["product__price__sum"] or 0}

# Роут для сортировки и фильтрации товаров
@app.get("/products/sorted/", response_model=List[ProductPydantic])
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
        query = query.order_by(f"{sort_by} DESC" if sort_by and desc else f"{sort_by}")


    products = await query
    return [await ProductPydantic.from_tortoise_orm(product) for product in products]

@app.get("/orders/", response_model=List[OrderPydantic])
async def list_orders():
    orders = await Order.all()
    return [await OrderPydantic.from_tortoise_orm(order) for order in orders]
