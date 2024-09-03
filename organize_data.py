import numpy as np
from pathlib import Path
import json
import re

def extract_power_report(project_path, solution):
    numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
    rx = re.compile(numeric_const_pattern, re.VERBOSE)
    full_path = project_path + solution + "impl/verilog/project.runs/impl_1/"
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

def extract_timing_summary(project_path, solution):
    numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
    rx = re.compile(numeric_const_pattern, re.VERBOSE)
    full_path = project_path + solution + "impl/verilog/project.runs/impl_1/"
    report_name = "bd_0_wrapper_timing_summary_routed.rpt"

    timing_ar = []
    for _ in range(6):
        timing_ar.append(np.NAN)

    if not Path(full_path+report_name).is_file():
        return [-1, -1, -1, -1]
    
    with open(full_path+report_name, "r") as rpt:
        lines = rpt.readlines()

    line_count = 0
    for line in lines:
        if line.find('Design Timing Summary') != -1:
            start_line_count = True
            
        if start_line_count:
            line_count += 1

        if line_count == 10:
            str_list = rx.findall(line)
            timing_ar[0] = float(str_list[0]) # vivado_WNS
            timing_ar[1] = float(str_list[1]) # vivado_TNS
            timing_ar[2] = float(str_list[4]) # vivado_WHS
            timing_ar[3] = float(str_list[5]) # vivado_THS
            timing_ar[4] = float(str_list[8]) # vivado_WPWS
            timing_ar[5] = float(str_list[9]) # vivado_TPWS

    #TODO: find and return worst slack path

    return timing_ar


def extract_utilization(project_path, solution):
    full_path = project_path + solution + "impl/verilog/project.runs/impl_1/"
    report_name = "bd_0_wrapper_utilization_placed.rpt"


def organize_data(dataset_path, writing_path, instance="None"):
    dataset_list = json.load("benchmarks.json")
    failed_instances = 0
    sol_index = 1
    sol_dir = "solution" + sol_index
    for dset in dataset_list:
        while (Path(sol_dir).is_dir()):
            vivado_WNS  = np.NAN #worst negative slack
            vivado_TNS  = np.NAN #total negative slack
            vivado_WHS  = np.NAN #worst hold slack
            vivado_THS  = np.NAN #total hold slack
            vivado_LUT  = np.NAN
            vivado_FF   = np.NAN
            vivado_DSP  = np.NAN
            vivado_BRAM = np.NAN
            vivado_pow  = np.NAN #total power
            vivado_dynP = np.NAN #dynamic power
            vivado_stcP = np.NAN #static power

            vitis_CP    = np.NAN #critical path
            vitis_FMAX  = np.NAN

            directives  = []

            if Path(sol_dir+"/impl/verilog/project.xpr").is_file():
                vivado_pow, vivado_dynP, vivado_stcP = extract_power_report("DATASET"+dset, sol_dir)
                
                pass #TODO: open each report (vivado: timing.prt, power.rpt, usage.rpt vitis: report.rpt) to get info
            else:
                failed_instances += 1

            #TODO: get directives regardless if failed insntance or not

            
            sol_index += 1
            sol_dir = "solution" + sol_index