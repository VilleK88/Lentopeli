import mysql.connector
from routes.config import db_config


class InventoryManager:
    def __init__(self):
        self.inventory = {}

    def set_inventory(self, inventory_data):
        self.inventory = inventory_data

    def get_inventory(self):
        """Retrieves the player's inventory from the database"""
        try:
            # Get the currently logged in user
            from loops import user
            player_id = user.user_id

            if not player_id:
                print("Error: No logged in user found")
                return {}

            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)  # Return results as dictionary

            # Get all inventory columns
            cursor.execute("""
                SELECT cash, current_fuel, fruits, alcohol, snacks, soda, meals, water
                FROM inventory 
                WHERE inventory_id = %s
            """, (player_id,))

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                self.inventory = result
                return result
            else:
                print(f"No inventory found for player ID: {player_id}")
                return {}

        except Exception as e:
            print(f"Error retrieving inventory: {e}")
            return {}

    def update_inventory(self, player_id, item, price=0):
        """Updates player inventory when purchasing an item"""
        db_item = "current_fuel" if item == "fuel" else item

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            if item == "fuel":
                # Calculate fuel units (1 fuel unit costs 10 euros)
                fuel_units = price / 10
                cursor.execute("UPDATE inventory SET current_fuel = current_fuel + %s WHERE inventory_id = %s",
                               (fuel_units, player_id))
            else:
                cursor.execute(f"UPDATE inventory SET {db_item} = {db_item} + 1 WHERE inventory_id = %s",
                               (player_id,))

            # Reduce cash
            cursor.execute("UPDATE inventory SET cash = cash - %s WHERE inventory_id = %s",
                           (price, player_id))

            conn.commit()
            cursor.close()
            conn.close()

            # Update our cached inventory
            self.get_inventory()
            return True
        except Exception as e:
            print(f"Error updating inventory: {e}")
            return False

    def use_item(self, player_id, item, customer_manager=None):
        """Use an item from inventory, potentially affecting customer mood"""
        db_item = "current_fuel" if item == "fuel" else item

        valid_items = ["fruits", "alcohol", "snacks", "soda", "meals", "water", "current_fuel"]
        if db_item not in valid_items:
            print(f"Invalid item name: {item}")
            return False

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # Check if item exists in inventory
            cursor.execute(f"SELECT {db_item} FROM inventory WHERE inventory_id = %s", (player_id,))
            current_quantity = cursor.fetchone()

            if current_quantity and current_quantity[0] > 0:
                # Use item (reduce quantity by 1)
                cursor.execute(f"UPDATE inventory SET {db_item} = {db_item} - 1 WHERE inventory_id = %s",
                               (player_id,))
                conn.commit()
                print(f"Used item: {item}")

                # Update customer mood if customer_manager is provided
                if customer_manager:
                    customer_manager.adjust_mood_based_on_product(item)

                success = True
            else:
                print(f"Not enough in inventory: {item}")
                success = False

            cursor.close()
            conn.close()

            # Update our cached inventory
            self.get_inventory()
            return success

        except Exception as e:
            print(f"Error using item: {e}")
            return False