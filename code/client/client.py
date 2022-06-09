import queue
from threading import Thread
import socket
import os
import struct
# For structring & destructring
import pickle
import threading
import time
import pyaudio
import sys

# PORT
PORT = 5432
# Global variable running flag to kill the thread when user changes the menu action
running = False

# Structure for Client Information


class site_info():
    def __init__(self, type, size, name, desc_size, desc, radio_stn_count, radio_stn_list):
        self.type = type
        self.size = size
        self.name = name
        self.desc_size = desc_size
        self.desc = desc
        self.radio_stn_count = radio_stn_count
        self.radio_stn_list = radio_stn_list

# Structure for site information


class radio_stn_info():
    def __init__(self, num, size, name, multiCast_add, data_port, info_port, bit_rate):
        self.num = num
        self.size = size
        self.name = name
        self.multiCast = multiCast_add
        self.data_port = data_port
        self.info_port = info_port
        self.bit_rate = bit_rate

# structure for song information


class song_info():
    def __init__(self, type, size, name, remaining_time, next_song_size, next_song_name):
        self.type = type
        self.size = size
        self.name = name
        self.remaining_time = remaining_time
        self.next_song_size = next_song_size
        self.next_song_name = next_song_name


class connect_to_station(Thread):
    def __init__(self, args):
        Thread.__init__(self)
        self.args = args
        self.start()

    def run(self):
        MCAST_GRP = self.args.multiCast
        PORT = self.args.data_port

        server_address = ('', PORT)

        BUFF_SIZE = 65536
        # Multicast UDP socket creation
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        self.group = socket.inet_aton(MCAST_GRP)
        self.mreq = struct.pack('=4sl', self.group, socket.INADDR_ANY)
        self.socket.setsockopt(
            socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(server_address)

        p = pyaudio.PyAudio()
        # Chunk data
        Piece_size = 10*1024
        # Making stream object so that we can play audio in chunks
        stream = p.open(format=p.get_format_from_width(2),
                        channels=2,
                        rate=44100,
                        output=True,
                        frames_per_buffer=Piece_size)

        # Queue data structure is used to store the data and for streaming
        q = queue.Queue(10000)

        # Function Storing data into queue
        def getAudioData():
            while True:
                if(running == False):
                    self.socket.close()
                    return
                frame, _ = self.socket.recvfrom(BUFF_SIZE)
                q.put(frame)

        # Thread for each client
        t1 = threading.Thread(target=getAudioData, args=())
        t1.start()
        time.sleep(1)

        while True:
            if(running == False):
                self.socket.close()
                return

            frame = q.get()
            # Live streaming of audio files
            stream.write(frame)
            if(q.empty()):
                break
        self.socket.close()


class Client:
    def __init__(self):

        self.main()

    def connect_to_server(self):
        print('[Connecting to server...]')
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.target_ip = sys.argv[1]

        BUFSIZE = 1024
        self.s.connect((self.target_ip, PORT))
        recv = self.s.recv(BUFSIZE)
        self.site_info = pickle.loads(recv)
        print('THE NAME OF THE SITE IS', self.site_info.name)
        print('There are %d radio stations in the site' %
              self.site_info.radio_stn_count)
        print('The radio stations are:')
        for i in range(self.site_info.radio_stn_count):
            print('[%d] %s M_Group %s data on %s info on %s' % (self.site_info.radio_stn_list[i].num,
                  self.site_info.radio_stn_list[i].name, self.site_info.radio_stn_list[i].multiCast, self.site_info.radio_stn_list[i].data_port, self.site_info.radio_stn_list[i].info_port))
        self.s.close()

    def main(self):
        global running
        self.connect_to_server()

        receiverThread = None
        lastStationSelected = -1
        print('[Select a radio station]')
        pause = False
        # This main thread will be used to take input from user & perform the required actions
        while True:
            # The following is the menu and the user will be prompted to select the action/ stations
            if pause == True:
                user_input = input(
                    'Enter C to change station or R to resume: ')
            else:
                if running == False:
                    user_input = input()
                else:
                    user_input = input(
                        'Enter C to change station, P to pause, or X to quit: ')
            if pause == False and running == False:
                if user_input.isnumeric() and int(user_input) <= self.site_info.radio_stn_count and int(user_input) > 0:
                    running = True
                    lastStationSelected = int(user_input)
                    user_input = int(user_input)-1
                    print("Starting staion %s MGroup  %s data on %s info on %s  " % (self.site_info.radio_stn_list[user_input].name, self.site_info.radio_stn_list[
                          user_input].multiCast, self.site_info.radio_stn_list[user_input].data_port, self.site_info.radio_stn_list[user_input].info_port))
                    receiverThread = connect_to_station(
                        self.site_info.radio_stn_list[int(user_input)])

                else:
                    print("Invalid station input")

            else:
                if pause == True:
                    if user_input == 'C':
                        pause = False
                        running = False
                        receiverThread.join()
                        self.connect_to_server()
                    elif user_input == 'R':
                        pause = False
                        print("Resuming....")
                        running = True
                        receiverThread = connect_to_station(
                            self.site_info.radio_stn_list[lastStationSelected - 1])
                    else:
                        print("Invalid input")
                else:
                    if user_input == "P":
                        print("Pausing...")
                        running = False
                        receiverThread.join()
                        print("Paused")
                        pause = True
                    elif user_input == "C":
                        running = False
                        receiverThread.join()
                        self.connect_to_server()
                    elif user_input == "X":
                        running = False
                        receiverThread.join()
                        os._exit(1)

                    else:
                        print('Invalid command')


client = Client()
