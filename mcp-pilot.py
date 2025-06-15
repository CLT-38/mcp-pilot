import asyncio
import time
from bleak import BleakScanner, BleakClient
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

# Définir les UUID et la mac adresse ici
NORDIC_UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NORDIC_UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
TARGET_DEVICE_ADDRESS = "F4:12:FA:6E:CF:59" # Adresse MAC de votre Arduino


@mcp.tool
async def pilot_mecanum_wheels_arduino(movements: list[int], duration_sec: float = 0.0):
    """ Pilot the mecanum wheels through sending movement commands to the Arduino.
    You have the following commands available:
    - 0: Stop all motors
    - 1: Move diagonally backward to the left
    - 2: Move backward
    - 3: Move diagonally backward to the right
    - 5: Stop all motors (explicit stop command, same as 0 for stopping after duration)
    - 7: Move diagonally forward to the left
    - 8: Move forward
    - 9: Move diagonally forward to the right

    Args:
        movements (list[int]): A list of movement commands to send sequentially.
        duration_sec (float, optional): If greater than 0, each 'movement' in the list will be
                                        sent approximately 4 times per second for this duration.
                                        After each movement's duration, a stop command (0) will be sent
                                        before processing the next movement.
                                        If 0 or not specified, each command is sent once.
    """
    print(f"Recherche des appareils BLE...")
    devices = await BleakScanner.discover()

    if not devices:
        print("Aucun appareil BLE trouvé.")
        return "Aucun appareil BLE trouvé."
    
    selected_device = None
    for device in devices:
        if device.address == TARGET_DEVICE_ADDRESS:
            selected_device = device
            break
    
    if not selected_device:
        message = f"L'appareil Arduino avec l'adresse {TARGET_DEVICE_ADDRESS} n'a pas été trouvé."
        print(message)
        # Optionnel: lister les appareils trouvés si la cible n'est pas là
        print("Appareils trouvés à la place :")
        for i, dev in enumerate(devices):
            print(f"{i}: {dev.name} ({dev.address})")
        return message

    print(f"Connexion à {selected_device.name} ({selected_device.address})...")

    try:
        async with BleakClient(selected_device.address) as client:
            if not client.is_connected:
                message = "Échec de la connexion à l'Arduino."
                print(message)
                return message
            
            print("Connecté avec succès à l'Arduino !")

            nus_service = client.services.get_service(NORDIC_UART_SERVICE_UUID.lower())
            if not nus_service:
                message = f"Le service UART Nordic (UUID: {NORDIC_UART_SERVICE_UUID}) n'a pas été trouvé."
                print(message)
                return message

            rx_char = nus_service.get_characteristic(NORDIC_UART_RX_CHAR_UUID.lower())
            if not rx_char:
                message = f"La caractéristique RX (UUID: {NORDIC_UART_RX_CHAR_UUID}) n'a pas été trouvée."
                print(message)
                return message

            results = []
            for movement_idx, movement in enumerate(movements):
                print(f"Traitement du mouvement {movement_idx + 1}/{len(movements)}: commande {movement}")
                command_to_send = bytearray([movement])
                
                if duration_sec > 0:
                    print(f"Envoi de la commande {movement} pendant {duration_sec} secondes (4 envois/sec)...")
                    
                    if movement == 0 or movement == 5:
                        print(f"La commande actuelle est un arrêt ({movement}). Envoi unique.")
                        await client.write_gatt_char(rx_char.uuid, command_to_send, response=True)
                        await asyncio.sleep(0.1) 
                        results.append(f"Commande d'arrêt {movement} envoyée une fois à {selected_device.name}.")
                        if movement_idx < len(movements) - 1: # Petit délai avant le prochain mouvement
                            await asyncio.sleep(0.2)
                        continue # Passer au mouvement suivant

                    num_sends = int(duration_sec * 4)
                    if num_sends == 0 and duration_sec > 0: 
                        num_sends = 1
                    
                    interval = 1.0 / 4.0 

                    for i in range(num_sends):
                        if not client.is_connected:
                            results.append("Client déconnecté pendant l'exécution de la commande.")
                            return ", ".join(results)
                        
                        print(f"Envoi de la commande {movement} (envoi {i+1}/{num_sends})")
                        await client.write_gatt_char(rx_char.uuid, command_to_send, response=True)
                        if i < num_sends - 1: 
                            await asyncio.sleep(interval)
                    
                    await asyncio.sleep(0.1) 

                    stop_command_value = 0 
                    print(f"Fin de la durée pour le mouvement {movement}. Envoi de la commande d'arrêt ({stop_command_value}).")
                    stop_data = bytearray([stop_command_value])
                    await client.write_gatt_char(rx_char.uuid, stop_data, response=True)
                    print("Commande d'arrêt envoyée.")
                    results.append(f"Commande {movement} exécutée pendant approx. {duration_sec}s, puis arrêtée. Envoyée à {selected_device.name}.")
                    if movement_idx < len(movements) - 1: # Petit délai avant le prochain mouvement
                        await asyncio.sleep(0.2) 
                else:
                    # Comportement original: envoi unique par mouvement
                    print(f"Envoi de la commande de mouvement unique : {movement}")
                    await client.write_gatt_char(rx_char.uuid, command_to_send, response=True)
                    print("Commande envoyée.")
                    await asyncio.sleep(0.1) 
                    results.append(f"Commande {movement} envoyée avec succès à {selected_device.name}.")
                    if movement_idx < len(movements) - 1: # Petit délai avant le prochain mouvement
                        await asyncio.sleep(0.2)
            
            return ", ".join(results) if results else "Aucun mouvement n'a été traité."

    except Exception as e:
        error_message = f"Erreur lors de la communication BLE : {e}"
        print(error_message)
        return error_message
    finally:
        # La déconnexion est gérée par `async with BleakClient`
        print("Déconnexion (ou tentative) de l'Arduino.")


if __name__ == "__main__":
    # Exemples de test direct (en dehors de MCP)
    # Pour envoyer une commande unique (avancer)
    # asyncio.run(pilot_mecanum_wheels_arduino([8]))

    # Pour faire avancer pendant 3 secondes, puis reculer pendant 1 seconde
    async def main_test():
        result = await pilot_mecanum_wheels_arduino(movements=[8, 2], duration_sec=1.5)
        print(f"Résultat du test : {result}")
        
        result_single_no_duration = await pilot_mecanum_wheels_arduino(movements=[7,0,9], duration_sec=0)
        print(f"Résultat du test (commandes uniques sans durée) : {result_single_no_duration}")

        result_stop_with_duration = await pilot_mecanum_wheels_arduino(movements=[0], duration_sec=2.0)
        print(f"Résultat du test (arrêt avec durée) : {result_stop_with_duration}")
        
        result_sequence = await pilot_mecanum_wheels_arduino(movements=[8, 0, 2, 0, 7, 0, 9], duration_sec=0.5)
        print(f"Résultat du test (séquence avec arrêts) : {result_sequence}")


    # Décommentez la ligne suivante pour exécuter le test ci-dessus :
    # asyncio.run(main_test())
    
    # Pour lancer le serveur MCP
    mcp.run()
