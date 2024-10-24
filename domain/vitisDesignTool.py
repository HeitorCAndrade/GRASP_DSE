from random import randrange
from domain.desingTool import DesignTool
from domain.vivadoDesignTool import Vivado
from domain.solution import Solution
import xml.etree.ElementTree as ET
from pathlib import Path
import os.path
import shutil
import time
import subprocess
import psutil
import sys
from exceptions.timeExceededException import TimeExceededException
class Vitis(DesignTool):
 
    
    
    def __init__(self, maxRAMUsage = 70, directivesFilename = './domain/directives.tcl'):
        self._MAX_RAM_USAGE = maxRAMUsage #in percentage
        self._DIRECTIVES_FILENAME = directivesFilename
        self._PROCESSNAME = 'vitis_hls'
        self._VIVADO_PROC_NAME = 'vivado'
        self._SCRIPT_PATH = './domain/callVitis.sh'
        self._FF_VALUE = 1; self._LUT_VALUE = 2; self._DSP_VALUE = 345.68; self._BRAM_VALUE = 547.33
        if sys.platform == 'win32':
            self._PROCESSNAME = 'vitis_hls.exe'
            self._SCRIPT_PATH = './domain/callVitis.bat'
        
    def runSynthesisTeste(self, solution: Solution, timeLimit=None, solutionSaver = None):
        if timeLimit is None:
            timeLimit = float('inf')
        if timeLimit<=0:
            raise Exception(f"****{self._PROCESSNAME} has exceed max time usage****")
        results = {}
        results['FF'] = randrange(10)
        results['DSP'] = randrange(1)
        results['LUT'] = randrange(10)
        results['BRAM'] = randrange(2)
        results['resources'] = randrange(3)
        results['latency'] = randrange(4)
        solution.setresults(results)
        return solution
    
    def check_if_done(self, benchmark, sol_count):
        sol = 'solution'+str(sol_count)
        is_done = False
        if Path(f'./DATASETS/{benchmark}/{sol}/impl/verilog/project.runs/impl_1/runme.log').is_file():
            print('implementation exists!')
            with open(f'./DATASETS/{benchmark}/{sol}/impl/verilog/project.runs/impl_1/runme.log', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.find('report_power completed successfully') != -1:
                        is_done = True
        return is_done

    def runSynthesis(self, solution: Solution, timeLimit = None, solutionSaver= None, benchmark = '', sol_count = 1):
        is_done = False
        #self.__killOnGoingVitisProcessIfAny()    
        #self.__killOnGoingVivadoProcessIfAny() 
        #if not especified, there is infinite time to run synthesis
        if timeLimit is None:
            timeLimit = float('inf')
        if timeLimit<=0:
            raise Exception(f"****{self._PROCESSNAME} has exceed max time usage****")
        self.__writeDirectivesIntoFile(solution.directives)
        #vitis call using subprocess
        print('########################################################')
        print(f'starting run {sol_count}!')
        print('########################################################')
        p = subprocess.Popen([self._SCRIPT_PATH])
        start = time.time()
        parent_pid = p.pid
        parent_process = psutil.Process(parent_pid)
        while parent_process.is_running() and parent_process.status() != psutil.STATUS_ZOMBIE:
            time.sleep(60)
            is_done = self.check_if_done(benchmark, sol_count)
            if time.time() - start > timeLimit or is_done == True:
                print('########################################################')
                if is_done:
                  print(f'run {sol_count} was successfull! Killing processes...')  
                else:
                    print(f'run {sol_count} exceeded time limit! Killing processes...')
                print('########################################################')
                for p in parent_process.children(recursive=True):
                    p.kill()
                parent_process.kill()
                print('finished killing processes')

        is_done = self.check_if_done(benchmark, sol_count) #last check
        return is_done

    def __writeDirectivesIntoFile(self,directives):
        directivesFile = open(self._DIRECTIVES_FILENAME, "w")
        for value in directives.values():
            if value != '' and value is not None:
                directivesFile.write(value + '\n')
            print(value)
        directivesFile.close()  

    def __killOnGoingVitisProcessIfAny(self):
        mydir='./Raise_dse'
        while os.path.exists(mydir):
            time.sleep(3)
            try:
                shutil.rmtree(mydir)
            except Exception as error:
                print(error)
            for proc in psutil.process_iter(['name']):
                if proc.name() == self._PROCESSNAME:
                    print(f'Killed process {proc.name()}!')
                    proc.kill()
                    break        

    def __killOnGoingVivadoProcessIfAny(self):
        mydir='./Raise_dse'
        while os.path.exists(mydir):
            time.sleep(3)
            try:
                shutil.rmtree(mydir)
            except Exception as error:
                print(error)
            for proc in psutil.process_iter(['name']):
                if proc.name() == self._VIVADO_PROC_NAME:
                    print(f'Killed process {proc.name()}!')
                    proc.kill()
                    break 

    def __monitorVitisProcess(self, timeLimit, solutionSaver):
        #testing if the synthesis ended
        vitisIsRunning = True   
        start = time.time()
        while vitisIsRunning:
            #time between checking if the process is still running
            time.sleep(3)
            vitisIsRunning = False
            for proc in psutil.process_iter(['name']):
                if proc.name() == self._PROCESSNAME:
                    vitisIsRunning = True
                    #check memory usage
                    try:
                        memoryUse = proc.memory_percent()
                    except Exception as e:
                        print(e)
                        break
                    if memoryUse > self._MAX_RAM_USAGE:
                        proc.kill()   
                        raise Exception(f"****{self._PROCESSNAME} has exceed max RAM usage****")
                    #check time usage 
                    if time.time()-start >= timeLimit:
                        proc.kill()   
                        raise TimeExceededException(f"****{self._PROCESSNAME} has exceed max time usage****")
                    if solutionSaver:
                        solutionSaver.save(None,'./time_stamps/timeStampFiller')
                    break

    def __monitorVivadoProcess(self, timeLimit, solutionSaver):
        #testing if the synthesis ended
        vivadoIsRunning = True   
        start = time.time()
        while vivadoIsRunning:
            #time between checking if the process is still running
            time.sleep(3)
            vivadoIsRunning = False
            for proc in psutil.process_iter(['name']):
                if proc.name() == self._VIVADO_PROC_NAME:
                    vivadoIsRunning = True
                    #check memory usage
                    try:
                        memoryUse = proc.memory_percent()
                    except Exception as e:
                        print(e)
                        break
                    if memoryUse > self._MAX_RAM_USAGE:
                        proc.kill()   
                        raise Exception(f"****{self._VIVADO_PROC_NAME} has exceed max RAM usage****")
                    #check time usage 
                    if time.time()-start >= timeLimit:
                        proc.kill()   
                        raise TimeExceededException(f"****{self._VIVADO_PROC_NAME} has exceed max time usage****")
                    if solutionSaver:
                        solutionSaver.save(None,'./time_stamps/timeStampFiller')
                    break
        
    def __getResultsFromSynthesis(self, xmlPath:str):   
        results = {}
        if os.path.exists(xmlPath):  
            print("Synthesis ended")
            #read xml file
            tree = ET.parse(xmlPath)
            root = tree.getroot()

            x = root.find('AreaEstimates')
            x = x.find('Resources')
            results['FF'] =int(x.find('FF').text)
            results['DSP'] = int(x.find('DSP').text)
            results['LUT'] = int(x.find('LUT').text)
            results['BRAM'] = int(x.find('BRAM_18K').text)
            results['resources'] =  results['FF'] * self._FF_VALUE + results['LUT'] * self._LUT_VALUE + results['DSP'] * self._DSP_VALUE + results['BRAM'] * self._BRAM_VALUE    
            x = root.find('PerformanceEstimates')
            x = x.find('SummaryOfOverallLatency')
            try:
                results['latency'] = int(x.find('Average-caseLatency').text)
            except ValueError:
                raise ValueError("****UNDETERMINED LATENCY****")
        else:
            raise Exception("****Error in synthesis - NO Synthesis Results****")   
        return results    
