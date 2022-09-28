import os, sys
print(os.environ)
# Checking if the SUMO_HOME environment variable is set. If it is, it adds the tools folder to the
# path. If it is not, it exits the program.
if 'SUMO_HOME' in os.environ:
     tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
     sys.path.append(tools)
else:
     sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
import traci.constants as tc


PORT = 8813
traci.init(PORT)
traci.setOrder(2) # number can be anything as long as each client gets its own number
# Getting the list of edges in the network.
step = 0
edges = []
for e in list(traci.edge.getIDList()):
     if "E" in e :
          edges.append(e)
print(edges)

# Setting the maximum speed of all edges to 24 m/s.
for e in edges:
     traci.edge.setMaxSpeed(e,24)

def next_edge(edges, id):
     """
     It returns the next edge in the route of the vehicle with the given ID
     
     :param edges: a list of the edges in the network
     :param id: the id of the vehicle
     :return: The next edge in the list of edges.
     """
     e = traci.vehicle.getRoadID(str(id))
     i = edges.index(e)
     return edges[(i+1) % len(edges)]

fichier = open("Result60.txt", "a")
fichier.write("time\t time loss\t Speed \n")
fichier.close()

# A while loop that runs until the simulation is over.
while traci.simulation.getMinExpectedNumber() > 0:
   traci.simulationStep()
   step += 1
   liste = os.listdir("./vehicle")

# Writing the time, time loss and speed of the vehicle with id 0 to the file Result.txt.
   print(liste)
   fichier = open("Result60.txt", "a")
   try:
     fichier.write(str(step)+ "\t " + str(traci.vehicle.getTimeLoss("0")) + " \t" + str(traci.vehicle.getSpeed("0")) + "\n")
     print(traci.vehicle.getTimeLoss("0"))
   except:
     #continue
     pass

   fichier.close()

# Reading the files in the vehicle folder and if the file is not empty, it is changing the lane of the
# vehicle.
   for f in liste :
        if "car" in f:
             id = int((f.split(".txt")[0]).split("car")[1])-1
             #time = os.path.getmtime("./vehicle/"+f)
             fichier = open("./vehicle/"+f, "r")
             val = fichier.read()
             if val != "" and val[0] != ">":
               try:
# The above code is checking if the vehicle is in the right lane. If it is not, it will change lanes.
                    lane = traci.vehicle.getLaneIndex("0")
                    if traci.vehicle.getLaneIndex(str(id)) > lane:
                         if traci.vehicle.couldChangeLane(str(id),1):
                              traci.vehicle.changeLaneRelative(str(id),2,duration = 50) #if bad change to 50
                         else:
                              traci.vehicle.changeSublane(str(id),2)

# Checking if the vehicle is in the left lane. If it is not, it will change lanes.
                    elif traci.vehicle.getLaneIndex(str(id)) <= lane:
                         if traci.vehicle.couldChangeLane(str(id),-1):
                              traci.vehicle.changeLaneRelative(str(id),-2,duration = 50)
                         else:
                              traci.vehicle.changeSublane(str(id),-2)
                    print(next_edge(edges,id) + ' veh: ' + f)
               except:
                    continue
             #else:
             #fichier.close()
# Writing the time loss of the vehicle to the file.
             #if val == "":
             else:
               print("modif")
               try:
                    value = str(traci.vehicle.getTimeLoss(str(id)))
                    fichier = open("./vehicle/"+f, "w")
                    if value != "":
                         fichier.write( ">>\t" + value + "\t" + str(step))
               except:
                    continue
             fichier.close()
traci.close()



