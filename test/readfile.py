# Reading the files in the vehicle folder and writing the content of each file in the vtime.txt file.
from cProfile import label
import os, sys
from turtle import color
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

dir = "./vehicle/"
file = os.listdir("./vehicle")
file.sort()
file.sort()

def plot(f):
    """
    It reads in a file, creates a dataframe, and plots the data
    
    :param f: the file name
    """
    data = pd.read_csv(f,sep='\s+')
    print(data.head())
    #print(data)
    #data = pd.DataFrame(data)

    #x = data[0]
    #y = data[1]
    print('*******creation du graph*******')
    pl = data.plot(x = 'time', y = 'Speed', title='Ambulance speed through time')
    pl.set_xlabel("Times (s) ")
    pl.set_ylabel("Speed (m/s) " )
    mean = data["Speed"].mean()
    plt.axhline(mean, color="red", linestyle = "dashed", label="Speed Average" )
    plt.legend()
    plt.show()

def read(file):
    """
    It reads the files in the vehicle directory and writes the content of each file in a new file called
    vtime.txt
    
    :param file: the name of the file to read
    """
    dir = "./vehicle/"
    print(file)

    for f in file:
        fichier = open(dir+f, "r")
        val = fichier.read()
        fichier.close

        fichier = open("vtime.txt","a")
        fichier.write(str(val)+"\n")
        fichier.close

#plot("graph.txt")
read(file)