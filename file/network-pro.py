import socket
import threading
import os
import struct
from colorama import *
from genericpath import isdir
import subprocess
import re
import platform
import socket
import traceback
import time
from tqdm import tqdm
from pathlib import Path
init(autoreset=True)
def get_ip_address():
    # Get the platform
    p = platform.system()

    # Get the output of the appropriate command based on the platform
    if p == "Windows":
        output = subprocess.check_output("ipconfig")
        ip_pattern = r"IPv4 Address\.+ : (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    else:
        output = subprocess.check_output("ifconfig")
        ip_pattern = r"inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"

    # Parse the output to extract the IP address
    match = re.search(ip_pattern, str(output))

    if match:
        return match.group(1)
    else:
        return None


BufferSize=1024


# server start code 

def handle_request(client_socket,client_address):
    # send welcome message
    # print(client_socket,client_address)
    # print("welcome to ftp")
    # time.sleep(.4)
    client_socket.sendall(b"220 Welcome to the FTP server\r\n")
    
    while True:
        # receive a command from the client
        command = client_socket.recv(1024).decode().strip()
        # print(f"Received command: {command}")

        if command.startswith("USER "):
            # TODO: check the username
            user_number=-1
            username = command.split(' ')[1]

            parent_dir = Path(__file__).resolve().parent.parent
            # Open the list.txt file using its relative path
            filePath = parent_dir / 'list.txt'

            
            with open(filePath, 'r') as f:
                nodes = f.read().splitlines()
                nodes=[line.split()[:4] for line in nodes]
                
                for i, node in enumerate(nodes):
                    if node[0]==client_address[0] and node[2]==username:
                        user_number=i
                        break

            if(user_number==-1):        
                client_socket.sendall(b"530 Login incorrect.\r\n")
                client_socket.close()
                # print(f"Closed connection from {client_address}")
                break
            else:
                client_socket.sendall(b"331 User name okay, need password.\r\n")
        elif command.startswith("PASS "):
            # TODO: check the password
            password = command.split(' ')[1]

            with open(filePath, 'r') as file:
                lines = file.readlines()
                line_n = lines[user_number-1]
                values = line_n.split()
                filePass = values[3]
            
            if password==filePass:
                client_socket.sendall(b"230 User logged in, proceed.\r\n")
            else:
                client_socket.sendall(b"530 Login incorrect.\r\n")
                client_socket.close()
                # print(f"Closed connection from {client_address}")
                break
            
        elif command.startswith("QUIT"):
            client_socket.sendall(b"221 Service closing control connection. Logged out if appropriate.\r\n")
            client_socket.close()
            # print(f"Closed connection from {client_address}")
            break
        elif command.startswith("PASV"):
            # enter passive mode and listen for data channel connections
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.bind((ip_address, 0))
            data_socket.listen(1)
            port = data_socket.getsockname()[1]
            # print(f"Listening on port {port}")
            ip_add2 =ip_address.replace(".", ",")
            
            client_socket.sendall(f"227 Entering Passive Mode ({ip_add2},{port//256},{port%256}) .\r\n".encode())
               
            data_client_socket, data_client_address = data_socket.accept()
            # print(f"Accepted data connection from {data_client_address}")
        elif command.startswith("LIST"):
            # send the list of files over the data channel
            
            # file_list = "\r\n".join(files)
            client_socket.sendall(b"150 Here comes the directory listing.\r\n")
        
            # send_file(data_client_socket, file_list)
            #sendall list
            parent_dir = Path(__file__).resolve().parent
           
            server_dir =parent_dir / "serverFiles"
            listing = os.listdir(server_dir)
            lenofListing=str(len(listing))                              
            data_client_socket.sendall(lenofListing.encode())
            time.sleep(.4)
            total_directory_size = 0
            for i in listing:
                
                data_client_socket.sendall(i.encode())
                time.sleep(.4)

                parent_dir = Path(__file__).resolve().parent
                server_dir = parent_dir / 'serverFiles'
                relativepath= server_dir / i

                total_directory_size += os.path.getsize(relativepath)
            


            data_client_socket.sendall(str(total_directory_size).encode())
            #list sent
            data_client_socket.close()
            data_socket.close()
            # print(f"Closed data connection from {data_client_address}")
            client_socket.sendall(b"226 Directory send OK.\r\n")
            
            # client_socket.recv(BufferSize)
            # print("Successfully sent file listing")


        elif command.startswith("RETR "):
           
            filename = command.split(' ')[1]

            parent_dir = Path(__file__).resolve().parent
            download_dir = parent_dir / 'serverFiles'
            file_path= download_dir / filename
           
            try:
                with open(file_path, 'rb') as file:
                    client_socket.sendall(b"150 Opening data connection.\r\n")

                    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    data_socket.bind((ip_address, 0))
                    data_socket.listen(1)
                    port = data_socket.getsockname()[1]
                    # print(f"Listening on port {port}")
                    ip_add2 =ip_address.replace(".", ",")
                    
                    client_socket.sendall(f"227 Entering Passive Mode ({ip_add2},{port//256},{port%256}) .\r\n".encode())
                    
                    data_client_socket, data_client_address = data_socket.accept()
                    # print(f"Accepted data connection from {data_client_address}")
                    
                    while True:
                        data = file.read(1024)
                        if not data:
                            break
                        data_client_socket.sendall(data)

                    client_socket.sendall(b'226 Transfer complete\r\n')
                    data_client_socket.close()
                    data_socket.close()

            except FileNotFoundError:
                client_socket.sendall(b'550 File not found\r\n')

        elif command.startswith("TYPE "):
            # set the data transfer mode
            client_socket.sendall(b"200 Type set to I.\r\n")
        
        else:
            client_socket.sendall(b"500 Command not recognized.\r\n")
            
    

