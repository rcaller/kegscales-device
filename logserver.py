import time

import network
import socket
# Put wi-fi details here to enable web logging
ssid = ''
password = ''

s = socket.socket()
class LogServer:
    def __init__(self):
        self.conn=""
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        network.hostname("kegscales")
        wlan.connect(ssid, password)
        # Wait for Wi-Fi connection
        connection_timeout = 10
        while connection_timeout > 0:
            if wlan.status() >= 3:
                break
            connection_timeout -= 1
            print('Waiting for Wi-Fi connection...')
            time.sleep(1)

        # Check if connection is successful
        if wlan.status() != 3:
            raise RuntimeError('Failed to establish a network connection')
        else:
            print('Connection successful!')
            network.hostname("kegscales")
            network_info = wlan.ifconfig()
            print('IP address:', network_info[0])
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen()

    def connect(self):
        if self.conn == "":
            try:
                self.conn, addr = s.accept()
                print('Got a connection from', addr)

                # Receive and parse the request
                request = self.conn.recv(1024)
                request = str(request)
                print('Request content = %s' % request)
                self.conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                self.conn.send("<head></head><body><h1>Kegscales Log</h1><p>")


            except OSError as e:
                self.conn.close()
                print('Connection closed')
        print("Conn Attempt")


    def log(self, logline):
         if self.conn!="":
             try:
                 self.conn.send("<br/>" + logline)
             except OSError as e:
                 self.conn.close()
                 self.conn=""
         print(logline)