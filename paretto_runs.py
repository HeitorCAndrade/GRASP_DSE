import os
import re
import shutil
from pathlib import Path
import subprocess

def run_paretto_runs(dir_tcl):
    cwd = os.getcwd()
    if not Path(dir_tcl).is_dir():
        print('ERROR: directive directry not found!')
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
        with open(os.path.join(cwd, 'script.tcl'), 'r') as f:
            lines = f.readlines()
            for i in range(len(lines)):
                if lines[i].find('open_solution') != -1:
                    print(f'sol_number: {sol_number}')
                    lines[i] = f'open_solution solution_mod_{sol_number}\n'
                    #print(line)
        
        with open(os.path.join(cwd, 'script.tcl'), 'w') as f:
            for line in lines:
                f.write(line)
        subprocess.run('vitis_hls -f script.tcl', shell=True)

    print('finished runs!')
        

def copy_run_reports(dir_runs, dir_report):
    cwd = os.getcwd()
    runs = os.listdir(path=os.path.join(cwd, dir_runs))

    for run in runs:
        if Path(os.path.join(cwd, dir_runs, run, 'impl/verilog/project.runs/impl_1')).is_dir():
            
            from_dir = os.path.join(cwd, dir_runs, run, 'impl/verilog/project.runs/impl_1/')
            print(f'from_dir: {from_dir}')
            to_dir = os.path.join(cwd, dir_report, run, 'reports/')
            print(f'to_dir: {to_dir}')
            os.makedirs(os.path.dirname(to_dir), exist_ok=True)
            if Path(from_dir+'bd_0_wrapper_power_routed.rpt').is_file():
                shutil.copyfile(from_dir+'bd_0_wrapper_power_routed.rpt', to_dir+'impl_power.rpt')
            if Path(from_dir+'bd_0_wrapper_utilization_placed.rpt').is_file():
                shutil.copyfile(from_dir+'bd_0_wrapper_utilization_placed.rpt', to_dir+'impl_utilization_placed.rpt')
            if Path(from_dir+'bd_0_wrapper_timing_summary_routed.rpt').is_file():
                shutil.copyfile(from_dir+'bd_0_wrapper_timing_summary_routed.rpt', to_dir+'impl_timing_summary.rpt')
            from_dir = os.path.join(cwd, dir_runs, run, 'syn/report/')
            print(f'from_dir: {from_dir}')
            print(f'to_dir: {to_dir}')
            if Path(from_dir+'csynth.rpt').is_file():
                shutil.copyfile(from_dir+'csynth.rpt', to_dir+'csynth.rpt')
        else:
            print('dir not found!')
            print(Path(os.path.join(cwd, dir_runs, run, 'impl/verilog/project.runs/impl_1')))

if __name__ == '__main__':
    dir_tcl = input('tcl mod directory name: ')
    dir_runs = input('run directory: ')
    dir_report = input('report directory: ')


    run_paretto_runs(dir_tcl)
    copy_run_reports(dir_runs, dir_report)