from .models import User
from .schemas import Order

class OrderProcessor:
    def process(self, user: User, order: Order):
        print(f"Processing order {order.id} for user {user.name}")
        return True
