
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
import matplotlib.pyplot as plt
from utils.abstractSolutionsSaver import SolutionsSaver
import seaborn as sns
import seaborn.objects as so
import pandas as pd

class RandomSearch(Heuristic):
    PARETTO_DATASETS = ['filtered_adpcm/ADPCM', 'filtered_aes/AES', 'filtered_backprop/BACKPROP', 'filtered_gemm/GEMM', 'filtered_gsm/GSM', 'filtered_sha/SHA', 'filtered_knn/KNN', 'filtered_gramschmidt/GRAMSCHMIDT', 'filtered_TRANS_FFT/TRANS_FFT', 'filtered_stencil3d/STENCIL3D']
    def __init__(self,filesDict,timeLimit=3600,solutionSaver:SolutionsSaver = None):
        super().__init__(filesDict)
        self.sol_exists = False
        self.sol_count = 1
        self.successful_inst_count = 0
        self.solutionSaver = solutionSaver
        self.benchName = self.filesDict['benchName']
        self._dir = self.filesDict['directory']
        self.paretto_axis = self.filesDict['paretto_frontier']
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
        elif self.filesDict['paretto_frontier'] != 'None':
            self.paretto_frontier(self.benchName, self._dir, self.paretto_axis)
        elif self.filesDict['retrieve_directives']:
            self.retrieve_directives(self.benchName, self._dir)
        elif self.filesDict['retrieve_hls']:
            self.retrieve_all(self.benchName, self._dir)
        elif self.filesDict['build_graphs']:
            self.build_dataframe(self._dir)
        else:
            self.run()


    def setTimeLimit(self,seconds):
        self._SECONDS = seconds

    def retrieve_all(self, bench, _dir = './BENCHMARKS'):
        is_filtered = False
        json_path = './'
        cwd = os.getcwd()
        bench_name = bench

        allowed_directives = ['set_directive_array_partition', 'set_directive_pipeline', 'set_directive_unroll']
        if not Path(os.path.join(cwd, _dir, bench)).is_dir():
            if not Path(os.path.join(cwd, _dir, 'filtered_'+bench)):
                print('ERROR: benchmark directory not found! Check if directory is correct or if benchmark is available.')
                print('exiting...')
                return
            else:
                bench = 'filtered_'+bench+'/'+bench
                
                is_filtered = True
            solution_dict = {}
            sols = os.listdir(os.path.join(cwd, _dir, bench))
        for sol in sols:
            print(f'sol: {sol}')
            directs = []
            if sol.find('mod') == -1:
                with open(os.path.join(cwd, _dir, bench, sol, f'{sol}_data.json'), 'r') as jf:
                    json_dict:dict = json.load(jf)
                    solution_dict[sol] = json_dict['HlsSolution']['DirectiveTcl']

                for direct in solution_dict[sol]: 
                    if direct.find('set_directive_pipeline') != -1:
                        if direct.find('-off=true') != -1:
                            subs = direct.split()
                            direct = subs[0] + ' -off '+subs[1]
                        directs.append(direct)

                    if direct.find('set_directive_array_partition') != -1:
                        subs = direct.split()
                        direct = subs[0]+' '+' '.join(subs[2:-1])+' '+subs[1]+' '+subs[-1]
                        directs.append(direct)

                    if direct.find('set_directive_unroll') != -1:
                        subs = direct.split()
                        direct = subs[0]+' '+' '.join(subs[2:])+' '+subs[1]
                        directs.append(direct)

                    if direct.find('set_directive_loop_flatten') != -1:
                        print(f'sol: {sol} has loop flatten!')
                        directs.append(direct)

                    if direct.find('set_directive_loop_merge') != -1:
                        print(f'sol: {sol} has loop merge!')
                        directs.append(direct)

                with open(os.path.join(cwd, f'{bench_name}_{sol}_hls.tcl'), 'w') as f:
                    for d in directs:
                        f.write(d)
                        f.write('\n')

                    


    def retrieve_directives(self, bench, _dir = './BENCHMARKS'):
        is_filtered = False
        json_path = './'
        cwd = os.getcwd()
        bench_name = bench

        allowed_directives = ['set_directive_array_partition', 'set_directive_pipeline', 'set_directive_unroll']
        if not Path(os.path.join(cwd, _dir, bench)).is_dir():
            if not Path(os.path.join(cwd, _dir, 'filtered_'+bench)):
                print('ERROR: benchmark directory not found! Check if directory is correct or if benchmark is available.')
                print('exiting...')
                return
            else:
                bench = 'filtered_'+bench+'/'+bench
                
                is_filtered = True

        first_line = True
        paretto_sols = {}
        with open('paretto_energy.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                paretto_sols[f'{line[:-1]}'] = []

        first_line = True
        with open('paretto_area.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line not in paretto_sols:
                    paretto_sols[f'{line[:-1]}'] = []

     
        with open('paretto_power.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line not in paretto_sols:
                        paretto_sols[f'{line[:-1]}'] = []

        print(paretto_sols.keys())
        
        for sol in paretto_sols.keys():
            has_undesired_direct = False
            directs = []
            if sol.find('_mod_') == -1:
                with open(os.path.join(cwd, _dir, bench, sol, f'{sol}_data.json'), 'r') as jf:
                    json_dict:dict = json.load(jf)
                    paretto_sols[sol] = json_dict['HlsSolution']['DirectiveTcl']

                for direct in paretto_sols[sol]:
                    #if direct.find('set_directive_loop_flatten') == -1 and direct.find('set_directive_loop_merge') == -1 and direct.find('set_directive_top') == -1:
                    if direct.find('set_directive_pipeline') != -1:
                        if direct.find('-off=true') != -1:
                            subs = direct.split()
                            direct = subs[0] + ' -off '+subs[1]
                        directs.append(direct)

                    if direct.find('set_directive_array_partition') != -1:
                        subs = direct.split()
                        direct = subs[0]+' '+' '.join(subs[2:-1])+' '+subs[1]+' '+subs[-1]
                        directs.append(direct)

                    if direct.find('set_directive_unroll') != -1:
                        subs = direct.split()
                        direct = subs[0]+' '+' '.join(subs[2:])+' '+subs[1]
                        directs.append(direct)

                    if direct.find('set_directive_loop_flatten') != -1 or direct.find('set_directive_loop_merge') != -1:
                        has_undesired_direct = True
                        
                print(has_undesired_direct)
                if has_undesired_direct:
                    with open(os.path.join(cwd, f'{bench_name}_{sol}_mod.tcl'), 'w') as f:
                        for d in directs:
                            f.write(d)
                            f.write('\n')
                        
            
                    

    def paretto_frontier(self, bench, _dir = 'DATASETS', y_axis='energy'):
        cwd = os.getcwd()
        is_filtered = False
        bench_name = bench
        power_file = 'impl/verilog/project.runs/impl_1/bd_0_wrapper_power_routed.rpt'
        time_file = 'impl/verilog/project.runs/impl_1/bd_0_wrapper_timing_summary_routed.rpt'
        area_file = 'impl/verilog/project.runs/impl_1/bd_0_wrapper_utilization_placed.rpt'
        hls_file = 'syn/report/csynth.rpt'
        min_snru = 5
        max_snru = 0
        min_power = 99999
        max_power = 0
        min_time = 99999999999999999
        max_time = 0
        min_snru_sol = ''
        print(f'directory: {_dir}')
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
            if not Path(os.path.join(cwd, _dir, 'filtered_'+bench)):
                print('ERROR: benchmark directory not found! Check if directory is correct or if benchmark is available.')
                print('exiting...')
                return
            else:
                bench = 'filtered_'+bench+'/'+bench
                print(f'found filtered version! ({bench})')
                power_file = 'reports/impl_power.rpt'
                time_file = 'reports/impl_timing_summary.rpt'
                area_file = 'reports/impl_utilization_placed.rpt'
                hls_file = 'reports/csynth.rpt'
                if bench_name == 'GRAMSCHMIDT':
                    print('GRAMSCHMIDT uses different hls report!')
                    hls_file = 'reports/csynth2.rpt'
                is_filtered = True
        
        best_energy = 999999999999999999
        best_time = 9999999999999999999
        best_power = 999999999999999999
        best_area = 5
        target_period = 8.000

        valid_sols_list = []
        energy_paretto =  []
        power_paretto =  []
        area_paretto =  []
        energy_area_paretto = []
        mod_count = 0
        #solutions = os.listdir(path=f'{_dir}/{bench}')
        solutions = os.listdir(os.path.join(cwd, _dir, bench))
        np_lut = np.array([])
        np_ff = np.array([])
        np_bram = np.array([])
        np_dsp = np.array([])
        np_dynP = np.array([])
        np_staticP = np.array([])
        np_power = np.array([])
        np_latency = np.array([])
        np_cycle = np.array([])
        np_time = np.array([])
        np_energy = np.array([])
        np_area = np.array([])
        np_wns = np.array([])
        print(f'sol count: {len(solutions)}')
        for sol in solutions:
            if sol.find('_mod_') != -1:
                mod_count = mod_count + 1
            disregard_sol = False
            is_already_disregarded = False
            #print('\n')
            #print(f'checking solution {sol}...')
            sol_ff = -1
            sol_bram = -1
            sol_dsp = -1
            sol_power = -1
            sol_dyn = -1.0
            sol_static = -1.0
            sol_period = -1.0
            sol_target_period = -1
            sol_cycles = -1

            lut_line_found = False
            ff_line_found = False
            bram_line_found = False
            dsp_line_found = False

            sol_path = os.path.join(cwd, _dir, bench, sol)
            if Path(sol_path).is_dir():
                if Path(f'{sol_path}/{area_file}').is_file():
                    with open(f'{sol_path}/{area_file}', 'r') as f:
                        lines = f.readlines()
                    for line in lines:
                        if line.find('CLB LUTs') != -1 and not lut_line_found:
                            sol_lut = int((rx.findall(line))[0])
                            lut_line_found = True
                            # if sol == 'solution466':
                            #     print(f'lut line:')
                            #     print(line)
                            #     print(f'extracted value: {sol_lut}')
                            #     print('----------------------------------------------------------------------------------')
                            #print(f'lut found: {sol_lut}')
                        if line.find('CLB Registers') != -1 and not ff_line_found:
                            sol_ff = int((rx.findall(line))[0])
                            ff_line_found = True
                            # if sol == 'solution466':
                            #     print(f'ff line:')
                            #     print(line)
                            #     print(f'extracted value: {sol_ff}')
                            #     print('----------------------------------------------------------------------------------')
                            #print(f'ff found: {sol_ff}')
                        if line.find('Block RAM Tile') != -1 and not bram_line_found:
                            sol_bram = float((rx.findall(line))[0])
                            bram_line_found = True
                            # if sol == 'solution466':
                            #     print(f'bram line:')
                            #     print(line)
                            #     print(f'extracted value: {sol_bram}')
                            #     print('----------------------------------------------------------------------------------')
                            #print(f'bram found: {sol_bram}')
                        if line.find(' DSPs') != -1 and not dsp_line_found:
                            sol_dsp = int((rx.findall(line))[0])
                            dsp_line_found = True
                            # if sol == 'solution466':
                            #     print(f'dsp line:')
                            #     print(line)
                            #     print(f'extracted value: {sol_dsp}')
                            #     print('----------------------------------------------------------------------------------')
                            #print(f'dsp found: {sol_dsp}')

                    sol_area = sol_lut/MAX_LUT + sol_ff/MAX_FF + sol_bram/MAX_BRAM + sol_dsp/MAX_DSP
                    if sol_area > max_snru:
                        max_snru = sol_area

                    temp_lut = -1.0
                    temp_ff = -1.0
                    temp_bram = -1.0
                    temp_dsp = -1.0

                    if sol_area < min_snru:
                        min_snru = sol_area
                        min_snru_sol = sol
                        print(f'updated min snru: {min_snru}, from sol: {sol}')
                        print(f'LUT FF BRAM DSP:')
                        print(f'{sol_lut} / {MAX_LUT} + {sol_ff} / {MAX_FF} + {sol_bram} / {MAX_BRAM} + {sol_dsp} / {MAX_DSP}')
                        temp_lut = sol_lut/MAX_LUT
                        temp_ff = sol_ff/MAX_FF
                        temp_bram = sol_bram/MAX_BRAM
                        temp_dsp = sol_dsp/MAX_DSP
                        print(f'temp results: {temp_lut} + {temp_ff} + {temp_bram}+ {temp_dsp}')
                        print(f'{temp_lut+temp_ff+temp_bram+temp_dsp} should equal {min_snru}')
                        print(f'###############################################################################')
                else:
                    print('area not found')
                    disregard_sol = True
                    if not is_already_disregarded:
                        is_already_disregarded = True
                        disregard_count = disregard_count + 1

                if Path(f'{sol_path}/{time_file}').is_file():
                    with open(f'{sol_path}/{time_file}', 'r') as f:
                        is_first_occurrence = 0
                        lines = f.readlines()
                    for line in lines:
                        if line.find('ap_clk') != -1:
                            if is_first_occurrence == 0:
                                is_first_occurrence = is_first_occurrence + 1
                                sol_period = float((rx.findall(line))[2])
                            elif is_first_occurrence == 1:
                                wns = float((rx.findall(line))[0])
                                #print(f'wns: {wns}')
                                sol_target_period = sol_period
                                sol_period = sol_period - wns
                                #print(f'period found: {sol_period}\n')
                                is_first_occurrence = is_first_occurrence + 1
                        
                else:
                    print('time not found')
                    disregard_sol = True
                    if not is_already_disregarded:
                        is_already_disregarded = True
                        disregard_count = disregard_count + 1


                if Path(f'{sol_path}/{power_file}').is_file():
                    with open(f'{sol_path}/{power_file}', 'r') as f:
                        lines = f.readlines()
                    for line in lines:
                        if line.find('Total On-Chip Power (W)') != -1:
                            sol_power = float((rx.findall(line))[0])
                        if line.find('Dynamic (W)') != -1:
                            sol_dyn = float((rx.findall(line))[0])
                            #print(f'power found: {sol_power}')
                        if line.find('Device Static (W)') != -1:
                            sol_static = float((rx.findall(line))[0])

                else:
                    print('power not found')
                    disregard_sol = True
                    if not is_already_disregarded:
                        is_already_disregarded = True
                        disregard_count = disregard_count + 1

                if Path(f'{sol_path}/{hls_file}').is_file():
                    with open(f'{sol_path}/{hls_file}', 'r') as f:
                        line_count = 0
                        lines = f.readlines()
                    for line in lines:
                        if line.find('(cycles)') != -1:
                            line_count = line_count + 1
                        if line_count > 0:
                            line_count = line_count + 1
                        if line_count == 4:
                            if bench_name == 'STENCIL3D':
                                sol_cycles = int((rx.findall(line))[2])
                            else:
                                sol_cycles = int((rx.findall(line))[1])
                                if sol == 'solution214':
                                    print(f'sol214: {sol_cycles}')
                            #print(f'cycle found: {sol_cycles}')
                else:
                    print('hls not found')
                    disregard_sol = True
                    if not is_already_disregarded:
                        is_already_disregarded = True
                        disregard_count = disregard_count + 1

                sol_time = sol_cycles * sol_period
                if sol_time < 0:
                    print(f'{sol}: WARNING: negative time! ({sol_cycles}, {sol_period})')
                    disregard_sol = True
                    if not is_already_disregarded:
                        is_already_disregarded = True
                        disregard_count = disregard_count + 1
                else:
                    if sol_time < min_time:
                        min_time = sol_time

                    if sol_time > max_time:
                        max_time = sol_time
                
                #print(f'old power: {sol_power}')
                sol_power = sol_dyn*sol_target_period/sol_period + sol_static
                sol_energy = sol_power * sol_time
                #print(f'new power: {sol_power}')
                if sol_power > max_power:
                    max_power = sol_power

                if sol_power < min_power:
                    min_power = sol_power

                

                if not disregard_sol:
                    valid_sols_list.append(sol)
                    np_time = np.append(np_time, sol_time)
                    np_energy = np.append(np_energy, sol_energy)
                    np_power = np.append(np_power, sol_power)
                    np_area = np.append(np_area, sol_area)
                else:
                    print(f'solution {sol} discarted!')
                    

        sol_dict = dict()
        np_y_paretto = np.array([])
        if y_axis == 'energy':
            np_y_paretto = np_energy
        if y_axis == 'area':
            np_y_paretto = np_area
        if y_axis == 'power':
            np_y_paretto = np_power
        for i in range(len(valid_sols_list)):
            if not (np_time[i], np_y_paretto[i]) in sol_dict:
                sol_dict[(np_time[i], np_y_paretto[i])] = [valid_sols_list[i]]
            else:
                sol_dict[(np_time[i], np_y_paretto[i])].append(valid_sols_list[i])
                #sol_dict[valid_sols_list[i]] = [np_time[i], np_energy[i]]

        sorted_dict = sorted(sol_dict.keys(), key=lambda x: x[0])
        sorted_energy = sorted(sol_dict.keys(), key=lambda x: x[1])

        print(f'mod count: {mod_count}')
        

        p_front = [sorted_dict[0]] #shortest time from solutions
        p_front_sols = [sol_dict[sorted_dict[0]][0]]
        print(f'init sol: {sol_dict[sorted_dict[0]][0]}')
        for index in range(len(sorted_dict)-1):
            i = index+1
            pair = sorted_dict[i] #[sorted_dict[i][0], sorted_dict[i][1]]
            if pair[1] <= p_front[-1][1]:
                p_front.append(pair)
                for _sol in sol_dict[sorted_dict[i]]:
                    p_front_sols.append(_sol)
        p_frontX = [pair[0] for pair in p_front]
        p_frontY = [pair[1] for pair in p_front]

        print(f'length of time: {len(p_frontX)}')
        print(f'length of {y_axis}: {len(p_frontY)}')

        with open(f'paretto_{y_axis}.txt', 'w') as fe:
            for line in p_front_sols:
                fe.write(f'{line}\n')

        x_points = []
        y_points = []
        p_color = []
        zord = []
        is_mod = False
        paretto_mod = False
        for x, y in sol_dict.keys():
            is_mod = False
            paretto_mod = False
            for _s in sol_dict[(x, y)]:
                if _s.find('_mod_') != -1:
                    is_mod = True
                    _s_split = _s.split('_mod_')
                    _s_join = ''.join(_s_split)
                    print(_s_join)
                    if _s_join in p_front_sols:
                        paretto_mod = True

            if not is_mod or paretto_mod or ((x in p_frontX) and (y in p_frontY)):
                x_points.append(x)
                y_points.append(y)
            else:
                pass
                #print('sol NOT added: ')
                #print(sol_dict[(x, y)])
                #print('\n')
            if (x in p_frontX) and (y in p_frontY):
                if not (not is_mod or paretto_mod):
                    print('ERROR: color added to invalid pair! (red)')
                    print(sol_dict[(x, y)])
                    print('\n')
                p_color.append('paretto frontier')
            elif paretto_mod:
                print('paretto mod added!')
                if not (not is_mod or paretto_mod):
                    print('ERROR: color added to invalid pair! (green)')
                    print(sol_dict[(x, y)])
                    print('\n')
                p_color.append('loop directive removed')
            elif not is_mod:
                if not (not is_mod or paretto_mod):
                    print('ERROR: color added to invalid pair! (blue)')
                    print(sol_dict[(x, y)])
                    print('\n')
                p_color.append('')
            else:
                print('unknown condition!')
                
        sns.set_theme()
        #df = pd.Dataframe()
        #sns.color_palette("Spectral", as_cmap=True)
        #sns.scatterplot(x=x_points, y=y_points, hue=p_color, s=18, palette=['blue', 'red', 'seagreen'])
        #plt.scatter(x_points, y_points, c=p_color)
        #if y_axis == 'energy':
            #plt.title(f'{bench_name} energy-time paretto frontier')
            #plt.ylabel('energy (nJ)')
       # if y_axis == 'power':
           # plt.title(f'{bench_name} power-time paretto frontier')
            #plt.ylabel('power (W)')
        #if y_axis == 'area':
            #plt.title(f'{bench_name} area-time paretto frontier')
            #plt.ylabel('area (snru)')
       # plt.xlabel('time (ns)')
       # plt.savefig(f'{bench_name}_{y_axis}_time.pdf')
        #plt.show()

        

        print(f'min snru found: {min_snru}, max snru found: {max_snru}')
        print(f'min power found: {min_power}, max power found: {max_power}')
        print(f'min time found: {min_time}, max time found: {max_time}')
        print(f'finished writing paretto files! There was {disregard_count} solution(s) that were disregarded')
        print('exiting...')

    def build_dataframe(self, _dir, save=True, file_name= 'stacked_bar_graph.pdf'):
        cwd = os.getcwd()
        data_dict = {}
        if not Path(os.path.join(cwd, _dir)).is_dir():
            print(f'ERROR: {_dir} directory not found!')
            return -1
        else:
            dir_path = os.path.join(cwd, _dir)

        # df = pd.DataFrame({
        #     'bench':[],
        #     'total_mods':[],
        #     'kept_mods':[],
        #     'removed_mods':[],
        # })
        #df.set_index(list(df)[0])
        for bench in self.PARETTO_DATASETS:
            print(f'running application {bench}...')
            bench_path = os.path.join(dir_path, bench)
            if Path(bench_path).is_dir():
                bench_name = bench.split('/')
                self.paretto_frontier(bench_name[1], dir_path, 'area')
                self.paretto_frontier(bench_name[1], dir_path, 'energy')
                self.paretto_frontier(bench_name[1], dir_path, 'power')
                lines_area = []
                lines_power = []
                lines_energy = []
                sol_dirs = os.listdir(bench_path)
                with open('paretto_area.txt', 'r') as f:
                    lines_area = f.readlines()
                with open('paretto_power.txt', 'r') as f:
                    lines_power = f.readlines()
                with open('paretto_energy.txt', 'r') as f:
                    lines_energy = f.readlines()

                os.system(f'cp paretto_area.txt {bench_name[1]}_paretto_area.txt')
                os.system(f'cp paretto_power.txt {bench_name[1]}_paretto_power.txt')
                os.system(f'cp paretto_energy.txt {bench_name[1]}_paretto_energy.txt')
                sum_lines = lines_area
                for l in lines_power:
                    if l not in sum_lines:
                        sum_lines.append(l)
                for l in lines_energy:
                    if l not in sum_lines:
                        sum_lines.append(l)

                total_mod_sol_number = 0
                total_removed_mod_sol = 0
                total_kept_mod_sol = 0
                total_paretto = len(sum_lines)
                #get number of mod solutions
                for d in sol_dirs:
                    if d.find('_mod_') != -1:
                        total_mod_sol_number = total_mod_sol_number + 1
                        
                print(f'found {total_mod_sol_number} mod sol numbers!')
                for l in sum_lines:
                    l_str = l.split('\n')
                    if l_str[0].find('_mod_') != -1:
                        total_kept_mod_sol = total_kept_mod_sol + 1
                        #total_paretto = total_paretto - 1
                total_removed_mod_sol = total_mod_sol_number - total_kept_mod_sol
                print(f'found {total_kept_mod_sol} kept mod solutions')
                print(f'found {total_removed_mod_sol} removed mod solutions')
                print(f'found {total_paretto} paretto solutions')
                if bench_name[1] != 'GRAMSCHMIDT': #bench_name[1] != 'TRANS_FFT' and 
                    data_dict[bench_name[1]] = [total_mod_sol_number, total_kept_mod_sol, total_removed_mod_sol, total_paretto]

                #df.loc[bench_name] = [total_mod_sol_number, total_kept_mod_sol, total_removed_mod_sol]

                #build stacked bar graph
                #save graph as PDF

            else:
                print(f'WARNING: {bench} directory not found! Path input: {bench_path}')

        df = pd.DataFrame.from_dict(data_dict, orient='index', columns=['Total modified solutions', 'Stayed in Pareto front', 'Left Pareto front', 'Pareto front size'])
        df['Application'] = df.index
        #sns.set_theme(style="darkgrid")
        #so.Plot(df["Application"], df["Total modified solutions"]).add(so.Bar(), so.Hist())
        # for k in data_dict.keys():
        #     print('showing results...')
        #     print(f'{k}: total: {data_dict[k][0]} kept: {data_dict[k][1]} discarded: {data_dict[k][2]}')

        print('#################################')
        print(df)
        df_pct = df.copy()
        # df_pct = df[["Application", "Stayed in Paretto front", "Left Paretto front", "Paretto front size"]].copy()
        # df_pct[["Stayed in Paretto front", "Left Paretto front", "Paretto front size"]] = df_pct[["Stayed in Paretto front", "Left Paretto front", "Paretto front size"]].div(
        #     df_pct[["Paretto front size", "Paretto front size", "Paretto front size"]].sum(axis=1), axis=0
        # ) * 100

        df_pct["Stayed in Pareto front"] = df["Stayed in Pareto front"] / df["Pareto front size"] * 100
        df_pct["Left Pareto front"] = df["Left Pareto front"] / df["Pareto front size"] * 100

        df_pct["Do not have target directives"] = 100 - (df_pct["Stayed in Pareto front"] + df_pct["Left Pareto front"])

        stayed_avg = df_pct.loc[:, 'Left Pareto front'].mean()

        df_long = df_pct.melt( #era df.melt
            id_vars="Application",
            value_vars=["Stayed in Pareto front", "Left Pareto front", "Do not have target directives"],
            var_name="Type",
            value_name="Percentage"
        )
        pivoted = df_long.pivot(index="Application", columns="Type", values="Percentage")
        custom_colors = ["#777b7e", "#4169e1", "#d30000"]  #grey=777b7e red=d30000 blue=4169e1
        # Plot stacked bars
        ax = pivoted.plot(
            kind="bar",
            stacked=True,
            figsize=(18, 6),
            color=custom_colors
        )

        for container in ax.containers:
            ax.bar_label(
                container,
                fmt="%.0f%%",  
                label_type="center",  
                fontsize=12,   
                #fontweight="bold",
                color="white" if container.patches[0].get_facecolor() != (0.827,0.827,0.827,1.0) else "black"  
            )

        plt.legend(
            #title="Label",
            fontsize=20,        
            title_fontsize=20,  
            bbox_to_anchor=(0.7, -0.1),
            ncol=3
        )
        
        plt.xticks(rotation=0, fontsize=16)   
        plt.yticks(fontsize=16)               
        plt.ylabel("Percentage", fontsize=18)
        plt.xlabel("Application", fontsize=18)
        
        plt.legend(ncol=3, bbox_to_anchor=(0.75, 1.05)) 
        if save:
            plt.savefig(file_name, bbox_inches="tight")
        #sns.despine()
        plt.show()
        print(f'percentage avg: {stayed_avg}')

        


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
                        


    

    
