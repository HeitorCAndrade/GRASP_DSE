
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
import os
import time
import psutil
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
        self.sol_exists = False
        self.sol_count = 1
        self.successful_inst_count = 0
        self.solutionSaver = solutionSaver
        self.filesDict = filesDict
        self.synthesisTimeLimit = int(filesDict['timeLimit'])
        self._SECONDS = timeLimit
        seed()
        self.run()
    def setTimeLimit(self,seconds):
        self._SECONDS = seconds


    def verify_successful_runs(self, benchName):
        print(f'verifying successful runs for {benchName}...')
        suc_runs = 0
        if not Path(f'./DATASETS/{benchName}').is_dir():
            print('benchmark directory not found, assuming 0 successful runs...')
            return suc_runs
        else:
            directories = os.listdir(path=f'./DATASETS/{benchName}')
            print(f'solutions found: {len(directories)}')
            for dir in directories:
                if Path(f'./DATASETS/{benchName}/{dir}/impl/verilog/project.runs/impl_1/runme.log').is_file():
                    with open(f'./DATASETS/{benchName}/{dir}/impl/verilog/project.runs/impl_1/runme.log', 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.find('report_power completed successfully') != -1:
                                suc_runs = suc_runs + 1
            if suc_runs > 0:
                print(f'found {suc_runs} successful runs!')
            else:
                print(f'no successful runs found!')
            return suc_runs

    def run(self):
        was_successfull = False
        #inTime = True
        manual_suc_verif = 0
        new_sol = 'solution1'
        benchName = self.filesDict['benchName']
        #start = time.time()
        controlTree:dict = {}
        if self.filesDict['resume']:
            if Path(f'./DATASETS/{benchName}/stored_permutations.json').is_file():
                print('Found permutation file!')
                self.successful_inst_count, controlTree = self.getStoredPermutations()
                if self.successful_inst_count == -1:
                    self.successful_inst_count = self.verify_successful_runs(benchName)
                manual_suc_verif = self.verify_successful_runs(benchName)

                if manual_suc_verif != self.successful_inst_count:
                    print(f'WARNING! STORED SUCCESSFUL COUNT WAS NOT UPDATED CORRECTLY! {manual_suc_verif}, {self.successful_inst_count}')
                    self.successful_inst_count = manual_suc_verif
                self.sol_count = self.successful_inst_count+1
                print(self.successful_inst_count)
                new_sol = 'solution' + str(self.sol_count)
                self.sol_exists = True
                while (self.sol_exists):
                    self.sol_exists = False
                    if Path(f'./DATASETS/{benchName}/{new_sol}/impl/verilog/project.runs/impl_1/runme.log').is_file():
                        with open(f'./DATASETS/{benchName}/{new_sol}/impl/verilog/project.runs/impl_1/runme.log', 'r') as f:
                            lines = f.readlines()
                            for line in lines:
                                if line.find('report_power completed successfully') != -1:
                                    print(f'implementation {new_sol} already done!')
                                    self.sol_count = self.sol_count + 1
                                    new_sol = 'solution' + str(self.sol_count)
                                    self.sol_exists = True

                generateScript(self.filesDict['cFiles'], self.filesDict['prjFile'], self.filesDict['benchName'], new_sol)
            else:
                print('WARNING: resume flag set to True but no permutation file was found!')
        
        while True:
            onePermutation = self.generateRandomPermutation(controlTree)
            self.sol_exists = True
            if onePermutation:    #se tiver uma permutacao na variavel
                solution = Solution(onePermutation)         #Solutions a partir deste
                try:
                    print(f'executing {new_sol}...')
                    was_successfull = self.synthesisWrapper(solution, self.synthesisTimeLimit, self.solutionSaver, self.sol_count)
                    
                except Exception as e:
                    print(e)
                else:   
                    print(f'done instance {new_sol}!')   

            end = time.time()
            if not onePermutation:
                print('####################\nNo permutations left!\n#################### ')
                break
            if was_successfull:
                self.successful_inst_count = self.successful_inst_count + 1
                self.storePermutations(controlTree, self.successful_inst_count)
            else:
                print(f'####################\n{self.sol_count} failed!\n#################### ')
            was_successfull = False
            if self.filesDict['maxInstances'] > 0 and (self.filesDict['maxInstances']) == self.successful_inst_count:
                print(f'####################\nReached maximum instance count: {self.sol_count}\n#################### ')
                print(self.successful_inst_count)
                print(self.filesDict['maxInstances'])
                break
            if self.successful_inst_count > 1 and (self.filesDict['maxInstances']) == (self.successful_inst_count / 2):
                print('half instance count reached, verifying completed ones ...')
                manual_suc_verif = self.verify_successful_runs(benchName)
                if manual_suc_verif != self.successful_inst_count:
                    print('successful runs count mismatch! correcting...')
                    self.successful_inst_count = manual_suc_verif
            self.sol_count = self.sol_count + 1
            new_sol = 'solution' + str(self.sol_count)
            self.sol_exists = True
            while (self.sol_exists):
                self.sol_exists = False
                if Path(f'./DATASETS/{benchName}/{new_sol}/impl/verilog/project.runs/impl_1/runme.log').is_file():
                    with open(f'./DATASETS/{benchName}/{new_sol}/impl/verilog/project.runs/impl_1/runme.log', 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.find('report_power completed successfully') != -1:
                                print(f'implementation {new_sol} already done!')
                                self.sol_count = self.sol_count + 1
                                new_sol = 'solution' + str(self.sol_count)
                                self.sol_exists = True
                                
            generateScript(self.filesDict['cFiles'], self.filesDict['prjFile'], self.filesDict['benchName'], new_sol)
            if self.solutionSaver:
                self.solutionSaver.save(self.solutions,'./time_stamps/timeStampRandomSearch')              
                        


    

    
