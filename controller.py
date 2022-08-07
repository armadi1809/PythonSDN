import sys
import socket
from datetime import datetime
import time
import threading
socketControl = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
linkUpdate = 0
modifiedLinks = []


def widestPath(nodes, edges, sourceInd):

    path_lengths = {}
    for v in nodes: 
        if (nodes[v][1] == True):
            path_lengths[v] = -9999
        else:
            path_lengths[v] = 0
    path_lengths[sourceInd] = 9999


    adjacent_nodes = {v: {} for v in nodes}
    for(u,v), [w_uv,alive1, alive2] in edges.items():
        if alive1:
            adjacent_nodes[u][v] = w_uv
        if alive2:
            adjacent_nodes[v][u] = w_uv
    
    temporary_nodes = [v for v in nodes if nodes[v][1] == True]
    pred = [v for v in nodes]
    while len(temporary_nodes) > 0:
        upper_bounds = {v: path_lengths[v] for v in temporary_nodes}
        
        u = max(upper_bounds, key=upper_bounds.get)
   

        temporary_nodes.remove(u)

        for v, w_uv in adjacent_nodes[u].items():
            if (v in temporary_nodes):
                if (path_lengths[v] < min(path_lengths[u], w_uv)):
                    path_lengths[v] =  min(path_lengths[u], w_uv)
                # print(v,path_lengths[v], w_uv)
               
                    pred[v] = u
    nextHop = [v for v in nodes]
    
    for v in nodes:
        if(nodes[v][1] == True):
            i = v
            while (pred[i] != sourceInd) :
                i = pred[i]
            nextHop[v] = i
        else: 
            nextHop[v] = -1
    # print(nextHop)
    return (path_lengths, nextHop)    
def handle_sending():
    global edges,nodes,numNodes,neighbors,contFile
    global linkUpdate
    global modifiedLinks

    
    for v in nodes:
        nodes[v][0] = False
    while True:
        time.sleep(6)
      
        for v in nodes: 
            if nodes[v][0] == True and nodes[v][1] == True: 
                
                nodes[v][0] = False
            elif(nodes[v][0] == False and nodes[v][1] == True):
                
                with open("Controller.log", "a") as contFile:
                    contFile.write(str(datetime.now().time()) + "\n")
                    contFile.write("Switch Dead " + str(v) + "\n\n\n")
                nodes[v][1] = False
                for e in edges:
                    if(v in e):
                        edges[e][1] = False
                        edges[e][2] = False
                routingLog = ""
                for v in nodes: 
                    if nodes[v][1] == True:
                        path_length, pred = widestPath(nodes, edges,v)
                        for v2 in nodes: 

                            routingLog = routingLog + str(v) + "," + str(v2) + ":" + str(pred[v2]) + "," + str(path_length[v2])+"\n"
                        msg1 = str(v) + "\n"
                        for v2 in nodes:
                            msg1 = msg1 + str(v) + "," + str(v2) + ":" + str(pred[v2])+"\n"    
                        socketControl.sendto(msg1.encode("utf-8"), (addresses[v][0], addresses[v][1]))
                with open("Controller.log", "a") as contFile:
                    contFile.write(str(datetime.now().time()) + "\n")
                    contFile.write("Routing Update\n")
                    contFile.write(routingLog)
                    contFile.write("Routing Complete\n\n\n")
            
            elif(nodes[v][0] == True and nodes[v][1] == False):
           
                nodes[v][1] = True
                nodes[v][0] = False
                routingLog = ""
                for e in edges:
                    if(v in e):
                        edges[e][1] = True
                        edges[e][2] = True
                msg = str(len(neighbors[v])) + "\n"
                for neigh in neighbors[v]:
                    msg = msg + str(neigh) + " " + addresses[neigh][0] + " " + str(addresses[neigh][1]) + "\n"
                socketControl.sendto(msg.encode("utf-8"), (addresses[v][0], addresses[v][1]))
                for v2 in nodes: 
                    
                    if nodes[v2][1] == True:
                        path_length, pred = widestPath(nodes, edges,v2)
                        for v3 in nodes: 

                            routingLog = routingLog + str(v2) + "," + str(v3) + ":" + str(pred[v3]) + "," + str(path_length[v3])+"\n"
                        msg1 = str(v2) + "\n"
                        for v3 in nodes:
                            msg1 = msg1 + str(v2) + "," + str(v3) + ":" + str(pred[v3])+"\n" 
                        print("Here Sending route Update of an alive switch") 
                        socketControl.sendto(msg1.encode("utf-8"), (addresses[v2][0], addresses[v2][1]))
                with open("Controller.log", "a") as contFile:
                    contFile.write(str(datetime.now().time()) + "\n")
                    contFile.write("Routing Update\n")
                    contFile.write(routingLog)
                    contFile.write("Routing Complete\n\n\n")
        if (linkUpdate == 1 and len(modifiedLinks) > 0):
            routingLog = "" 
            for pair in modifiedLinks:
                with open("Controller.log", "a") as contFile:
                    contFile.write(str(datetime.now().time()) + "\n")
                    contFile.write("Link Dead " + str(pair[0]) + "," + str(pair[1]) + "\n\n\n")
                if edges[pair][1] == True:
                    edges[pair][1] = False
                    edges[pair][2] = False
                        
                else:
                    edges[pair][1] = True
                    edges[pair][2] = True
            for v in nodes: 
                if nodes[v][1] == True: 
                    path_length, pred = widestPath(nodes, edges,v)                           
                    msg1 = str(v) + "\n"
                    for v2 in nodes:
                        routingLog = routingLog + str(v) + "," + str(v2) + ":" + str(pred[v2]) + "," + str(path_length[v2])+"\n"
                        msg1 = msg1 + str(v) + "," + str(v2) + ":" + str(pred[v2])+"\n"   
                    socketControl.sendto(msg1.encode("utf-8"), (addresses[v][0], addresses[v][1]))
            with open("Controller.log", "a") as contFile:
                    contFile.write(str(datetime.now().time()) + "\n")
                    contFile.write("Routing Update\n")
                    contFile.write(routingLog)
                    contFile.write("Routing Complete\n\n\n")
            linkUpdate = 0
            
        

