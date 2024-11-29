import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
from argparse import ArgumentParser
import matplotlib
import json
import matplotlib.pyplot as plt
import re

def extract_power_report(project_path, solution):
    numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
    rx = re.compile(numeric_const_pattern, re.VERBOSE)
    full_path = "./DATASETS/" + project_path + '/' + solution + "/impl/verilog/project.runs/impl_1/"
    report_name = "bd_0_wrapper_power_routed.rpt"

    total_power = np.NaN
    dynamic_power = np.NAN
    static_power = np.NAN

    if not Path(full_path+report_name).is_file():
        return [-1, -1, -1]
        
    with open(full_path+report_name, "r") as rpt:
        lines = rpt.readlines()

    for line in lines:
        if line.find('Total On-Chip Power (W)') != -1:
            total_power = float((rx.findall(line))[0])
        if line.find('Dynamic (W)') != -1:
            dynamic_power = float((rx.findall(line))[0])
        if line.find('Device Static (W)') != -1:
            static_power = float((rx.findall(line))[0])

    return [total_power, dynamic_power, static_power]

# def extract_timing_summary(project_path, solution):
#     numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
#     rx = re.compile(numeric_const_pattern, re.VERBOSE)
#     full_path = project_path + solution + "impl/verilog/project.runs/impl_1/"
#     report_name = "bd_0_wrapper_timing_summary_routed.rpt"

#     timing_ar = []
#     for _ in range(6):
#         timing_ar.append(np.NAN)

#     if not Path(full_path+report_name).is_file():
#         return [-1, -1, -1, -1]
    
#     with open(full_path+report_name, "r") as rpt:
#         lines = rpt.readlines()

#     line_count = 0
#     for line in lines:
#         if line.find('Design Timing Summary') != -1:
#             start_line_count = True
            
#         if start_line_count:
#             line_count += 1

#         if line_count == 10:
#             str_list = rx.findall(line)
#             timing_ar[0] = float(str_list[0]) # vivado_WNS
#             timing_ar[1] = float(str_list[1]) # vivado_TNS
#             timing_ar[2] = float(str_list[4]) # vivado_WHS
#             timing_ar[3] = float(str_list[5]) # vivado_THS
#             timing_ar[4] = float(str_list[8]) # vivado_WPWS
#             timing_ar[5] = float(str_list[9]) # vivado_TPWS

#     #TODO: find and return worst slack path

#     return timing_ar


def extract_timing_summary(bench_name, solution):
    path = f'./DATASETS/{bench_name}/{solution}/impl/report/verilog/'

    if Path(path+'export_impl.xml').is_file():
        tree = ET.parse(path+'export_impl.xml')
        root = tree.getroot()
        wns = root.find('TimingReport/WNS_FINAL').text
        tns = root.find('TimingReport/TNS_FINAL').text
        #whs = root.find('').text
        #ths = root.find('').text
        return float(wns), float(tns)
    
    return -1.0, -1.0

def extract_utilization(bench_name, solution):
    path = f'./DATASETS/{bench_name}/{solution}/impl/report/verilog/'

    if Path(path+'export_impl.xml').is_file():
        tree = ET.parse(path+'export_impl.xml')
        root = tree.getroot()
        lut  = root.find('AreaReport/Resources/LUT').text
        bram  = root.find('AreaReport/Resources/BRAM').text
        ff    = root.find('AreaReport/Resources/FF').text
        dsp   = root.find('AreaReport/Resources/DSP').text
        clb   = root.find('AreaReport/Resources/CLB').text
        latch = root.find('AreaReport/Resources/LATCH').text
        target_clock = root.find('TimingReport/TargetClockPeriod').text
        achieved_clk = root.find('TimingReport/AchievedClockPeriod').text
        return int(lut), int(bram), int(ff), int(dsp), int(clb), int(latch), float(target_clock), float(achieved_clk)
    
    return -1, -1, -1, -1, -1, -1, -1.0, -1.0


def extract_hls_report(bench_name, solution):
    path = f'./DATASETS/{bench_name}/{solution}/syn/report/'

    if Path(path+'csynth.xml').is_file():
        tree = ET.parse(path+'csynth.xml')
        root = tree.getroot()
        time_info = root.find('ModuleInformation/Module/PerformanceEstimates/SummaryOfOverallLatency/Average-caseLatency').text
        clock_period = root.find('ModuleInformation/Module/PerformanceEstimates/SummaryOfTimingAnalysis/TargetClockPeriod').text
        return int(time_info), float(clock_period)
    
    return -1, -1.0


