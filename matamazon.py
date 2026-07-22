import sys
import json


class InvalidIdException(Exception):
    pass


class InvalidPriceException(Exception):
    pass

class InvalidQuantityException(Exception):
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
        return f"Customer(id={self.id}, name={repr(self.name)}, city={repr(self.city)}, address={repr(self.address)})"

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
        return f"Supplier(id={self.id}, name={repr(self.name)}, city={repr(self.city)}, address={repr(self.address)})"

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
        return f"Product(id={self.id}, name={repr(self.name)}, price={self.price}, supplier_id={self.supplier_id}, quantity={self.quantity})"

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
            raise InvalidIdException("The product does not exist in the system.")

        product = self.products[product_id]
        if quantity > product.quantity:
            raise InvalidQuantityException(
                "The quantity requested for this product is greater than the quantity in stock.")

        total_price = product.price * quantity
        new_order = Order(self.next_order_id, customer_id, product_id, quantity, total_price)

        self.orders[self.next_order_id] = new_order
        self.next_order_id += 1
        product.quantity -= quantity

        return "The order has been accepted in the system"

    def remove_object(self, _id, class_type):
        if not isinstance(_id, int) or _id < 0:
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

            products_to_delete = [p_id for p_id, p in self.products.items() if p.supplier_id == _id]
            for p_id in products_to_delete:
                del self.products[p_id]

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
        with open(path, "w") as out_file:
            for customer in self.customers.values():
                print(customer, file=out_file)
            for supplier in self.suppliers.values():
                print(supplier, file=out_file)
            for product in self.products.values():
                print(product, file=out_file)

    def export_orders(self, out_file):
        orders_by_city = {}
        for order in self.orders.values():
            product = self.products[order.product_id]
            supplier = self.suppliers[product.supplier_id]
            city = supplier.city
            if city not in orders_by_city:
                orders_by_city[city] = []
            orders_by_city[city].append(str(order))

        json.dump(orders_by_city, out_file)


def load_system_from_file(path):
    customers = []
    suppliers = []
    products = []

    with open(path, "r") as in_file:
        lines = in_file.readlines()

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        try:
            obj = eval(line)
        except (InvalidIdException, InvalidPriceException):
            raise
        except Exception:
            continue

        if isinstance(obj, Customer):
            customers.append(obj)
        elif isinstance(obj, Supplier):
            suppliers.append(obj)
        elif isinstance(obj, Product):
            products.append(obj)

    system = MatamazonSystem()

    for customer in customers:
        system.register_entity(customer, True)
    for supplier in suppliers:
        system.register_entity(supplier, False)
    for product in products:
        system.add_or_update_product(product)

    return system


USAGE_MESSAGE = "Usage: python3 matamazon.py -l <matamazon_log> -s <matamazon_system> -o <output_file> -os <out_matamazon_system>"
GENERAL_ERROR_MESSAGE = "The matamazon script has encountered an error"

VALID_FLAGS = ("-l", "-s", "-o", "-os")
REQUIRED_FLAGS = ("-l",)


def _tokenize(line):
    tokens = []
    current = ""
    for ch in line:
        if ch.isspace():
            if current != "":
                tokens.append(current)
                current = ""
        else:
            current += ch
    if current != "":
        tokens.append(current)
    return tokens


def _parse_cli_args(argv):
    args = {}
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag not in VALID_FLAGS or flag in args or i + 1 >= len(argv):
            return None
        args[flag] = argv[i + 1]
        i += 2

    for required in REQUIRED_FLAGS:
        if required not in args:
            return None
    return args


def _to_text(token):
    return token.replace("_", " ")


def _handle_register(system, tokens):
    entity_type = tokens[1].lower()
    entity_id = int(tokens[2])
    name = _to_text(tokens[3])
    city = _to_text(tokens[4])
    address = _to_text(tokens[5])
    if entity_type == "customer":
        system.register_entity(Customer(entity_id, name, city, address), True)
    elif entity_type == "supplier":
        system.register_entity(Supplier(entity_id, name, city, address), False)


def _handle_add_or_update(system, tokens):
    product_id = int(tokens[1])
    name = _to_text(tokens[2])
    price = float(tokens[3])
    supplier_id = int(tokens[4])
    quantity = int(tokens[5])
    system.add_or_update_product(Product(product_id, name, price, supplier_id, quantity))


def _handle_order(system, tokens):
    customer_id = int(tokens[1])
    product_id = int(tokens[2])
    if len(tokens) > 3:
        system.place_order(customer_id, product_id, int(tokens[3]))
    else:
        system.place_order(customer_id, product_id)


def _handle_remove(system, tokens):
    class_type = tokens[1]
    obj_id = int(tokens[2])
    system.remove_object(obj_id, class_type)


def _handle_search(system, tokens):
    query = _to_text(tokens[1])
    if len(tokens) > 2:
        results = system.search_products(query, float(tokens[2]))
    else:
        results = system.search_products(query)
    print(results)


def _process_log_file(system, log_path):
    with open(log_path, "r") as log_file:
        for raw_line in log_file:
            tokens = _tokenize(raw_line)
            if not tokens:
                continue
            command = tokens[0]

            if command == "register":
                _handle_register(system, tokens)
            elif command == "add" or command == "update":
                _handle_add_or_update(system, tokens)
            elif command == "order":
                _handle_order(system, tokens)
            elif command == "remove":
                _handle_remove(system, tokens)
            elif command == "search":
                _handle_search(system, tokens)


def main():
    args = _parse_cli_args(sys.argv[1:])
    if args is None:
        print(USAGE_MESSAGE, file=sys.stderr)
        exit(1)

    try:
        if "-s" in args:
            system = load_system_from_file(args["-s"])
        else:
            system = MatamazonSystem()

        _process_log_file(system, args["-l"])

        if "-o" in args:
            with open(args["-o"], "w") as out_file:
                system.export_orders(out_file)
        else:
            system.export_orders(sys.stdout)

        if "-os" in args:
            system.export_system_to_file(args["-os"])

    except Exception:
        print(GENERAL_ERROR_MESSAGE)
        exit(0)


if __name__ == "__main__":
    main()