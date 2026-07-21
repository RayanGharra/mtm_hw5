class InvalidIdException(Exception):
    pass


class InvalidPriceException(Exception):
    pass


class Customer:
    def __init__(self, id, name, city, address):
        if not isinstance(id, int) or id < 0:
            raise InvalidIdException("Invalid customer ID")
        self.id = id
        self.name = name
        self.city = city
        self.address = address

    def __str__(self):
        return f"Customer(id={self.id}, name='{self.name}', city='{self.city}', address='{self.address}')"

    def __repr__(self):
        return self.__str__()


class Supplier:
    def __init__(self, id, name, city, address):
        if not isinstance(id, int) or id < 0:
            raise InvalidIdException("Invalid supplier ID")
        self.id = id
        self.name = name
        self.city = city
        self.address = address

    def __str__(self):
        return f"Supplier(id={self.id}, name='{self.name}', city='{self.city}', address='{self.address}')"

    def __repr__(self):
        return self.__str__()


class Product:
    def __init__(self, id, name, price, supplier_id, quantity):
        if not isinstance(id, int) or id < 0:
            raise InvalidIdException("Invalid product ID")
        if not isinstance(supplier_id, int) or supplier_id < 0:
            raise InvalidIdException("Invalid supplier ID")
        if not isinstance(quantity, int) or quantity < 0:
            raise InvalidIdException("Invalid quantity")
        if not isinstance(price, (int, float)) or price < 0:
            raise InvalidPriceException("Invalid price")

        self.id = id
        self.name = name
        self.price = float(price)
        self.supplier_id = supplier_id
        self.quantity = quantity

    def __str__(self):
        return f"Product(id={self.id}, name='{self.name}', price={self.price}, supplier_id={self.supplier_id}, quantity={self.quantity})"

    def __lt__(self, other):
        return self.price < other.price

    def __repr__(self):
        return self.__str__()


class Order:
    def __init__(self, id, customer_id, product_id, quantity, total_price):
        if not isinstance(id, int) or id < 0:
            raise InvalidIdException("Invalid order ID")
        if not isinstance(customer_id, int) or customer_id < 0:
            raise InvalidIdException("Invalid customer ID")
        if not isinstance(product_id, int) or product_id < 0:
            raise InvalidIdException("Invalid product ID")
        if not isinstance(quantity, int) or quantity < 0:
            raise InvalidIdException("Invalid quantity")
        if not isinstance(total_price, (int, float)) or total_price < 0:
            raise InvalidPriceException("Invalid total price")

        self.id = id
        self.customer_id = customer_id
        self.product_id = product_id
        self.quantity = quantity
        self.total_price = float(total_price)

    def __str__(self):
        return f"Order(id={self.id}, customer_id={self.customer_id}, product_id={self.product_id}, quantity={self.quantity}, total_price={self.total_price})"

    def __repr__(self):
        return self.__str__()


