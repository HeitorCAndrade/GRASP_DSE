import argparse
import time
from heuristics.impl.RandomSearch import RandomSearch
from predictor.estimators.estimator import Estimator
from heuristics.heuristic import Heuristic
from predictor.estimators.randomforest.randomForest import RandomForestEstimator
from domain.solution import Solution
from utils.Script_tcl import generateScript
import copy
import random



class GRASP(Heuristic):
    
    
    def __init__(self,filesDict,outPath,model:Estimator,timeLimit=43200,trainTime = 7200, saveInterval = None,seed=0, RCLSynthesisInterval=0):
        super().__init__(filesDict, outPath)
        self.TRAIN_TIME = trainTime #3
        self._SECONDS = timeLimit
        self.alpha = 0.7
        self.start = time.time()
        sample = RandomSearch(filesDict, outPath,self.TRAIN_TIME,saveInterval=saveInterval,saveName="GRASP")
        self.estimator = model
        try:
            self.estimator.trainModel(sample.solutions)
        except Exception as error:
            print(error)
        for solution in sample.solutions.values():
            self.saveSolution(solution)
        random.seed(seed)        
        self.saveInterval = saveInterval#every 'saveInterval' time, save solutions in a file
        if RCLSynthesisInterval==0:
            self.RCLSynthesisInterval = float('inf')
        else:
            self.RCLSynthesisInterval = RCLSynthesisInterval
        
        
        self.createSolutionsDict()
       
    
    def createSolutionsDict(self,iterations=10):
        """
        procedure GRASP(Max Iterations,Seed)
            1 Read Input();
            2 for k = 1,...,Max Iterations do
                3 Solution ← Greedy Randomized Construction(Seed);
                4 if Solution is not feasible then
                    5 Solution ← Repair(Solution);
                6 end;
                8 Update Solution(Solution,Best Solution);
            9 end;
            10 return Best Solution;
        end GRASP.

        """
        numSaves = 0 # number of times that all solutions were saved
        generateScript(self.cFiles, self.prjFile)
        end = time.time()
        #for i in range(iterations):
        while end-self.start <= self._SECONDS:
            solution = self.constructGreedyRandomizedSolution()
            #save all current solutions 
            if self.saveInterval:
                if (time.time() - self.start)/self.saveInterval >= numSaves + 1:
                    self.writeToFile(f'./time_stamps/timeStampGRASP{numSaves}')
                    numSaves+=1
            #repair solution?
            solution = self.localSearch(solution)
            end = time.time()

    def makeRCL(self,directiveGroup:str,solutionToBuild:dict,dictDir:dict):
        """
        Enters in RCL if candidate resource X latency is below
        (1+alpha)*min(resourceXlatency of all canidates)
        """
        RCL = []
        candidates = [] 
        bestResourcesXLatency = float('inf')
        #take all candidates
        for directive in dictDir[directiveGroup]:
            solutionToBuild[directiveGroup] = directive
            candidate = Solution(solutionToBuild,self.cFiles,self.prjFile)
            estimatedResults = self.estimator.estimateSynthesis(candidate)
            candidate.setresults(estimatedResults)
            candidates.append(candidate)
            resourcesXlatency=  candidate.results['resources'] * candidate.results['latency']
            if  resourcesXlatency < bestResourcesXLatency:
                bestResourcesXLatency = resourcesXlatency
        
        #create RCL from some or all candidates
        #RCL = {v E Vk | dv < (1 + alpha)*min(resourcesXlatency)}
        #v = candidate, Vk = candidates, dv = resourcesXlatency of candidate
        for candidate in candidates:
            resourcesXlatency=  candidate.results['resources'] * candidate.results['latency']
            if  resourcesXlatency < (1+self.alpha)*bestResourcesXLatency:
                #append only the directive string
                RCL.append(candidate.directives[directiveGroup])
        return RCL

    
    def constructGreedyRandomizedSolution(self):
        """
        procedure Greedy Randomized Construction(Seed)
            1 Solution ← /0;
            2 Initialize the set of candidate elements;
            3 Evaluate the incremental costs of the candidate elements;
            4 while there exists at least one candidate element do
                5 Build the restricted candidate list (RCL);
                6 Select an element s from the RCL at random;
                7 Solution ← Solution ∪ {s};
                8 Update the set of candidate elements;
                9 Reevaluate the incremental costs;
            10 end;
            11 return Solution;
        end Greedy Randomized Construction.
        """
        solutionToBuild = dict.fromkeys(self.dictDir,'') #Cria um dicionário 'diretivas' a partir do 'dictDir' mas 
                                                        #mantendo apenas os títulos das diretivas - seu valores são
                                                        #trocados por None
        directiveGroups = list(self.dictDir.keys()) 
        dictDirCopy = copy.deepcopy(self.dictDir)
        random.shuffle(directiveGroups)
        for count,directiveGroup in enumerate(directiveGroups):
            RCL = self.makeRCL(directiveGroup,solutionToBuild,dictDirCopy)
            s = random.choice(RCL)
            solutionToBuild[directiveGroup] = s
            if ((count+1) % self.RCLSynthesisInterval == 0): #count+1 just to not include 0 on the count
                #synthesis of current solution under construction and feed solution to model
                constructedSolution = Solution(solutionToBuild,self.cFiles,self.prjFile)
                try:
                    synthesisTimeLimit = self._SECONDS - (time.time() - self.start) 
                    self.synthesisWrapper(constructedSolution,synthesisTimeLimit)
                    self.estimator.trainModel(constructedSolution)
                except Exception as error:
                    print(error)
 

            self.__removeRedundantDirectives(dictDirCopy,directiveGroup,s)
        #basically, if last iteration of the loop above didnt got synthesized then synthesize, else dont synthesize
        if not ((count+1) % self.RCLSynthesisInterval == 0):
            constructedSolution = Solution(solutionToBuild,self.cFiles,self.prjFile)
            try:
                synthesisTimeLimit = self._SECONDS - (time.time() - self.start) 
                self.synthesisWrapper(constructedSolution,synthesisTimeLimit)
                self.estimator.trainModel(constructedSolution)
            except Exception as error:
                print(error)

        return constructedSolution

    def __removeRedundantDirectives(self,dictDir:dict,directiveGroup,directive):
        solution = dict.fromkeys(self.dictDir,'')
        solution[directiveGroup] = directive
        for group in dictDir.keys():
            if group is not directiveGroup:
                for dir in dictDir[group]:
                    solution[group] = dir
                    if self.isRedundantDesign(solution):
                        dictDir[group].remove(dir)
                    solution[group] = ''
 
        return dictDir


    def localSearch(self,solution:Solution):
        neighbors = [] #in resources x latency
        
        for directiveGroup in self.dictDir.keys():
            neighborDirectives = copy.deepcopy(solution.directives)
            for directive in self.dictDir[directiveGroup]:
                if solution.directives[directiveGroup] != directive:
                    neighborDirectives[directiveGroup] = directive
                    neighborSolution = Solution(neighborDirectives,self.cFiles,self.prjFile)
                    estimatedResults = self.estimator.estimateSynthesis(neighborSolution)
                    neighborSolution.setresults(estimatedResults)
                    neighbors.append(neighborSolution)
        
        neighborsSorted = sorted(neighbors,key=lambda k: k.results['resources'] * k.results['latency']) #sort in ascending order of resource X latency
        #synthesize top n neighbors, for now is top 1 synthesizable
        i=0
        synthesisCount = 0
        n = 1
        topSynthesis = []
        while i < len(neighborsSorted):
            try:
                synthesisTimeLimit = self._SECONDS - (time.time() - self.start)#totalTimeAvailable - timePassed
                self.synthesisWrapper(neighborsSorted[i],synthesisTimeLimit)
            except Exception as error:
                print(error)
            else:
                synthesisCount+=1
                topSynthesis.append(neighborsSorted[i])
                if synthesisCount == n:
                    break
            i+=1
        topSolution=None
        if topSynthesis:
            try:
                self.estimator.trainModel(topSynthesis)
            except Exception as error:
                print(error)
            topSolution = max(topSynthesis,key=lambda k: k.results['resources'] * k.results['latency'])    
        return topSolution

        