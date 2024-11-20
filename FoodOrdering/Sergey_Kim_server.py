import socket
import xml.etree.ElementTree as ET
import struct
import threading
import select
import random
import json

#function to read from file containing the menu
def readFile(filename):
    try:
        with open(filename, 'r') as file: #open file
            read = file.readlines() #read lines
            item_prices = {} #initialize menu array
            for line in read: #get every line
                #strip every line off whitespaces and split into words
                chunks = line.strip().split()
                #check if each element in chunks contains 2 words
                if len(chunks) == 2:
                    #add to menu array
                    item_prices[chunks[0]] = int(chunks[1])
            return item_prices #return menu
    except FileNotFoundError: #file not found
        print("No file")
        return {}

item_prices = readFile("prices.txt") #read menu from file

def create(): #create identification number
    return random.randint(0, 2**32 - 1)

def parse_order(body): #parse the client input for menu item and their quantity
    root = ET.fromstring(body)

    order = []
    for item in root.findall('.//item'): #xml format extract
        item_name, item_quantity = item.text.split()
        item_quantity = int(item_quantity)
        order.append({"name": item_name, "quantity": item_quantity})
    return order

def getPrice(order): #get total price of the order
    total = 0.0
    for item in order:
        item_name = item["name"]
        item_quantity = item["quantity"]

        if item_name in item_prices: #for every item add its price to total
            priceElem = item_prices[item_name]
            total += item_quantity * priceElem

    return total

def getMessage(client_socket): #receive client message
    chunks = []

    chunk = client_socket.recv(4096)
    if chunk == b'':
        raise RuntimeError("No chunks detected")
    chunks.append(chunk)

    return b''.join(chunks)

def getBalance(cardNum, orderCost):
    #open cards.txt and match client inputted card to its balance
    try:
        with open('cards.txt', 'r') as file:
            read = file.readlines()
            cardBalance = {}
            for line in read:
                chunks = line.strip().split('=')
                if len(chunks) == 2:
                    card, balance_str = chunks[0].strip(), chunks[1].strip()
                    cardBalance[card] = float(balance_str)

            cardNum = cardNum.strip()

            if cardNum in cardBalance:
                balance = cardBalance[cardNum]
                if balance >= orderCost:
                    cardBalance[cardNum] -= orderCost
                    #open cards.txt and deduct order price from balance
                    with open('cards.txt', 'w') as file:
                        for card, newBalance in cardBalance.items():
                            file.write(f"{card} = {newBalance}\n")

                    return True
                else:
                    return False
            else: #no card found
                print("no card")
                return False
    except FileNotFoundError:
        print("No cards file")
        return False

def clientReq(client_socket): #handle client requests
    data = getMessage(client_socket) #get data
    print(f"{data}\n")
    if not data:
        print("Client disconnected.")
        return
    try:
        rtype = data[4]

        responseId = create()
        order_id = struct.unpack('!I', data[:4])[0] #unpack data to get orderid

        order = {}
        cardNum = ""

        if rtype == 2:
            orderMsg = parse_order(data[5:]) #parse and store items and quantities
            finalPrice = getPrice(orderMsg) #calculate price
            #pack order info into header
            header = struct.pack('!IIII', responseId, order_id, rtype, len(str(finalPrice)))
            #pack price into body
            body = str(finalPrice).encode('utf-8')

            client_socket.sendall(header + body) #send to client

            with open('orders.txt', 'a') as file: #open orders.txt and write the order into it
                file.write(f"Response ID: {responseId}, Order ID: {order_id}, Final Price: {finalPrice}\n")

        elif rtype == 1: #send the menu to client using json
            item_prices_str = json.dumps(item_prices)
            header = struct.pack('!IIII', responseId, order_id, rtype, len(item_prices_str))
            body = item_prices_str.encode('utf-8')

            client_socket.sendall(header + body)
        elif rtype == 3: #send payment info to client
            try:
                data_str = data[8:].decode('utf-8', 'ignore')
                string = json.loads(data_str)

                name = string.get('name', '')
                cardNum = string.get('cardNum', '')
                try: #try to open orders and read them
                    with open('orders.txt', 'r') as file:
                        read = file.readlines()
                        allPrices = {}
                        for line in read:
                            chunks = [chunk.strip() for chunk in line.split(',')]
                            for chunk in chunks:
                                key, value = chunk.split(':')
                                order[key.strip()] = value.strip()

                        if 'Order ID' in order and 'Final Price' in order:
                            order_id = int(order['Order ID'])
                            finalPrice = float(order['Final Price'])

                            if getBalance(cardNum, finalPrice):
                                #if card has enough balance, thank client for purchase
                                #then send client data
                                message = f"Thank you for your purchase, {name}!"
                                msgLen = len(message)
                                header = struct.pack('!IIII', responseId, order_id, 3, 200)
                                body = message.encode('utf-8')
                            else:
                                message = "Not enough funds."
                                msgLen = len(message)
                                header = struct.pack('!IIII', responseId, order_id, 3, 403)
                                body = message.encode('utf-8')

                            client_socket.sendall(header + struct.pack('!I', msgLen) + body)
                        else:
                            header = struct.pack('!IIII', responseId, order_id, 3, 404)
                            body = "Order not found.".encode('utf-8')
                            client_socket.sendall(header + struct.pack('!I', len(body)) + body)
                except FileNotFoundError:
                    print("No orders file")
                    return False

            except json.JSONDecodeError:
                print("Invalid JSON format for order type 3")

    except Exception as e:
        print(f"Error: {e}")
host = "localhost"
port = 8080

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind((host, port))
serversocket.listen()
serversocket.setblocking(False)

print(f"host = {host}, port = {port}")

lock = threading.Lock()
active = [serversocket]


try:
    while True:

        read, _, _ = select.select(active, [], [])

        for sock in read:
            if sock is serversocket:
                client, address = serversocket.accept()
                print(f"Connected to {client}")

                with lock:
                    active.append(client)

            else:
                print("Not server")
                threading.Thread(target=clientReq, args=(client,)).start()
                with lock:
                    active.remove(client)
except KeyboardInterrupt:
    serversocket.close()