def organize_data(bench_name, filter_flag):
    #dataset_list = json.load("benchmarks.json")
    dset_dir = f'./DATASETS/{bench_name}'
    failed_instances = 0
    sol_index = 1
    sol_dir = 'solution' + str(sol_index)

    list_to_df = []

    bench_dataframe = pd.DataFrame(columns=['wns', 'tns', 'lut', 'ff', 'dsp', 'bram', 'clb', 'latch', 'target_clk', 'achieved_clk', 'total_power', 
                                            'dynamic_power', 'static_power', 'clock_cycles'])

    for _ in Path(dset_dir).iterdir():
        if Path(f'{dset_dir}/{sol_dir}').is_dir():
            print('got here 0')
            vivado_WNS  = np.NAN #worst negative slack
            vivado_TNS  = np.NAN #total negative slack
            vivado_WHS  = np.NAN #worst hold slack
            vivado_THS  = np.NAN #total hold slack

            vivado_LUT  = np.NAN
            vivado_FF   = np.NAN
            vivado_DSP  = np.NAN
            vivado_BRAM = np.NAN
            vivado_CLB  = np.NAN
            vivado_latch = np.NAN

            target_clock = np.NAN
            achieved_clk = np.NAN

            vivado_pow  = np.NAN #total power
            vivado_dynP = np.NAN #dynamic power
            vivado_stcP = np.NAN #static power

            vitis_CP    = np.NAN #clock period
            vitis_FMAX  = np.NAN
            vitis_CC    = np.NAN #clock cycles

            directives  = []

            if Path(f'./DATASETS/{bench_name}/{sol_dir}/impl/verilog/project.runs/impl_1/runme.log').is_file():
                print('got here 1')
                with open(f'./DATASETS/{bench_name}/{sol_dir}/impl/verilog/project.runs/impl_1/runme.log', 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.find('report_power completed successfully') != -1:
                            print('got here 2')
                            #vivado_WNS, vivado_TNS, vivado_WHS, vivado_THS = extract_timing_summary(bench_name, sol_dir)
                            vivado_WNS, vivado_TNS = extract_timing_summary(bench_name, sol_dir)
                            vivado_pow, vivado_dynP, vivado_stcP = extract_power_report(bench_name, sol_dir)
                            vivado_LUT, vivado_BRAM, vivado_FF, vivado_DSP, vivado_CLB, vivado_latch, target_clock, achieved_clk  = extract_utilization(bench_name, sol_dir)
                            vitis_CP, vitis_CC = extract_hls_report(bench_name, sol_dir)

                            list_to_df.append([sol_dir, vivado_LUT, vivado_BRAM, vivado_FF, vivado_DSP, vivado_CLB, vivado_latch, target_clock, achieved_clk,
                                               vivado_WNS, vivado_TNS, vitis_CC, vivado_pow, vivado_dynP, vivado_stcP])
                        else:
                            failed_instances += 1

            #TODO: get directives regardless if failed insntance or not

        sol_index += 1
        sol_dir = "solution" + str(sol_index)
    print('list:')
    print(list_to_df)
    bench_dataframe = pd.DataFrame(list_to_df)
   # bench_dataframe.set_index(list(bench_dataframe)[0])
    bench_dataframe.columns = ['solution', 'lut', 'bram', 'ff', 'dsp', 'clb', 'latch', 'target_clk', 'achieved_clk', 'wns', 'tns', 'cycles', 'total_power', 'dynamic_power', 'static_power']
    
    return bench_dataframe 

def build_graphs(resources_data, bench_name):
    #resources_data.plot.scatter(x='cycles', y='lut')
    plt.scatter(resources_data['cycles'], resources_data['lut'])
    plt.show()

def main():
    parser = ArgumentParser()

    parser.add_argument('-b', '--benchmark', help='benchmark name or use \'*\' for all benchmarks available', required=True)
    parser.add_argument('-f', '--filter', help='use this option to filter the benchmark, leaving only the reports, directives and IRs', required=False)
    parser.add_argument('-g', '--graphs', help='set this flag to make graphs comparing design resources usage vs design speed (in clock cycles)', required=False, nargs='?', const=1)
    parser.add_argument('-s', '--sanity-check', help='check if the benchmark has the amount provided of valid samples', required=False)

    args = parser.parse_args()

    bench_name = args.benchmark

    f_flag = args.filter

    resources_data = []
    
    if bench_name != '*':
        assert Path(f'./DATASETS/{bench_name}').is_dir()
        aux = organize_data(bench_name, f_flag)
        if args.graphs:
            build_graphs(aux, bench_name)
        resources_data.append(aux)
    else:
        assert Path('./DATASETS').is_dir()
        for bench in Path('./DATASETS').iterdir():
            aux = organize_data(bench, f_flag)
            resources_data.append(aux)


if __name__ == '__main__':
    main()


    




    

