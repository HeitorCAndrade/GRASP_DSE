
#---------------------------------------------------------------------------------------------------------------------------------------
#Cada tipo de diretiva sera chamado de uma "variavel".
#Pra fazer o random, para cada variavel será randomizado um valor de seu dominio. 
#Exemplo: Variavel de "unroll main", pode ter como dominio: None, set_directive_unroll -factor 4, set_directive_unroll -factor 8.
#         Portanto nesse caso diremos que essa variavel pode assumir os valores 0,1,2 . 0 sempre será a opção de None (sem aquela diretiva)

#arvore de controle para checar se permutacao ja foi vista
#EXEMPLO: primeiro tipo de diretiva:       [0 | 1 ]
#                                         / | \    \  
#         segundo tipo de diretiva:     [0 |1 |2]  [1]
#E vai indo, os numeros representam qual diretiva foi usada das possiveis diretivas daquele tipo. "0" representa None (sem aquela diretiva)
#---------------------------------------------------------------------------------------------------------------------------------------
import json
import time
from heuristics.heuristic import Heuristic
from pathlib import Path
from domain.solution import Solution
from utils.Script_tcl import generateScript
import copy
from random import seed
from random import randint
import random
from utils.abstractSolutionsSaver import SolutionsSaver

class RandomSearch(Heuristic):
    
    def __init__(self,filesDict,timeLimit=3600,solutionSaver:SolutionsSaver = None):
        super().__init__(filesDict)
        self.sol_count = 1
        self.solutionSaver = solutionSaver
        self.filesDict = filesDict
        self._SECONDS = timeLimit
        seed()
        self.run()
    def setTimeLimit(self,seconds):
        self._SECONDS = seconds
    def run(self):
        onePermutation = {}
        inTime = True
        benchName = self.filesDict['benchName']
        start = time.time()
        controlTree:dict = {}
        temp = self.getFinishedSolutions()
        if temp is not None:
           controlTree = temp 
        else: 
            print('####################\ncheckpoint file not found\n#################### ')
        while inTime:

            onePermutation = self.generateRandomPermutation(controlTree)
            if onePermutation:    #se tiver uma permutacao na variavel
                solution = Solution(onePermutation)         #Solutions a partir deste
                try:
                    #synthesisTimeLimit = self._SECONDS - (time.time() - start) 
                    self.synthesisWrapper(solution,self.solutionSaver)
                except Exception as e:
                    print(e)
                #executa else qnd try roda sem erros
                else:   
                    print(solution.results) 
                    print (len(self.solutions))      

            end = time.time()
            if not onePermutation:
                print('####################\nNo permutations left!\n#################### ')
                break
            if self.filesDict['maxInstances'] > 0 and (self.filesDict['maxInstances']) == self.sol_count:
                print(f'####################\nReached maximum instance count: {self.sol_count}\n#################### ')
                break
            if Path(f'./DATASETS/{benchName}/{new_sol}/impl/verilog/project.runs/impl_1/runme.log').is_file():
                self.sol_count = self.sol_count + 1
            else:
                print(f'####################\n{self.sol_count} failed!\n#################### ')
            new_sol = 'solution' + str(self.sol_count)
            generateScript(self.filesDict['cFiles'], self.filesDict['prjFile'], self.filesDict['benchName'], new_sol)
            if self.solutionSaver:
                self.solutionSaver.save(self.solutions,'./time_stamps/timeStampRandomSearch')              
                        


    

    