def handle_receiving():
    #wait to receive
    #check type of message
    #if a register request, act accordingly
    #if updates 
    global edges,nodes,numNodes,neighbors,contFile
    global linkUpdate
    global modifiedLinks
    timeUpdate = time.time()
    while True: 
        
        data,addr = socketControl.recvfrom(1024)
        data = data.decode("utf-8")
        timeElapsed = time.time()
        if(len(modifiedLinks) > 0):
            if(timeElapsed - timeUpdate > 20):
                modifiedLinks = []
    
        # if(data[0] == "2"):
        #     print(data)
        if(data):
            
            if("True" in data or "False" in data):
                
                nodes[int(data[0])][0] = True
                
                switch = int(data[0])
                data = data.split("\n")
            
                for i in range(1, len(data)-1):
                    
                    pair = (switch, int(data[i].split(",")[0]))
                    address = (addresses[pair[1]][0], addresses[pair[1]][1])
                   
                    
                  
                    if (pair[1] > pair[0] and str(edges[pair][1]) != data[i].split(",")[1] and nodes[pair[1]][1] == True and pair not in modifiedLinks):
                        linkUpdate = 1
                        modifiedLinks.append(pair)
                        timeUpdate = time.time()
                    elif(pair[1] < pair[0] and str(edges[(pair[1],pair[0])][2]) != data[i].split(",")[1] and nodes[pair[1]][1] == True and (pair[1],pair[0]) not in modifiedLinks):
                        linkUpdate = 1
                        modifiedLinks.append((pair[1], pair[0]))
                        timeUpdate = time.time()
            elif("Register request" in data):
               
                switch = int(data.replace("Register request ",""))
                if (nodes[switch][1] == False):
                    addresses[switch] = addr
                    with open("Controller.log", "a") as contFile:
                        contFile.write(str(datetime.now().time()) + "\n")
                        contFile.write("Switch Alive " + str(switch) + "\n\n\n")
                    nodes[switch][0] = True
                    
        
    
  

def parseFile():
    edges = {}
    
    filename = sys.argv[2]
    configur = open(filename, "r")
    numNodes = (int)(configur.readline())
    neighbors = [[] for v in range(numNodes)]
    nodes = {i: [True,True] for i in range(numNodes)}
    routes = configur.readlines()
    for line in routes:
        route = line.split()
        edges[((int) (route[0]), (int) (route[1]))] = [(int)(route[2]),True,True]
        neighbors[(int) (route[0])].append((int) (route[1]))
        neighbors[(int) (route[1])].append((int) (route[0]))
    return(edges, nodes,numNodes, neighbors)
   
def main():
    global edges,nodes,numNodes,neighbors,contFile 
    edges,nodes,numNodes,neighbors = parseFile()
    
    

    host = ""
    port = int(sys.argv[1])

    socketControl.bind((host, port))
    nodesConnected = 0
    global addresses
    with open("Controller.log","w") as contFile:
        contFile.write("")
        
    addresses = [v for v in nodes]
    while nodesConnected < numNodes:
        data, addr = socketControl.recvfrom(1024)
        
        if not data: 
            print("Unable to receive data")
            sys.exit()
        msg_request = data.decode("ascii")
        print(data.decode("ascii"))
        nodesConnected = nodesConnected + 1
        addresses[int(msg_request[-1])] = addr
        with open("Controller.log","a") as contFile:
            contFile.write(msg_request + "\n\n\n")
    with open("Controller.log", "a") as contFile:
        contFile.write(str(datetime.now().time()) + "\n")
    routingLog = ""
    for v in nodes: 
        path_length, pred = widestPath(nodes, edges,v)
        for v2 in nodes: 

            routingLog = routingLog + str(v) + "," + str(v2) + ":" + str(pred[v2]) + "," + str(path_length[v2])+"\n"
        msg1 = str(v) + "\n"
        msg = str(len(neighbors[v])) + "\n"
        for neigh in neighbors[v]:
            msg = msg + str(neigh) + " " + addresses[neigh][0] + " " + str(addresses[neigh][1]) + "\n"
        for v2 in nodes:
            msg1 = msg1 + str(v) + "," + str(v2) + ":" + str(pred[v2])+"\n"    
        

       
        socketControl.sendto(msg.encode("utf-8"), (addresses[v][0], addresses[v][1]))
        socketControl.sendto(msg1.encode("utf-8"), (addresses[v][0], addresses[v][1]))
        with open("Controller.log","a") as contFile:
            contFile.write("Register Response " + str(v) + "\n")
    with open("Controller.log", "a") as contFile:
            contFile.write("\n\n\n")
            contFile.write(str(datetime.now().time()) + "\n")
            contFile.write("Routing Update\n")
            contFile.write(routingLog)
            contFile.write("Routing Complete\n\n\n")
    sender = threading.Thread(target=handle_sending,args=())
    sender.start()
    receiver = threading.Thread(target=handle_receiving, args=())
    receiver.start()
    sender.join()
    receiver.join()

if __name__ == "__main__":       
    main() 

        


