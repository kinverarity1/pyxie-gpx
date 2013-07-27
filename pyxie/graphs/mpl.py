import matplotlib.pyplot as plt

def map(motion, ax):
    ax.plot(motion.x, motion.y)
    

def map_dataArr(dataArr, ax):
    ax.plot(dataArr[:,1], dataArr[:,2])