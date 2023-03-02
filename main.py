from heuristics.impl.GRASP import GRASP
from heuristics.impl.RandomSearch import RandomSearch
from heuristics.impl.greedy import Greedy
from heuristics.heuristic import Heuristic
from heuristics.impl.hillClimbing0 import HillClimbing
from heuristics.impl.exhaustiveSearch import ExhaustiveSearch
from heuristics.impl.greedyWithEstimator import GreedyWithEstimator
from heuristics.impl.randomSearchWithEstimator import RandomSearchWithEstimator
from heuristics.impl.genetic import GA
import argparse
#import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from utils.graphs import Graphs
from utils.paretoComparer import ParetoComparer
from utils.plotMaker import PlotMaker
import pandas as pd
from predictor.estimators.randomforest.randomForest import RandomForestEstimator
from predictor.estimators.randomforest.randomForestFactory import RandomForestFactory
from predictor.preprocessing.preProcessor import PreProcessor
from sklearn.model_selection import train_test_split
from predictor.estimators.m5p.m5pEstimator import M5PrimeEstimator
from predictor.estimators.m5p.m5pFactory import M5PrimeFactory
from utils.estimatorTrainer import  RandomSamplesEstimatorTrainer
from utils.timeLapsedSolutionsSaver import TimeLapsedSolutionsSaver

import pickle 


if __name__ == "__main__": 
    
    
    #Initialize parser
    parser = argparse.ArgumentParser()
 
    # Adding argument
    parser.add_argument("-c", "--cFiles", help = "C input files list", required=True, nargs='+')
    parser.add_argument("-d", "--dFile", help = "Directives input file",required=True)
    parser.add_argument("-p", "--prjFile", help = "Prj. top file",required=True)
    parser.add_argument("-o", "--saveFile", help = "name of save file",required=True)
    parser.add_argument("-args", "--arguments", help = "arguments of heuristic",required=False, nargs='+')

 
    # Read arguments from command line
    args = parser.parse_args()
    
    filesDict = {}
    filesDict['cFiles'] = args.cFiles
    filesDict['dFile'] = args.dFile
    filesDict['prjFile'] = args.prjFile
    filesDict['saveFile'] = args.saveFile
    filesDict['arguments'] = args.arguments

    hour = 3600
    RESOURCE_TO_COMPARE = 'resources'
    factory = RandomForestFactory(filesDict["dFile"])   
    model = RandomForestEstimator(filesDict['dFile'])
    trainer = RandomSamplesEstimatorTrainer(filesDict,model,8*hour)
    try:
        with open(filesDict['arguments'][1], 'rb') as modelFile:
            loadModel = pickle.load(modelFile)
    except Exception as e:
        trainer.trainUntilErrorThreshold(0.8,4*hour)
        with open(filesDict['arguments'][1], 'wb') as modelFile:
            pickle.dump(model,modelFile)
    with open(filesDict['arguments'][1], 'rb') as modelFile:
        model = pickle.load(modelFile)
    '''
    if (-1 == int(filesDict['arguments'][0])):
        solutionsSaver = TimeLapsedSolutionsSaver(0.2*hour)
        heuristic1 = GA(filesDict,'./domain/directives.tcl',factory,timeLimit=2*hour,baseEstimator=model,trainTime=1*hour,solutionSaver=solutionsSaver) 
    else:
        solutionsSaver = TimeLapsedSolutionsSaver(0.2*hour)
        heuristic1 = GRASP(filesDict,'./domain/directives.tcl',model,timeLimit=2*hour,trainTime=1*hour,solutionSaver=solutionsSaver,RCLSynthesisInterval=int(filesDict['arguments'][0]))   
    #heuristic1 = GRASP(filesDict,'./domain/directives.tcl',model,timeLimit=2*hour,trainTime=1*hour,solutionSaver=solutionsSaver,RCLSynthesisInterval=int(filesDict['arguments'][0]),seed=0)   
    #file para plotar o resultado do computador remoto, caso queira interagir com o plot ao invés de ser só um jpg
    
    heuristic1.writeToFile(filesDict['saveFile'])
    '''
    '''

    
    #heuristic1 = GA(filesDict,'./domain/directives.tcl',factory,36000,saveInterval=1500)
    #heuristic1.writeToFile('./dse/aes_genetic10h')
    
    with open("./GRASP1_AES_2h_teste",'rb') as file:
        heuristic1 = pickle.load(file)
    with open("./GRASP1_DIGIT_2h_teste",'rb') as file:
        heuristic2 = pickle.load(file)
    
    print(heuristic1.solutions[len(heuristic1.solutions) - 1].results)
    print(heuristic2.solutions[0].results)
    
    comparer = ParetoComparer(RESOURCE_TO_COMPARE,'latency')
    #print(comparer.compare(heuristic1,heuristic2))
    #print(comparer.compare(heuristic2,heuristic1))
   
    plt = PlotMaker("gsm", RESOURCE_TO_COMPARE, 'latency')
    grasp1Digit  = Graphs.pathToListsOfSolutions("./saves/GRASP0_SPAM_30h/")
    geneticDigit  = Graphs.pathToListsOfSolutions("./saves/genetic_DIGIT_2h/")

    Graphs.plotADP(plt,grasp1Digit,'grasp1',720) #blue
    Graphs.plotADP(plt,geneticDigit,'genetic',720)
    #plt.createPlot(heuristic2.solutions) 
    plt.showPlot()
    '''