# server end

def client_part():
    
    while True:
        time.sleep(2.5)
        p = platform.system()
        if p == "Windows":
            os.system('cls')
            pass
           
        else:
            os.system('clear')
          
        # read the list of network nodes from a file

        parent_dir = Path(__file__).resolve().parent.parent
        # Open the list.txt file using its relative path
        filePath = parent_dir / 'list.txt'

        with open(filePath, 'r') as f:
            nodes = f.read().splitlines()

        nodes=[line.split()[:2] for line in nodes]
        
        isListEmpty=True
        print(Fore.CYAN+"---------------------------------")
        for i, node in enumerate(nodes):
            if node[0]!=ip_address:
                isListEmpty=False
                print(f'{i+1}. ({node[0]} , {node[1]})')
        print("-1. Exit\n-2. Update the list")
        print(Fore.CYAN+"---------------------------------")
        if isListEmpty:
            print(Fore.RED+"It seems that no server is online.")
            node_index = int(input('Enter :'))
        # # prompt the user to select a node to connect to
        else:
            node_index = int(input('Enter node number to connect:'))
        if node_index==-1:
            break
        
        if node_index==-2:
            continue
        
        node_ip=nodes[node_index-1][0]
        node_port= nodes[node_index-1][1]
        server_address = (node_ip, int(node_port))
        

        # # create a TCP socket for control channel
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # # connect to the selected node on control channel
        try:
            client_socket.connect(server_address)
            print(Fore.GREEN+"You have successfully connected")
        except:
            print(Fore.RED+"It seems that the requested server is not online!")
            continue

        # receive welcome message
        print(Back.WHITE+Fore.CYAN+client_socket.recv(1024).decode())

        # send username and password
        clientName=input("Enter your user name:")

        client_socket.sendall(f"USER {clientName}\r\n".encode())
        response=client_socket.recv(1024).decode()
        print(Back.WHITE+Fore.CYAN+response)
        if response.startswith('530'):
            print(Fore.RED+"wrong username")
            client_socket.close()
            continue
        

        #check the server response 
        clientPass=input("Enter your password:")
        client_socket.sendall(f"PASS {clientPass}\r\n".encode())
        response=client_socket.recv(1024).decode()
        print(Back.WHITE+Fore.CYAN+response)

        if response.startswith('530'):
            print(Fore.RED+"wrong password.")
            client_socket.close()
            continue
        
        
        # enter passive mode
        client_socket.sendall(b"PASV\r\n")
        response = client_socket.recv(1024).decode()
        print(Back.WHITE+Fore.CYAN+response)


        parts = response.split("(")[1].split(")")[0].split(",")

        # Extract the IP address, low port, and high port
        ip_var = parts[0] + "." + parts[1] + "." + parts[2] + "." + parts[3]
        highport = int(parts[4])
        lowport = int(parts[5])

        port =  int(highport) * 256 + int(lowport)
        
        host = ip_var

        # connect to the data channel
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.connect((host, port))

        # request the list of files
        client_socket.sendall(b"LIST\r\n")
        response = client_socket.recv(1024).decode()
        print(Back.WHITE+Fore.CYAN+response)


        # receive the list of files
        number_of_files = data_socket.recv(1024).decode()
        print(Fore.YELLOW+"--------------------------")

        for i in range(int(number_of_files)):
           
            file_name = data_socket.recv(1024).decode()

            print(Fore.MAGENTA+Back.YELLOW+file_name)
            
                
            
        total_directory_size = data_socket.recv(1024).decode()
        print(f"Total directory size: {total_directory_size}")
        print(Fore.YELLOW+"--------------------------")
        #list received
        response = client_socket.recv(1024).decode()
        print(Back.WHITE+Fore.CYAN+response)
        data_socket.close()
       

        client_socket.sendall(b"TYPE I\r\n") # set binary mode
        response = client_socket.recv(1024).decode()
        print(Back.WHITE+Fore.CYAN+response)

        while True:
            # Get the filename from the user
            filename = input('Enter the filename:(-1 to connect to another node)')

            # Check if the user wants to quit
            if filename == '-1':
                client_socket.sendall(b'QUIT\r\n')
                response = client_socket.recv(1024).decode()
                print(Back.WHITE+Fore.CYAN+response)
                break

            # Send the RETR command to the server

            client_socket.sendall(f"RETR {filename}\r\n".encode())
            start_time = time.time()
            response = client_socket.recv(1024)
            print(Back.WHITE+Fore.CYAN+response.decode())
            # Check if the file was found
            if response.decode().startswith('550'):
                print(Fore.RED+'File not found !!!')
            else:
                response = client_socket.recv(1024).decode()
                    
                parts = response.split("(")[1].split(")")[0].split(",")

                # Extract the IP address, low port, and high port
                ip_var = parts[0] + "." + parts[1] + "." + parts[2] + "." + parts[3]
                highport = int(parts[4])
                lowport = int(parts[5])

                port =  int(highport) * 256 + int(lowport)
                # print(port)#
                host = ip_var

                # connect to the data channel
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                data_socket.connect((host, port))
                
                print(Fore.GREEN+"connected to data channel")
                

                parent_dir = Path(__file__).resolve().parent
                download_dir = parent_dir / 'downloadedFiles'
                file_path= download_dir / filename

                # Receive the data from the server and write it to a file
               
              


                with open(file_path, 'wb') as file:
                    while True:
                        data = data_socket.recv(1024)
                        if not data:
                            break
                        file.write(data)
                end_time = time.time()

                bar_format = '{desc}: {percentage:3.0f}%|{bar:10}{r_bar}'
                tqdm_kwargs = {'total': 100, 'desc': 'Progress', 'unit': '%', 'leave': True, 'bar_format': bar_format}
                time_diff = end_time - start_time

                for i in tqdm(range(100), **tqdm_kwargs):
                    time.sleep(time_diff / 100) 
                # Close the data socket
                data_socket.close()

                # Print a success message
                response = client_socket.recv(1024)
                print(Back.WHITE+Fore.CYAN+response.decode())

        client_socket.close()

    
     


