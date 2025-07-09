import os
import re
import shutil
from pathlib import Path
import subprocess

def run_paretto_runs(dir_tcl, hls_only=False):
    cwd = os.getcwd()
    script_name = 'script.tcl'
    if hls_only:
        print('SELECTED HLS ONLY!')
        script_name = 'hls_script.tcl'
    if not Path(dir_tcl).is_dir():
        print('ERROR: directive directory not found!')
        return

    runs = os.listdir(path=os.path.join(cwd, dir_tcl))
    sol_number = 0
    for run in runs:
        print(f'run: {run}')
        if run.find('STENCIL3D') != -1:
            sol_number = (re.findall(r'\d+', run))[1]
        else:
            sol_number = (re.findall(r'\d+', run))[0]
        subprocess.run(f'cp {os.path.join(cwd, dir_tcl, run)} ./directives.tcl', shell=True)
        print(f'preparing run {sol_number}...')
        print(f'copied directive file {os.path.join(cwd, dir_tcl, run)}')
        lines = []
        with open(os.path.join(cwd, script_name), 'r') as f:
            lines = f.readlines()
            for i in range(len(lines)):
                if lines[i].find('open_solution') != -1:
                    print(f'sol_number: {sol_number}')
                    lines[i] = f'open_solution solution_mod_{sol_number}\n'
                    #print(line)
        
        with open(os.path.join(cwd, script_name), 'w') as f:
            for line in lines:
                f.write(line)
        subprocess.run(f'vitis_hls -f {script_name}', shell=True)

    print('finished runs!')


def copy_run_reports(dir_runs, dir_report, hls_only=False):
    cwd = os.getcwd()
    runs = os.listdir(path=os.path.join(cwd, dir_runs))
    incomplete_runs = []
    if hls_only:
        print('copy reports: SELECTED HLS ONLY!')
    for run in runs:
        no_complete_reports = False
        if not hls_only:
            if Path(os.path.join(cwd, dir_runs, run, 'impl/verilog/project.runs/impl_1')).is_dir():
                
                from_dir = os.path.join(cwd, dir_runs, run, 'impl/verilog/project.runs/impl_1/')
                print(f'from_dir: {from_dir}')
                to_dir = os.path.join(cwd, dir_report, run, 'reports/')
                print(f'to_dir: {to_dir}')
                os.makedirs(os.path.dirname(to_dir), exist_ok=True)
                if Path(from_dir+'bd_0_wrapper_power_routed.rpt').is_file():
                    shutil.copyfile(from_dir+'bd_0_wrapper_power_routed.rpt', to_dir+'impl_power.rpt')
                else:
                    no_complete_reports = True
                    incomplete_runs.append(run)
                if Path(from_dir+'bd_0_wrapper_utilization_placed.rpt').is_file():
                    shutil.copyfile(from_dir+'bd_0_wrapper_utilization_placed.rpt', to_dir+'impl_utilization_placed.rpt')
                else:
                    if not no_complete_reports:
                        no_complete_reports = True
                        incomplete_runs.append(run)
                if Path(from_dir+'bd_0_wrapper_timing_summary_routed.rpt').is_file():
                    shutil.copyfile(from_dir+'bd_0_wrapper_timing_summary_routed.rpt', to_dir+'impl_timing_summary.rpt')
                else:
                    if not no_complete_reports:
                        no_complete_reports = True
                        incomplete_runs.append(run)
                from_dir = os.path.join(cwd, dir_runs, run, 'syn/report/')
                print(f'from_dir: {from_dir}')
                print(f'to_dir: {to_dir}')
                if Path(from_dir+'csynth.rpt').is_file():
                    shutil.copyfile(from_dir+'csynth.rpt', to_dir+'csynth.rpt')
                else:
                    if not no_complete_reports:
                        no_complete_reports = True
                        incomplete_runs.append(run)
            else:
                print('dir not found!')
                print(Path(os.path.join(cwd, dir_runs, run, 'impl/verilog/project.runs/impl_1')))
        else:
            from_dir = os.path.join(cwd, dir_runs, run, 'syn/report/')
            if Path(from_dir+'csynth.rpt').is_file():
                shutil.copyfile(from_dir+'csynth.rpt', to_dir+'csynth.rpt')
            else:
                if not no_complete_reports:
                    no_complete_reports = True
                    incomplete_runs.append(run)

    for run in incomplete_runs:
        print(f'run {run} is missing reports!')

if __name__ == '__main__':
    dir_tcl = input('tcl mod directory name: ')
    dir_runs = input('run directory: ')
    dir_report = input('report directory: ')
    hls_s = input('hls only? : y or n')

    if hls_s == 'y':
        hls = True
    elif hls_s == 'n':
        hls = False
    else:
        input_valid = False

    if input_valid:
        run_paretto_runs(dir_tcl, hls)
        copy_run_reports(dir_runs, dir_report, hls)
    else:
        print(f'ERROR: hls option should be y or n (value assigned: {hls_s})! Exiting...')