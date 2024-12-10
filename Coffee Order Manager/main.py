from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float

app = Flask(__name__)

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///orders.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Order(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("order.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="order_items")

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    all_orders = db.session.execute(db.select(Order).order_by(Order.id)).scalars().all()
    return render_template("index.html", orders=all_orders)

@app.route('/menu', methods=['GET', 'POST'])
def menu():
    coffee_menu = [
        {"name": "Caffe Latte", "price": 2.5},
        {"name": "Cafe Mocha", "price": 5.0},
        {"name": "Caramel Macchiato", "price": 4.5},
        {"name": "Cafe Americano", "price": 3.0},
        {"name": "Cappuccino", "price": 3.5},
        {"name": "Double Espresso", "price": 3.0},
        {"name": "Espresso", "price": 2.0},
    ]

    if request.method == "POST":
        # Create a new order
        new_order = Order()

        # Add items to the order
        for coffee in coffee_menu:
            quantity = int(request.form.get(coffee["name"], 0))
            if quantity > 0:
                order_item = OrderItem(name=coffee["name"], price=coffee["price"], quantity=quantity, order=new_order)
                db.session.add(order_item)

        db.session.commit()
        return redirect(url_for('home'))

    return render_template("menu.html", coffee_menu=coffee_menu)

@app.route('/edit_order/<int:id>', methods=['GET', 'POST'])
def edit_order(id):
    order = db.get_or_404(Order, id)

    if request.method == 'POST':
        for item in order.order_items:
            quantity_field = f'quantity_{item.id}'
            new_quantity = int(request.form.get(quantity_field, item.quantity))
            item.quantity = new_quantity

        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit_order.html", order=order)

if __name__ == "__main__":
    app.run(debug=True)

    #TODO Add a Delete Option in the edit_order.html template
    #TODO Exception Handling