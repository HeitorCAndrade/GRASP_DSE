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
        sol_number = (re.findall(r'\b\d+\b', run))[0]
        subprocess.run(f'cp {os.path.join(cwd, dir_tcl, run)} .', shell=True)
        lines = []
        with open(os.path.join(cwd, 'script.tcl'), 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.find('open_solution') != -1:
                    line = f'open_solution solution_mod_{sol_number}\n'
                    print(line)
        
        #with open(os.path.join(cwd, 'script.tcl'), 'w') as f:
        for line in lines:
            print(line)
            #f.write(line)
        print(f'running with {run}...')
        #subprocess.run('vitis_hls -f script.tcl', shell=True)

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
            shutil.copyfile(from_dir+'bd_0_wrapper_power_routed.rpt', to_dir+'impl_power.rpt')
            shutil.copyfile(from_dir+'bd_0_wrapper_utilization_placed.rpt', to_dir+'impl_utilization_placed.rpt')
            shutil.copyfile(from_dir+'bd_0_wrapper_timing_summary_routed.rpt', to_dir+'impl_timing_summary.rpt')
            from_dir = os.path.join(cwd, dir_runs, run, 'syn/report/')
            print(f'from_dir: {from_dir}')
            print(f'to_dir: {to_dir}')
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