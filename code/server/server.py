import math
import socket
import struct
import threading
import os
import time
# For structring & destructring
import pickle
import wave
import pyaudio
# There will be one thread per client
# There are total k stations and one thread per station doing multicast
numStations = 4
# PORT
PORT = 5432
# TTL
MULTICAST_TTL = 2

# Structure for site information


class site_info():
    def __init__(self, type, size, name, desc_size, desc, radio_stn_count, radio_stn_list):
        self.type = type
        self.size = size
        self.name = name
        self.desc_size = desc_size
        self.desc = desc
        self.radio_stn_count = radio_stn_count
        self.radio_stn_list = radio_stn_list

# Structure for radio station information


class radio_stn_info():
    def __init__(self, num, size, name, multiCast_add, data_port, info_port, bit_rate):
        self.num = num
        self.size = size
        self.name = name
        self.multiCast = multiCast_add
        self.data_port = data_port
        self.info_port = info_port
        self.bit_rate = bit_rate

# Structure for song information


class song_info():
    def __init__(self, type, size, name, remaining_time, next_song_size, next_song_name):
        self.type = type
        self.size = size
        self.name = name
        self.remaining_time = remaining_time
        self.next_song_size = next_song_size
        self.next_song_name = next_song_name


class Server:
    def __init__(self):
        stnList = []
        # Radio station list and its details
        for i in range(numStations):
            stn = radio_stn_info(
                i+1, 7, 'RED FM'+str(i+1), '224.1.1.'+str(i), PORT+((i+1)*10), PORT+((i+1)*10)+1, 44100)
            stnList.append(stn)
        # Site Information
        self.site = site_info(
            10, 2, 'FM', 14, "It's best site", numStations, stnList)

        # Starting all stations
        for i in range(numStations):
            threading.Thread(target=self.makeStation,
                             args=(i,)).start()
            time.sleep(1)

        # Socket creation
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.accept_connections()

    def accept_connections(self):

        ip = socket.gethostbyname(socket.gethostname())

        self.s.bind((ip, PORT))
        self.s.listen(100)

        print('Running on IP: '+ip)
        print('Running on port: '+str(PORT))

        while 1:
            c, addr = self.s.accept()
            print('one client connected having address: '+addr[0])
            # Multiple clients can connect by creating thread for each client
            threading.Thread(target=self.handle_client,
                             args=(c, addr,)).start()

    def handle_client(self, c, addr):
        site = self.site
        # Structuring data to send
        data_club = pickle.dumps(site)

        c.send(data_club)

        c.shutdown(socket.SHUT_RDWR)
        c.close()

    def makeStation(self, stationNum):
        # Fetching songs from folder
        path = os.path.abspath(os.getcwd())+'/station'+str(stationNum+1)+'/'

        dir_list = os.listdir(path)

        # Assigning Multicast grp dataport and info port information is taken from site
        MCAST_GRP = self.site.radio_stn_list[stationNum].multiCast
        data_port = self.site.radio_stn_list[stationNum].data_port
        info_port = self.site.radio_stn_list[stationNum].info_port

        # UDP Sockets for data multicasting
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.settimeout(0.2)
        ttl = struct.pack('b', 1)
        server_socket.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

        print('Started %s data on %s info on %s' %
              (MCAST_GRP, data_port, info_port))

        while(1):
            # Iterating through all station list
            for i in range(len(dir_list)):
                song_name = path+dir_list[i]
                next_song = dir_list[(i+1) % len(dir_list)]

                # Chunk data size
                Piece_size = 10*1024

                wavFr = wave.open(song_name)

                data = None

                Total_Pieces = math.ceil(wavFr.getnframes()/Piece_size)
                # Time left for the particular song (Following is the total time for the song))
                Time_left = Total_Pieces*Piece_size/44100
                songInfo = song_info(
                    12, len(dir_list[i]), dir_list[i], Time_left, len(next_song), next_song)
                running = False

                # sending song info
                def sendSongInfo():
                    while(True):
                        songInfo.Time_left = Time_left
                        data_club_song_info = pickle.dumps(songInfo)
                        server_socket.sendto(
                            data_club_song_info, (MCAST_GRP, info_port))
                        if running == False:
                            return
                        if(Time_left <= 0):
                            break
                        time.sleep(1)
                print('Station number %d SongName: %s' %
                      (stationNum+1, songInfo.name))

                # Starting new thread for sending port information
                tSong = threading.Thread(target=sendSongInfo, args=())
                running = True
                tSong.start()
                time.sleep(1)

                cnt = 0
                # Reading each frame and sending it to multicast group
                data = wavFr.readframes(Piece_size)
                while (data):
                    server_socket.sendto(data, (MCAST_GRP, data_port))
                    Time_left -= Piece_size/44100
                    time.sleep(0.001)
                    data = wavFr.readframes(Piece_size)
                    cnt += 1
                running = False
                # kill the thread
                tSong.join()
        server_socket.close()


server = Server()
