from .models import User, Order
from .logic import OrderProcessor

def run():
    u = User(id=1, name="Hank")
    o = Order(id=101, user_id=1, amount=99.9)
    p = OrderProcessor()
    p.process(u, o)

if __name__ == "__main__":
    run()
