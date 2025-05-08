from loops.inventorymanager import InventoryManager


class Product:
    def __init__(self, name, price, description):
        self.name = name
        self.price = price
        self.description = description


class Shop:
    def __init__(self):
        self.inventory_manager = InventoryManager()
        self.products = {
            "fruits": Product("fruits", 10, "Terveellinen välipala matkustajille"),
            "alcohol": Product("alcohol", 15, "Laadukkaita alkoholijuomia"),
            "snacks": Product("snacks", 8, "Pientä naposteltavaa matkalle"),
            "soda": Product("soda", 5, "Virvoitusjuomia koko perheelle"),
            "meals": Product("meals", 12, "Lämpimiä aterioita pitkille lennoille"),
            "water": Product("water", 3, "Puhdasta vettä"),
            "fuel": Product("fuel", 100, "Lentopolttoaine (10 litraa)")
        }

    def get_products_list(self):
        return [{"name": product.name, "price": product.price, "description": product.description}
                for product in self.products.values()]

    def purchase_product(self, player_id, selection, cash):
        """
        Ostaa tuotteen pelaajalle

        Args:
            player_id: Pelaajan ID
            selection: Valitun tuotteen nimi
            cash: Pelaajan käteinen

        Returns:
            (True/False, viesti, uusi käteismäärä)
        """
        selection = selection.lower()
        if selection not in self.products:
            return False, "Tuotetta ei löydy kaupasta.", cash

        product = self.products[selection]
        if cash < product.price:
            return False, "Ei tarpeeksi rahaa!", cash

        # Päivitä inventaario ja vähennä käteinen
        self.inventory_manager.update_inventory(player_id, selection, product.price)
        new_cash = cash - product.price

        return True, f"Ostit {selection}. Käteistä jäljellä: {new_cash}€", new_cash