import time

import socket
from ucollections import deque

s = socket.socket()
class LogServer:
    instance=None
    initialised = False
    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        if self.initialised == False:
            self.conn=""
            self.log_entries = deque([], 200)
            print("Initialising logging")
            addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setblocking(False)
            s.bind(addr)
            s.listen()
            self.initialised = True


    def connect(self):
        if  self.conn == "":
            try:
                self.conn, addr = s.accept()
                print('Got a connection from', addr)
                time.sleep(1)
                # Receive and parse the request
                request = self.conn.recv(1024)
                request = str(request)
                print('Request content = %s' % request)
                self.conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                self.conn.send("<head></head><body><h2>Kegscales Log</h2><p>")
                self.conn.send("<br/>".join(self.log_entries))

            except OSError as e:
                if(e.errno == 11):
                    print("No debug connected")
                else:
                    print('Connection error ' + str(e))



    def log(self, *loglines):
        logline = str(time.time()) +": " + "".join(str(l) for l in loglines)
        if self.conn!="":
             try:
                 self.conn.send("<br/>" + logline)
             except OSError as e:
                 self.conn.close()
                 self.conn=""
        self.log_entries.append(logline)
        print(logline)