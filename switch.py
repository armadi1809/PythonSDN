
import socket
import sys
import time
from datetime import datetime
import threading
import argparse


#Parse command line flags
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)      # For UDP
udp_host = sys.argv[2]
udp_port = sys.argv[3] 
neighbors = {}
filename = "switch" + sys.argv[1] + ".log"
parser = argparse.ArgumentParser()
parser.add_argument("switchID", type = int)
parser.add_argument("contHost", type = str)
parser.add_argument("contPort", type = str)
parser.add_argument("-f", "--failure", help = "Link Failure ID", required = False, default = "")
argument = parser.parse_args()

#Method to handle sending from the switch
def handle_sending():
    global udp_host, udp_port, neighbors,filename
    count = 0
    
    iD = int(sys.argv[1])
    while True:
        count += 1
        time.sleep(2)
        msg = (str(iD) + " KEEP_ALIVE").encode("utf-8")
        
        for v in neighbors :
            if(neighbors[v][3] == True and argument.failure != str(v)):
                sock.sendto(msg,(neighbors[v][0], int(neighbors[v][1])))
        topUpdate = str(iD) + "\n"
        for v in neighbors : 
            if(neighbors[v][3] == True and argument.failure!= str(v)):
                topUpdate = topUpdate + str(v) + ",True" + "\n"
            else:
                topUpdate = topUpdate + str(v) + ",False" + "\n"
     
        topUpdate = topUpdate.encode("utf-8")
        
        sock.sendto(topUpdate,(udp_host, udp_port))
        if count == 3:
            linkUpdate = 0
            topUpdate = str(iD) + "\n"
            for v in neighbors: 
                if(neighbors[v][2] == False and neighbors[v][3] == True):
                    linkUpdate = 1
                    with open(filename,"a") as logFile:
                        logFile.write(str(datetime.now().time())+ "\n")
                        logFile.write("Neighbor Dead " + str(v)+"\n\n\n")
                    topUpdate = topUpdate + str(v) +",False\n"
                    neighbors[v][3] = False
                elif(neighbors[v][2] == True and neighbors[v][3] == True):
                    neighbors[v][2] = False
                    topUpdate = topUpdate + str(v) +",True\n"
                elif(neighbors[v][2] == True and neighbors[v][3] == False):
                    linkUpdate = 1
                    topUpdate = topUpdate + str(v) +",True\n"
                    neighbors[v][3] = True
            if (linkUpdate == 1): 
                sock.sendto(topUpdate.encode("utf-8"),(udp_host, udp_port))
            
            count = 0

#Method responsible for handling received messages from other switches and controller. 
def handle_receiving():
    global udp_host, udp_port, neighbors,filename
    
    while True: 
        try:
            data, addr = sock.recvfrom(1024)
        except:
            print("Here in exception")
            continue 
        # print("Here After Exception")
        if data: 
            data = data.decode("ascii")
            if "KEEP_ALIVE" in data: 
           
                if (neighbors[int(data[0])][2] == False and neighbors[int(data[0])][3] == False and data[0] != argument.failure): 

                    #Neighbor is back alive
                    neighbors[int(data[0])][2] = True
                    neighbors[int(data[0])][0] = addr[0]
                    neighbors[int(data[0])][1] = str(addr[1])
                    with open(filename, "a") as logFile:
                        logFile.write(str(datetime.now().time())+ "\n")
                        logFile.write("Neighbor Alive " + data[0]+"\n\n\n")

                elif(neighbors[int(data[0])][2] == False and neighbors[int(data[0])][3] == True and data[0] != argument.failure):
                    neighbors[int(data[0])][2] = True
                    
            elif(data[0] == sys.argv[1]):
                with open(filename, "a") as logFile:
                    logFile.write(str(datetime.now().time())+"\n")
                    logFile.write("Routing Update\n")
                    logFile.write(data[2:])
                    logFile.write("Routing Complete\n\n\n")
            
def main():
    global udp_host, udp_port, neighbors,filename
    
    udp_host = sys.argv[2]		# Host IP
    udp_port = int(sys.argv[3])			        # specified port to connect   
    msg = ("Register request " + sys.argv[1]).encode("ascii")
    sock.sendto(msg,(udp_host,udp_port))
    with open(filename, "w") as logFile:
        logFile.write(str(datetime.now().time()) + "\n")
        logFile.write("Register Request Sent\n\n\n")
    data, addr = sock.recvfrom(1024)
    print("Data received")
    with open(filename,"a") as logFile:
        logFile.write(str(datetime.now().time()) + "\n")
        logFile.write("Register Response Received\n\n\n")
    data1, addr1 = sock.recvfrom(1024)
    data1 = data1.decode('utf-8')

    data = data.decode('utf-8')
    dataList = data.split('\n')

    neighbors = {}
    for i in range(1,len(dataList) - 1) :
                
        neighborAddress = dataList[i].split()
        neighbors[int(neighborAddress[0])] = []
        neighbors[int(neighborAddress[0])].append(neighborAddress[1])
        neighbors[int(neighborAddress[0])].append(neighborAddress[2])
        if argument.failure == neighborAddress[0]:
            neighbors[int(neighborAddress[0])].append(False)
            neighbors[int(neighborAddress[0])].append(True)
        else:
            neighbors[int(neighborAddress[0])].append(True)
            neighbors[int(neighborAddress[0])].append(True)
           
    with open(filename, "a") as logFile:
        logFile.write(str(datetime.now().time()) + "\n")
        logFile.write("Routing update\n")
        logFile.write(data1[2:])
        logFile.write("Routing complete\n\n\n")

    #Threads start
    sender = threading.Thread(target=handle_sending,args=())
    receiver = threading.Thread(target=handle_receiving, args=())
    sender.start()    
    receiver.start()
    sender.join()
    receiver.join()

if __name__ == "__main__":        
    main()