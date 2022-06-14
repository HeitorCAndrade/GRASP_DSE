from ast import arguments, dump
from pickle import TRUE
from re import A
from setuptools import Require
from RandomSearch import RandomSearch
from greedy import Greedy
from heuristic import Heuristic
from hillClimbing0 import HillClimbing
from exhaustiveSearch import ExhaustiveSearch
from resourceGreedy import ResourceGreedy
import argparse
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
import pandas as pd
import pickle
if __name__ == "__main__":
    
    
    #Initialize parser
    parser = argparse.ArgumentParser()
 
    # Adding argument
    parser.add_argument("-c", "--cFiles", help = "C input files list", required=TRUE, nargs='+')
    parser.add_argument("-d", "--dFile", help = "Directives input file",required=TRUE)
    parser.add_argument("-p", "--prjFile", help = "Prj. top file",required=TRUE)

 
    # Read arguments from command line
    args = parser.parse_args()
    
    filesDict = {}
    filesDict['cFiles'] = args.cFiles
    filesDict['dFile'] = args.dFile
    filesDict['prjFile'] = args.prjFile
    

    
    heuristic = HillClimbing(filesDict,'directives.tcl')
    #heuristic = Greedy(filesDict,'directives.tcl')
    #heuristic = ExhaustiveSearch(filesDict,'directives.tcl')
    #heuristic = RandomSearch(filesDict,'directives.tcl')
    #heuristic = ResourceGreedy(filesDict,'directives.tcl')
    #heuristic.writeSolutionsDict()
    
    RESOURCE_TO_COMPARE = 'resources'
    ######################### GRAPH
    listLUT = []
    listLat = []
    
    for element in heuristic.solutions:
        resources = heuristic.solutions[element].resultados[RESOURCE_TO_COMPARE]#heuristic.solutions[element].resultados['resources']
        lat = heuristic.solutions[element].resultados['latency']
        listLUT.append(resources)
        listLat.append(lat)
    

    x_name = RESOURCE_TO_COMPARE
    y_name = 'Latency'
    df = pd.DataFrame(list(zip(listLUT, listLat)),
               columns =[x_name, y_name])
    x = df[x_name]
    y = df[y_name]
    
    
    fig, ax = plt.subplots(1)
    plt.plot(listLUT,listLat,'s',)
    plt.title('Spam-Filter')
    plt.xlabel(x_name)
    plt.ylabel(y_name)
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    # hText = 0.8
    # for solution in heuristic.solutions:
    #     plt.figtext(0.05, hText,solution, fontsize=9)
    #     plt.figtext(0.05 , hText-0.05, 'Latency:', fontsize=8)
    #     plt.figtext(0.15 , hText-0.05, listLat[solution-1], fontsize=8)
    #     plt.figtext(0.05 , hText-0.1, '#LUT:', fontsize=8)
    #     plt.figtext(0.15 , hText-0.1, listLUT[solution-1], fontsize=8)
    #     hText -= 0.15  


    plt.savefig('./Plot/plot.jpg')
    #file para plotar o resultado do computador remoto, caso queira interagir com o plot ao invés de ser só um jpg
    with open('./Plot/solutionsFile', 'wb') as solutionsFile:
        pickle.dump(heuristic, solutionsFile)
    solutionsFile.close()
    plt.show() 
   
