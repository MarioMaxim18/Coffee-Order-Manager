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

@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html", message="The requested resource was not found."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html", message="An internal error occurred. Please try again later."), 500

@app.route('/')
def home():
    try:
        all_orders = db.session.execute(db.select(Order).order_by(Order.id)).scalars().all()
        return render_template("index.html", orders=all_orders)
    except Exception as e:
        return render_template("500.html", message=f"Failed to load orders: {e}"), 500

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
        try:
            new_order = Order()
            for coffee in coffee_menu:
                try:
                    quantity = int(request.form.get(coffee["name"], 0))
                    if quantity > 0:
                        order_item = OrderItem(name=coffee["name"], price=coffee["price"], quantity=quantity, order=new_order)
                        db.session.add(order_item)
                except ValueError:
                    return render_template("500.html", message=f"Invalid quantity for {coffee['name']}"), 400

            db.session.commit()
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            return render_template("500.html", message=f"Failed to create an order: {e}"), 500

    return render_template("menu.html", coffee_menu=coffee_menu)

@app.route('/edit_order/<int:id>', methods=['GET', 'POST'])
def edit_order(id):
    try:
        order = db.get_or_404(Order, id)
    except Exception as e:
        return render_template("500.html", message=f"Order not found: {e}"), 404

    if request.method == 'POST':
        try:
            for item in order.order_items:
                quantity_field = f'quantity_{item.id}'
                new_quantity = int(request.form.get(quantity_field, item.quantity))
                if new_quantity < 0:
                    raise ValueError("Quantity cannot be negative.")
                item.quantity = new_quantity

            db.session.commit()
            return redirect(url_for('home'))
        except ValueError as ve:
            return render_template("500.html", message=f"Invalid input: {ve}"), 400
        except Exception as e:
            db.session.rollback()
            return render_template("500.html", message=f"Failed to update order: {e}"), 500

    return render_template("edit_order.html", order=order)

@app.route('/delete_order/<int:id>', methods=['POST'])
def delete_order(id):
    try:
        order = db.get_or_404(Order, id)
        db.session.delete(order)
        db.session.commit()
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()
        return render_template("500.html", message=f"Failed to delete the order: {e}"), 500

if __name__ == "__main__":
    app.run(debug=True)