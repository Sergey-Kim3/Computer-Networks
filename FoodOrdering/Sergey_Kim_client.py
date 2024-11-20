import socket
import random
import sys
import struct
import json

def create(): #function to create a random identification number
    return random.randint(0, 2**32 - 1)

def getMessage(client_socket): #functino to "receive" data from the server
    chunks = [] #array to store the final message received

    chunk = client_socket.recv(4096) #one chunk of the message
    if chunk == b'': #runtime error if chunk is empty
        raise RuntimeError("No chunks detected")
    chunks.append(chunk)

    return b''.join(chunks) #fill the array with the entire message



def send_recv_req(body, host, port, rtype):
    #function to send the message to the server and receive data from the server
    id = create();
    header = id.to_bytes(4, byteorder = 'big') + bytes([rtype])
    #convert the id and request type to bytes and fill in the header

    if rtype == 1: #body is empty if MENU
        body = ""
    elif rtype == 2: #accept input from user if ORDR
        print("Enter the order in XML format:")
        print("<body>")
        print("  <item>Shashlyk 2</item>")
        print("  <item>Ramen 3</item>")
        print("  <item>Pizza 1</item>")
        print("</body>")
        sys.stdout.flush()
        body = input("Enter your order:\n") #fill in the body
    elif rtype == 3: #accept inputs to fill in the header and body
        orderNum = input("Enter your order id: ")
        name = input("Enter your name: ")
        address = input("Enter your address: ")
        cardNum = input("Enter your card number: ")

        #pack the header to send it later
        header += struct.pack('!I', int(orderNum))
        #pack the body to send it later
        body = json.dumps({"name": name, "address": address, "cardNum": cardNum})


    send = header + body.encode('utf-8') #compile send message

    #establish connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host, port))
        client.sendall(send) #send data to server
        #calculate header length
        headerLen = struct.calcsize('!IIII')

        #if ORDR, receive data from server
        if rtype == 2:
            try:
                #timeout in order not to get stuck waiting if no data
                client.settimeout(1)
                #receive header using calculated length above
                response_header = client.recv(headerLen)
                #receive all the relevant details of the order and extract them
                respId, orderId, respType, finPrice = struct.unpack('!IIII', response_header)
                #finPrice is length, hence we use it to get the actual finalPrice
                responseBody = client.recv(finPrice)
                if not responseBody:
                    return

                print(f"\nResponse ID: {respId}")
                print(f"Order ID: {orderId}")
                print(f"Response Type: {respType}")
                print(f"Order Price: {responseBody.decode('utf-8')}")
            except socket.timeout: #if timeout then print no response
                print("No response")
            finally: #reset timeout
                client.settimeout(None)
        elif rtype == 1: #if MENU then receive data
            try:
                client.settimeout(1)
                #get data from the server (client receives data from server, hence we use it)
                data = getMessage(client)
                #extract header from data using headerlen
                header = data[:headerLen]
                #extract body from data using headerlen to pinpoint body
                body = data[headerLen:]

                #extract menu details
                respId, orderId, respType, len = struct.unpack('!IIII', header)
                #decode item prices received
                item_prices_str = body.decode('utf-8')

                #load item_prices in json format
                item_prices = json.loads(item_prices_str)

                print(f"\nResponse ID: {respId}")
                print(f"Order ID: {orderId}")
                print(f"Response Type: {respType}")
                print(f"Item Prices: ")

                #output the menu
                for item, price in item_prices.items():
                    print(f"{item}: {price}")

            except socket.timeout:
                print("No response")
            finally:
                client.settimeout(None)
        elif rtype == 3: #receive payment data from server in case of PAYM
            try:
                client.settimeout(1)
                header = client.recv(headerLen)

                if not header:
                    print("No connection")
                    return

                #different name for body of the message to avoid confusion
                #receive body using first four bytes for length
                bodyStr = client.recv(struct.unpack('!I', client.recv(4))[0])
                #receive and output data
                respId, order_id, rtype, success = struct.unpack('!IIII', header)

                print(f"Response ID: {respId}")
                print(f"Order ID: {order_id}")
                print(f"Request Type: {rtype}")
                print(f"Success Code: {success}")
                print(f"{bodyStr.decode('utf-8')}")
            except socket.timeout:
                print("No response")
            finally:
                client.settimeout(None)

#definte host, port and intiialize request type
host = "localhost"
port = 8080
req_type = None

#do not terminate until user says so
while True:
    #ask for request type
    while req_type not in ['1', '2', '3']:
        req_type = input("Enter the request type!\n1 - MENU\n2 - ORDER\n3 - PAYMENT\n")
    #cast request to integer
    req_type = int(req_type)
    #send and receive data
    send_recv_req("", host, port, req_type)
    #ask if user wants to continue
    exit = input("\nDo you want to continue? (y/n)\n")
    #terminate client if client types anything other than y
    if exit != 'y':
        break
