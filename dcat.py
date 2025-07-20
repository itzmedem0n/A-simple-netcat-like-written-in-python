#dcat.py
import sys
import subprocess
import getopt
import threading
import socket
from rich import print

address = ''
port = 0
listener = False
command = False
upload = ''
execute = ''

def help():
    print("""A SIMPLE TOOL SIMILAR TO NETCAT WRITTEN WITH PYTHON BY[red] YaCine[/red]           
  [yellow]Options:[/yellow]
  -l, --listen                Start the program in listener/server mode
  -e, --execute=<command>     Execute the specified command upon receiving a connection
  -c, --command               Initialize a command shell (interactive)
  -p, --port=<port>           Specify the port to connect to or listen on
  -a, --address=<address>     Specify the target IP address to connect to or bind (default 0.0.0.0 in server mode)
  -u, --upload=<destination>  Specify a destination path to save the uploaded file
  -h, --help                  Show this help menu

Examples:
  1. Send data to a server:
     echo "Hello" | python3 your_script.py -a 192.168.1.5 -p 5555

  2. Listen for incoming data on port 5555:
     python3 your_script.py -l -p 5555

  3. Upload a file to the server:
     python3 your_script.py -l -p 5555 -u /tmp/uploaded.txt

  4. Execute a command on client connection:
     python3 your_script.py -l -p 5555 -e "ls -la"

  5. Get an interactive shell on connection:
     python3 your_script.py -l -p 5555 -c

Note:
- Combine `--listen` with `--command` or `--execute` for server behavior.
- For client mode, omit `--listen` and provide `--address` and `--port`.""")
    sys.exit(1)

def main():
    global address, upload, port, listener, execute, command
    
    try:
        ops, args = getopt.getopt(sys.argv[1:], 'hcla:p:e:u:', ['help', 'listen', 'address=', 'port=', 'execute=', 'upload=', 'command'])
    except getopt.GetoptError as err:
        print(f"Error: {err}")
        help()
        
    for o, a in ops:
        if o in ('-h', '--help'):
            help()
        elif o in ('-a', '--address'):
            address = a
        elif o in ('-p', '--port'):
            port = int(a)
        elif o in ('-l', '--listen'):
            listener = True
        elif o in ('-e', '--execute'):
            execute = a
        elif o in ('-u', '--upload'):
            upload = a
        elif o in ('-c', '--command'):
            command = True
        else:
            print('INPUT IS INCORRECT')
            help()
    
    if not listener and len(address) and port > 0:
        buffer = ''
        client_sender(buffer)
    elif listener:
        server_loop()
    else:
        print("Error: Invalid configuration. Use -h for help.")
        help()

def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((address, port))
        if len(buffer):
            client.send(buffer.encode())
        
        while True:
            response = ''
            while True:
                data = client.recv(1024)
                if not data:
                    break 
                response += data.decode()
                if response.endswith('\n') or response.endswith('> '):
                    break
            
            if response:
                print(response, end='')
            
            try:
                buffer = input()
                buffer += '\n'
                client.send(buffer.encode())
            except EOFError:
                break
                
    except Exception as e:
        print("CONNECTION FAILED!", str(e))
    finally:
        client.close()

def server_loop():
    global address
    if not len(address):
        address = '0.0.0.0'
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((address, port))
    server.listen(3)
    print(f"[*] Listening on {address}:{port}")
    
    while True:
        client_socket, client_address = server.accept()
        print(f"[*] Accepted connection from {client_address[0]}:{client_address[1]}")
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

def client_handler(client_socket):
    global upload, execute, command
    
    if len(upload):
        upfile = b''
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            else:
                upfile += data
        try:
            with open(upload, 'wb') as file:
                file.write(upfile)  
            client_socket.send(b'File has been written successfully...\n')
        except Exception as e:
            client_socket.send(f"An error has occurred: {e}\n".encode())
    
    if len(execute):
        output = run_command(execute)
        client_socket.send(output)
    
    if command:
        while True:
            try:
                client_socket.send(b"Shell > ")
                cmd_buffer = b''
                while b'\n' not in cmd_buffer:
                    data = client_socket.recv(1024)
                    if not data:
                        return
                    cmd_buffer += data
                
                response = run_command(cmd_buffer.decode())
                client_socket.send(response)
            except:
                break
    
    client_socket.close()

def run_command(command):
    command = command.rstrip()
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        return output
    except Exception as e:
        return str(e).encode()


main()