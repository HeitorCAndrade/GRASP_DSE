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
    pass

def extract_utilization(project_path, solution):
    pass


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