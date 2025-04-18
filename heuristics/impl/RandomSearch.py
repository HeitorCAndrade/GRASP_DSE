
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
import json
from heuristics.heuristic import Heuristic
from pathlib import Path
from domain.solution import Solution
from utils.Script_tcl import generateScript
from utils.Script_tcl import generateReportScript
import subprocess
import copy
import glob
import shutil
from random import seed
from random import randint
import random
import numpy as np
import re
from utils.abstractSolutionsSaver import SolutionsSaver

class RandomSearch(Heuristic):
    
    def __init__(self,filesDict,timeLimit=3600,solutionSaver:SolutionsSaver = None):
        super().__init__(filesDict)
        self.sol_exists = False
        self.sol_count = 1
        self.successful_inst_count = 0
        self.solutionSaver = solutionSaver
        self.benchName = self.filesDict['benchName']
        self.base_instances = self.filesDict['base_instances']
        self.filesDict = filesDict
        self.synthesisTimeLimit = int(filesDict['timeLimit'])
        self._SECONDS = timeLimit
        seed()
        if self.filesDict['verify']:
            if self.filesDict['reports']:
                self.verify_successful_runs(self.benchName, True)
            else:
                self.verify_successful_runs(self.benchName)
        elif self.filesDict['filter']:
            self.filter_dataset(self.benchName)
        elif self.filesDict['clean']:
            self.remove_unwanted_files(self.benchName)
        elif self.filesDict['paretto_frontier'] != '':
            self.paretto_frontier(self.benchName)
            pass
        else:
            self.run()


    def setTimeLimit(self,seconds):
        self._SECONDS = seconds


    def paretto_frontier(self, bench, _dir = 'DATASETS'):
        cwd = os.getcwd()
        disregard_count = 0
        numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
        rx = re.compile(numeric_const_pattern, re.VERBOSE)
        MAX_LUT = 871680
        MAX_FF = 1743360
        MAX_BRAM = 1344
        MAX_DSP = 5952
        #return instances that form the paretto frontier for that benchmark

        #if not Path(f'{dir}/{bench}').is_dir():
        if not Path(os.path.join(cwd, _dir, bench)).is_dir():
            print('ERROR: benchmark directory not found! Check if directory is correct or if benchmark is available.')
            print('exiting...')
            return
        
        best_energy = np.nan
        best_time = np.nan
        best_power = np.nan
        best_area = np.nan

        energy_paretto =  []
        power_paretto =  []
        area_paretto =  []
        energy_area_paretto = []

        #solutions = os.listdir(path=f'{_dir}/{bench}')
        solutions = os.listdir(os.path.join(cwd, _dir, bench))

        for sol in solutions:
            disregard_sol = False
            is_already_disregarded = False
            print('\n')
            print(f'checking solution {sol}...')
            sol_ff = -1
            sol_bram = -1
            sol_dsp = -1
            sol_power = -1
            sol_period = -1.0
            sol_cycles = -1
            sol_path = os.path.join(cwd, _dir, bench, sol)
            if Path(sol_path).is_dir():
                if Path(f'{sol_path}/impl/verilog/project.runs/impl_1/bd_0_wrapper_utilization_placed.rpt').is_file():
                    with open(f'{sol_path}/impl/verilog/project.runs/impl_1/bd_0_wrapper_utilization_placed.rpt', 'r') as f:
                        lines = f.readlines()
                    for line in lines:
                        if line.find('CLB LUTs') != -1:
                            sol_lut = int((rx.findall(line))[0])
                            #print(f'lut found: {sol_lut}')
                        if line.find('CLB Registers') != -1:
                            sol_ff = int((rx.findall(line))[0])
                            #print(f'ff found: {sol_ff}')
                        if line.find('Block RAM Tile') != -1:
                            sol_bram = float((rx.findall(line))[0])
                            #print(f'bram found: {sol_bram}')
                        if line.find(' DSPs') != -1:
                            sol_dsp = int((rx.findall(line))[0])
                            #print(f'dsp found: {sol_dsp}')

                    sol_area = sol_lut/MAX_LUT + sol_ff/MAX_FF + sol_bram/MAX_BRAM + sol_dsp/MAX_DSP
                else:
                    disregard_sol = True
                    if not is_already_disregarded:
                        is_already_disregarded = True
                        disregard_count = disregard_count + 1

                
                

                if Path(f'{sol_path}/impl/verilog/project.runs/impl_1/bd_0_wrapper_timing_summary_routed.rpt').is_file():
                    with open(f'{sol_path}/impl/verilog/project.runs/impl_1/bd_0_wrapper_timing_summary_routed.rpt', 'r') as f:
                        is_first_occurrence = True
                        lines = f.readlines()
                    for line in lines:
                        if line.find('ap_clk') != -1 and is_first_occurrence:
                            is_first_occurrence = False
                            sol_period = float((rx.findall(line))[2])
                            #print(f'period found: {sol_period}')
                else:
                    disregard_sol = True
                    if not is_already_disregarded:
                        is_already_disregarded = True
                        disregard_count = disregard_count + 1

                if Path(f'{sol_path}/impl/verilog/project.runs/impl_1/bd_0_wrapper_power_routed.rpt').is_file():
                    with open(f'{sol_path}/impl/verilog/project.runs/impl_1/bd_0_wrapper_power_routed.rpt', 'r') as f:
                        lines = f.readlines()
                    for line in lines:
                        if line.find('Total On-Chip Power (W)') != -1:
                            sol_power = float((rx.findall(line))[0])
                            #print(f'power found: {sol_power}')
                else:
                    disregard_sol = True
                    if not is_already_disregarded:
                        is_already_disregarded = True
                        disregard_count = disregard_count + 1

                if Path(f'{sol_path}/syn/report/csynth.rpt').is_file():
                    with open(f'{sol_path}/syn/report/csynth.rpt', 'r') as f:
                        line_count = 0
                        lines = f.readlines()
                    for line in lines:
                        if line.find('(cycles)') != -1:
                            line_count = line_count + 1
                        if line_count > 0:
                            line_count = line_count + 1
                        if line_count == 4:
                            sol_cycles = int((rx.findall(line))[1])
                            #print(f'cycle found: {sol_cycles}')
                else:
                    disregard_sol = True
                    if not is_already_disregarded:
                        is_already_disregarded = True
                        disregard_count = disregard_count + 1

                sol_time = sol_cycles * sol_period
                sol_energy = sol_power * sol_time
                

                if not disregard_sol:
                    #time x energy
                    if sol_energy < best_energy:
                        best_energy = sol_energy
                        print('energy paretto updated! (energy axis)')
                        energy_paretto.append(sol)
                    elif sol_time < best_time:
                        best_time = sol_time
                        print('energy paretto updated! (time axis)')
                        energy_paretto.append(sol)
                    elif (sol_energy == best_energy) and (sol_time == best_time):
                        energy_paretto.append(sol)
                        print('energy paretto updated! solution with equal values as frontier')

                    #time x power
                    if sol_power < best_power:
                        best_power = sol_power
                        power_paretto.append(sol)
                    elif sol_time < best_time:
                        best_time = sol_time
                        power_paretto.append(sol)
                    elif (sol_power == best_power) and (sol_time == best_time):
                        power_paretto.append(sol)

                    #time x area
                    if sol_area < best_area:
                        best_area = sol_area
                        area_paretto.append(sol)
                    elif sol_time < best_time:
                        best_time = sol_time
                        area_paretto.append(sol)
                    elif (sol_area == best_area) and (sol_time == best_time):
                        area_paretto.append(sol)
                        

        with open('paretto_energy.txt', 'w') as fe:
            for line in energy_paretto:
                fe.write(f'{line}\n')

        with open('paretto_power.txt', 'w') as fp:
            for line in power_paretto:
                fp.write(f'{line}\n')

        with open('paretto_area.txt', 'w') as fa:
            for line in area_paretto:
                fa.write(f'{line}\n')

        print(f'finished writing paretto files! There was {disregard_count} solution(s) that were disregarded')
        print('exiting...')


                #check time x power, time x energy, energy x area, time x area


    # def run_loop_dict(self, bench, loop_directive, dir = '.'):
    #     print('WARNING: bases instances must be done before running this command!')
    #     run = 1
    #     if loop_directive == 'merge':
    #         chosed_direct = 'loop_merge'
    #     else:
    #         chosed_direct = 'loop_flatten'

    #     #directories = os.listdir(path=f'./DATASETS/{bench}')

    #     #number of base runs to gather data
    #     runs = 30
    #     json_file = '/home/heitor/Masters/DATASET_GEN/solution2_data.json'
    #     #first, extract directives from run
        
    #     to_read_run = 'solution'+str(run)
    #     options = []
    #     # for i in range(runs):
    #     #     if Path(f'{dir}/{bench}').is_dir():
    #     #         if Path(f'{dir}/{bench}/{to_read_run}/{to_read_run}_data.json').is_file():
    #     with open(json_file, 'r') as jf:
    #         sol_json:dict = json.load(jf)
    #         #print(sol_json['HlsSolution']['DirectiveTcl'])
    #     base_run_directives = sol_json['HlsSolution']['DirectiveTcl']

    #     #get flatten or merge directives available
    #     json_2 = f'./directives_files/aes.json'
    #     with open(json_2, 'r') as jf:
    #         directives_options:dict = json.load(jf)

        
    #     for d, c in directives_options['directives'].items():
    #         if d.find(chosed_direct) != -1:
    #             flatten_option = c['possible_directives'][1]
    #             options.append(flatten_option)

    #     #print(options)

    #     #transform directives from solution + loop/merge into solution for script generation
    #     final_directives = []
    #     run = run + 1


    def copy_prj_files(self, benchName, sol):
        from_dir = f'./DATASETS/{benchName}/{sol}/'
        to_dir = f'./DATASETS/filtered/{benchName}/{sol}/'

        warn_missing = False

        if not Path(f'{to_dir}').is_dir():
            Path(f'{to_dir}').mkdir()

        f = open(to_dir+'__MISSING_FILES__', 'w')

        #IRs:
        Path(to_dir+'IRs').mkdir(exist_ok=True)
        for file in glob.glob(os.path.join(from_dir+'.autopilot/db/',"*.bc")):
            shutil.copy2(file, to_dir+'IRs/')
        #TODO: copiar o outro IR -> falar com Gabriel

        #directives
        try:
            shutil.copyfile(from_dir+f'{sol}.directive', to_dir+f'{sol}.directive')
        except FileNotFoundError:
            f.write('missing directive file\n')
            warn_missing = True

        try:
            shutil.copyfile(from_dir+f'{sol}_data.json', to_dir+f'{sol}_data.json')
        except FileNotFoundError:
            f.write('missing json directive file\n')
            warn_missing = True

        #reports
        Path(to_dir+'reports').mkdir(exist_ok=True)
        try: 
            shutil.copyfile(from_dir+'syn/report/csynth.rpt', to_dir+'reports/csynth.rpt')
        except FileNotFoundError:
            f.write('missing csynth rpt\n')
            warn_missing = True
        try:
            shutil.copyfile(from_dir+'syn/report/csynth.xml', to_dir+'reports/csynth.xml')
        except FileNotFoundError:
            f.write('missing csynth xml\n')
            warn_missing = True

        try:
            shutil.copyfile(from_dir+'impl/report/verilog/export_syn.rpt', to_dir+'reports/export_syn.rpt')
            shutil.copyfile(from_dir+'impl/report/verilog/export_syn.xml', to_dir+'reports/export_syn.xml')
        except FileNotFoundError:
            f.write('missing export synth files\n')
            warn_missing = True

        try:
            shutil.copyfile(from_dir+'impl/report/verilog/export_impl.rpt', to_dir+'reports/export_impl.rpt')
            shutil.copyfile(from_dir+'impl/report/verilog/export_impl.xml', to_dir+'reports/export_impl.xml')
        except FileNotFoundError:
            f.write('missing export impl files\n')
            warn_missing = True

        try:
            shutil.copyfile(from_dir+'impl/verilog/project.runs/impl_1/bd_0_wrapper_power_routed.rpt', to_dir+'reports/impl_power.rpt')
            shutil.copyfile(from_dir+'impl/verilog/project.runs/impl_1/bd_0_wrapper_timing_summary_routed.rpt', to_dir+'reports/impl_timing_summary.rpt')
            shutil.copyfile(from_dir+'impl/verilog/project.runs/impl_1/bd_0_wrapper_utilization_placed.rpt', to_dir+'reports/impl_utilization_placed.rpt')
        except FileNotFoundError:
            f.write('missing project implementation reports\n')
            warn_missing = True

        try:
            shutil.copyfile(from_dir+'impl/verilog/project.runs/impl_1/runme.log', to_dir+'reports/impl_runme.log')
        except FileNotFoundError:
            f.write('missing implementation log\n')
            warn_missing = True
        try:
            shutil.copyfile(from_dir+'impl/verilog/project.runs/synth_1/runme.log', to_dir+'reports/synth_runme.log')
        except FileNotFoundError:
            f.write('missing logic synthesis log\n')
            warn_missing = True

        #miscellaneous files 
        try:
            shutil.copyfile(from_dir+'impl/export.dcp', to_dir+'export.dcp')
        except FileNotFoundError:
            f.write('missing design checkpoint (.dcp)\n')
            warn_missing = True


        f.close()
        if not warn_missing:
            Path(to_dir+'__MISSING_FILES__').unlink()

    def remove_unwanted_files(self, bench):
        #in .autopilot directory, remove yml, xml, txt, v, vhd, wcfg, c, cpp, log, tcl, rpt, adb -> alternatively, preserve bc, ll, json files
        #in impl, remove rtd, vhdl directory
        if Path(f'./DATASETS/{bench}').is_dir():
            directories = os.listdir(path=f'./DATASETS/{bench}')
            for dir in directories:
                print(f'processing {dir}...')
                if Path(f'./DATASETS/{bench}/{dir}').is_dir():
                    print(f'inside directory .autopilot/db/...')
                    for auto in os.listdir(path=f'./DATASETS/{bench}/{dir}/.autopilot/db'):
                        if Path(os.path.join(f'./DATASETS/{bench}/{dir}/.autopilot/db/', auto)).is_file():
                            if (not auto.endswith('.bc')) and (not auto.endswith('.ll')) and (not auto.endswith('.json')):
                                os.remove(os.path.join(f'./DATASETS/{bench}/{dir}/.autopilot/db', auto))
                                print(f'deleting file: {auto}')
                        else:
                            shutil.rmtree(os.path.join(f'./DATASETS/{bench}/{dir}/.autopilot/db', auto))
                            print(f'deleting directory: {auto}')
                        
                    try:
                        print('deleting directory /syn/vhdl')
                        shutil.rmtree(f'./DATASETS/{bench}/{dir}/syn/vhdl')
                    except FileNotFoundError:
                        print('/syn/vhdl directory not found')

                    try:
                        print('deleting directory /impl/vhdl')
                        shutil.rmtree(f'./DATASETS/{bench}/{dir}/impl/vhdl')
                    except FileNotFoundError:
                        print('/impl/vhdl directory not found\n')
                    print('----------------------------------------------')
                    print(f'inside directory impl/verilog...')
                    for root, dirs, files in os.walk(f'./DATASETS/{bench}/{dir}/impl/verilog', topdown=True):
                        for dir in dirs:
                            if dir == 'vhdl':
                                print('deleting directory vhdl')
                                shutil.rmtree(os.path.join(root), dir)
                        for f in files:
                            if (not f.endswith('.v')) and (not f.endswith('.tcl')) and (not f.endswith('.xpr')) and (not f.endswith('.rpt')) and (not f.endswith('.xml')) and (not f.endswith('.log')) and (not f.endswith('.xdc')):
                                print(f'deleting file {f} inside {root}')
                                os.remove(os.path.join(root, f))

                print('##############################################\n')


    def filter_dataset(self, benchName):
        total_runs = 0
        missing_timing = 0
        missing_area = 0
        missing_power = 0
        missing_directives = 0
        missing_directives_j = 0

        filtered_dir_ok = True
        directories = os.listdir(path=f'./DATASETS/{benchName}')
        try:
            Path(f'./DATASETS/filtered/{benchName}').mkdir(parents=True)
        except FileExistsError:
            print('dataset directory already exists. Continuing...')
        else:
            print('filtered directory created!')

        for dir in directories:
                if Path(f'./DATASETS/{benchName}/{dir}/impl/verilog/project.runs/impl_1/runme.log').is_file():
                    with open(f'./DATASETS/{benchName}/{dir}/impl/verilog/project.runs/impl_1/runme.log', 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.find('route_design completed successfully') != -1:
                                if filtered_dir_ok:
                                    self.copy_prj_files(benchName, dir)

        filtered_dirs = os.listdir(path=f'./DATASETS/filtered/{benchName}')
        for sol in filtered_dirs:
            total_runs = total_runs + 1
            if not Path(f'./DATASETS/filtered/{benchName}/{sol}/reports/impl_power.rpt').is_file():
                missing_power = missing_power + 1
            if not Path(f'./DATASETS/filtered/{benchName}/{sol}/reports/impl_timing_summary.rpt').is_file():
                print(f'sol: {sol}')
                missing_timing = missing_timing + 1
            if not Path(f'./DATASETS/filtered/{benchName}/{sol}/reports/impl_utilization_placed.rpt').is_file():
                missing_area = missing_area + 1
            if not Path(f'./DATASETS/filtered/{benchName}/{sol}/{sol}.directive').is_file():
                missing_directives = missing_directives + 1
            if not Path(f'./DATASETS/filtered/{benchName}/{sol}/{sol}_data.json').is_file():
                missing_directives_j = missing_directives_j + 1

        print(f'finish filtering dataset {benchName}')
        print(f'out of {total_runs} runs...')
        print(f'there are {missing_power} instances with missing power report')
        print(f'there are {missing_timing} instances with missing timing report')
        print(f'there are {missing_area} instances with missing area report')
        print(f'there are {missing_directives} instances with missing directive run file')
        print(f'there are {missing_directives_j} instances with missing directive json file\n')


    def generate_missing_reports(self, benchName, dir, area, power, timing):
        generateReportScript(benchName, dir, area, power, timing)
        subprocess.run('vivado -mode tcl -script ./domain/generate_report.tcl', shell=True)

    def verify_successful_runs(self, benchName, gen_rpts = False):
        #INFO: [Common 17-206] Exiting Vivado at
        print(f'verifying successful runs for {benchName}...')
        suc_runs = 0
        fully_complete = 0
        rpt_count_power = 0
        rpt_count_timing = 0
        rpt_count_area = 0
        failed_timing = 0
        gen_area = False
        gen_power = False
        gen_timing = False
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
                            if line.find('route_design completed successfully') != -1:
                                suc_runs = suc_runs + 1
                                if line.find('CRITICAL WARNING: [Timing 38-282] The design failed to meet the timing requirements') != -1:
                                    failed_timing = failed_timing + 1
                                if line.find('[Common 17-206] Exiting Vivado at') != -1:
                                    fully_complete = fully_complete + 1
                                if Path(f'./DATASETS/{benchName}/{dir}/impl/verilog/project.runs/impl_1/bd_0_wrapper_utilization_placed.rpt').is_file():
                                    rpt_count_area = rpt_count_area + 1
                                else:
                                    gen_area = True
                                if Path(f'./DATASETS/{benchName}/{dir}/impl/verilog/project.runs/impl_1/bd_0_wrapper_power_routed.rpt').is_file():
                                    rpt_count_power = rpt_count_power + 1
                                else:
                                    gen_power = True
                                if Path(f'./DATASETS/{benchName}/{dir}/impl/verilog/project.runs/impl_1/bd_0_wrapper_timing_summary_routed.rpt').is_file():
                                    rpt_count_timing = rpt_count_timing + 1
                                else:
                                    gen_timing = True
                                if (gen_area or gen_power or gen_timing) == True:
                                    print(f'missing reports for {benchName}/{dir}!')
                                if (gen_area or gen_power or gen_timing) == True and gen_rpts:
                                    print(f'generating missing reports for {benchName}/{dir}...')
                                    self.generate_missing_reports(benchName, dir, gen_area, gen_power, gen_timing)
                                    print('done!\n')
                            
                gen_area = False
                gen_power = False
                gen_timing = False

            if suc_runs > 0:
                print(f'found {suc_runs} successful runs, of which {fully_complete} were fully completed!')
                print(f'there are {suc_runs-rpt_count_area} successful runs without the final area report')
                print(f'there are {suc_runs-rpt_count_power} successful runs without the final power report')
                print(f'there are {suc_runs-rpt_count_timing} successful runs without the final timing report')
                print(f'there are {failed_timing} successful runs with failed timing!')
            else:
                print(f'no successful runs found!')
            return suc_runs


    def run_base_inst(self, controlTree, succ_prev_runs):
        is_first_run = True
        new_sol = 'solution1'
        sol_index = 1
        successfull_runs = succ_prev_runs
        store_count = 0
        benchName = self.filesDict['benchName']
        current_directive = ''
        dir_index = 1

        permutation, current_directive, dir_index, is_first_run = self.generateSingularPermutations(controlTree, current_directive, dir_index, is_first_run)
        solution = Solution(permutation)
        generateScript(self.filesDict['cFiles'], self.filesDict['prjFile'], self.filesDict['benchName'], new_sol)
        was_successfull = self.synthesisWrapper(solution, self.synthesisTimeLimit, self.solutionSaver, sol_index, designToolChoice='vitis')
        if was_successfull:
            successfull_runs = successfull_runs + 1
        sol_index = sol_index + 1
        while not is_first_run:
            permutation, current_directive, dir_index, is_first_run = self.generateSingularPermutations(controlTree, current_directive, dir_index, is_first_run)
            solution = Solution(permutation)
            new_sol = 'solution'+str(sol_index)
            generateScript(self.filesDict['cFiles'], self.filesDict['prjFile'], self.filesDict['benchName'], new_sol)
            was_successfull = self.synthesisWrapper(solution, self.synthesisTimeLimit, self.solutionSaver, sol_index, designToolChoice='vitis')
            if was_successfull:
                if store_count == 5:
                    self.storePermutations(controlTree, successfull_runs)
                    store_count = 0
                else:
                    store_count = store_count + 1
                successfull_runs = successfull_runs + 1
            sol_index = sol_index + 1

        verified_successfull_runs = self.verify_successful_runs(benchName)

        print(f'atempted runs: {sol_index-1}')
        print(f'counted successful runs: {successfull_runs}')
        print(f'verified successful runs: {verified_successfull_runs}')

        return controlTree, sol_index, verified_successfull_runs
        

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
        
        if self.base_instances:
            print('starting base instances')
            controlTree, self.sol_count, self.successful_inst_count = self.run_base_inst(controlTree, self.successful_inst_count)
            self.storePermutations(controlTree, self.successful_inst_count)
            print('finished base runs!')
        else:
            print('base instances not set')

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
                manual_suc_verif = self.verify_successful_runs(benchName)
                if manual_suc_verif >= self.successful_inst_count:
                    print('successful runs count mismatch! correcting...')
                    self.successful_inst_count = manual_suc_verif
                else:
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
                        


    

    