def server_part():

    password = "1234"
    
    parent_dir = Path(__file__).resolve().parent.parent
        # Open the list.txt file using its relative path
    filePath = parent_dir / 'list.txt'
    with open(filePath, "r+") as f:
        lines = f.readlines()

        # Remove empty lines
        lines = [line for line in lines if line.strip() != ""]

        # Check if there's already a line with the same IP address
        found = False
        for i, line in enumerate(lines):
            if line.startswith(ip_address + " "):
                lines[i] = ip_address + " " + str(server_port) + " " + hostname + " " + password + "\n"
                found = True
                break

        # If not, add the new line to the end of the file
        if not found:
            lines.append(ip_address + " " + str(server_port) + " " + hostname + " " + password + "\n")

        # Write the updated lines back to the file
        f.seek(0)
        f.writelines(lines)
        f.truncate()



    try:

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((ip_address, server_port))#
            server_socket.listen(5)
           
            print(Back.WHITE+ Fore.MAGENTA + "Waiting for incoming connections...")
            
            while True:
                client_socket, client_address = server_socket.accept()
                
                try:

                    handle_client_thread = threading.Thread(target=handle_request, args=(client_socket, client_address))
                    handle_client_thread.start()
                
                except Exception as e:
                    print("An error occurred:", e)
                    print("Traceback:")
                    traceback.print_exc()

    except:
        print(Back.WHITE+ Fore.RED +"The server cannot be placed in listening mode")

 


def find_free_port():
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
    

def get_ipv4_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = None
    finally:
        s.close()
    return ip

hostname = socket.gethostname()
ip_address = get_ipv4_address()   
server_port= int(find_free_port())

if __name__ == '__main__':
    
    server_thread = threading.Thread(target=server_part)
    main_thread = threading.Thread(target=client_part)

    server_thread.start()
    main_thread.start()

    # wait for both threads to complete
    server_thread.join()
    main_thread.join()
   
    
    print("Both threads have completed their execution")