class MatamazonSystem:
    """
    Main system class that stores and manages customers, suppliers, products and orders.

    The system must support:
        - Registering customers/suppliers (with unique IDs across both types).
        - Adding/updating products (must validate supplier existence).
        - Placing orders (validate product existence and stock).
        - Removing objects by ID and type (with dependency constraints).
        - Searching products by name/query and optional max price.
        - Exporting system state to a text file (customers/suppliers/products only).
        - Exporting orders to JSON grouped by supplier origin city.

    Notes:
        - The specification does not require specific internal fields. Any data structures are allowed,
          as long as the behaviors match the spec.
        - A parameterless constructor is required.
    """

    def __init__(self):
        self.customers = {}
        self.suppliers = {}
        self.products = {}
        self.orders = {}
        self.next_order_id = 1


    def register_entity(self, entity, is_customer):
        if is_customer:
            if entity.id in self.customers:
                raise InvalidIdException("Customer id already exists in the system.")
            self.customers[entity.id] = entity
        else:
            if entity.id in self.suppliers:
                raise InvalidIdException("Supplier id already exists in the system.")
            self.suppliers[entity.id] = entity

    def add_or_update_product(self, product):
        if product.supplier_id not in self.suppliers:
            raise InvalidIdException("Supplier id does not exist in the system.")

        if product.id in self.products:
            existing_product = self.products[product.id]

            if existing_product.supplier_id != product.supplier_id:
                raise InvalidIdException("Product already exists but belongs to a different supplier.")
            self.products[product.id] = product
        else:
            self.products[product.id] = product

    def place_order(self, customer_id, product_id, quantity=1):

        if customer_id not in self.customers:
            raise InvalidIdException("Customer id does not exist in the system.")

        if product_id not in self.products:
            return "The product does not exist in the system"

        product = self.products[product_id]

        if quantity > product.quantity:
            return "The quantity requested for this product is greater than the quantity in stock"

        total_price = product.price * quantity
        new_order = Order(self.next_order_id, customer_id, product_id, quantity, total_price)

        self.orders[self.next_order_id] = new_order
        self.next_order_id += 1
        product.quantity -= quantity

        return "The order has been accepted in the system"

    def remove_object(self, _id, class_type):
        if not isinstance(_id, int) or id < 0:
            raise InvalidIdException("id must be a non-negative integer.")

        clean_type = class_type.strip().lower()

        if clean_type == "order":
            if _id not in self.orders:
                raise InvalidIdException("Order id not found.")

            order = self.orders[_id]
            if order.product_id in self.products:
                self.products[order.product_id].quantity += order.quantity

            del self.orders[_id]
            return

        if clean_type == "customer":
            if _id not in self.customers:
                raise InvalidIdException("Customer id not found.")
            for order in self.orders.values():
                if order.customer_id == _id:
                    raise InvalidIdException("Cannot delete: Customer has an active order.")
            del self.customers[_id]

        elif clean_type == "product":
            if _id not in self.products:
                raise InvalidIdException("Product id not found.")
            for order in self.orders.values():
                if order.product_id == _id:
                    raise InvalidIdException("Cannot delete: Product is part of an active order.")
            del self.products[_id]

        elif clean_type == "supplier":
            if _id not in self.suppliers:
                raise InvalidIdException("Supplier id not found.")
            for order in self.orders.values():
                product = self.products.get(order.product_id)
                if product and product.supplier_id == _id:
                    raise InvalidIdException("Cannot delete: Supplier has a product in an active order.")
            del self.suppliers[_id]

        else:
            raise InvalidIdException("Invalid class type provided.")

    def search_products(self, query, max_price=None):
        matching_products = []
        for product in self.products.values():
            if product.quantity == 0:
                continue

            if query not in product.name:
                continue

            if max_price is not None and product.price > max_price:
                continue
            matching_products.append(product)

        return sorted(matching_products)

    def export_system_to_file(self, path):
        """
        Export system state (customers, suppliers, products) to a text file.

        Args:
            path (str): Output file path.

        Behavior:
            - Write each object on its own line, using the object's print/str representation.
            - Orders must NOT be included.
            - No constraint on the ordering of objects in the output.

        Raises:
            OSError (or any file-open exception): Must be propagated to the caller.
        """
        # TODO implement this method as instructed
        pass

    def export_orders(self, out_file):
        """
        Export orders in JSON format grouped by origin city.

        Args:
            out_file (file-like)

        Behavior (per specification):
            - Produce a JSON object where:
                - Keys: origin city (supplier city) for each order.
                - Values: list of strings representing orders (format as specified in section 4.1.4).
            - Order lists can be in any order.
            - No requirement on key ordering.

        Raises:
            Any exception during writing: Must be propagated to the caller.

        Notes:
            - The order origin city is the supplier city of the ordered product.
        """
        # TODO implement this method as instructed
        pass


def load_system_from_file(path):
    """
    Load a MatamazonSystem from an input file.

    Args:
        path (str): Path to a text file containing customers, suppliers and products.

    Returns:
        MatamazonSystem: Initialized system with the data found in the file.

    Behavior:
        - The file lines contain objects in the format produced by export_system_to_file (section 4.2).
        - Lines may appear in any order (e.g., product lines can appear before supplier lines).
        - Illegal lines may be ignored.
        - If an exception occurs during the creation of any required object due to invalid data,
          the function should stop and propagate the exception (as specified).

    Notes:
        - The assignment hints that eval() may be used.
    """
    # TODO implement this function as instructed
    pass

# TODO all the main part here