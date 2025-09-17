import os
import re
import shutil
from pathlib import Path
import subprocess

AES = {'name': 'AES', 'files': 'add_files {../GRASP_DSE/benchmarks/aes/aes_enc.c ../GRASP_DSE/benchmarks/aes/aes.c ../GRASP_DSE/benchmarks/aes/aes_dec.c}', 'top': 'set_top aes_main', 'dict': 'open_project MOD_FIX_RUNS/AES_FIX_MOD_RUNS'}
ADPCM = {'name': 'ADPCM', 'files': 'add_files {../GRASP_DSE/benchmarks/adpcm/adpcm.c}', 'top': 'set_top adpcm_main', 'dict': 'open_project MOD_FIX_RUNS/ADPCM_FIX_MOD_RUNS'}
BACKPROP = {'name': 'BACKPROP', 'files': 'add_files {../GRASP_DSE/benchmarks/backprop/backprop.c}', 'top': 'set_top backprop', 'dict': 'open_project MOD_FIX_RUNS/BACKPROP_FIX_MOD_RUNS'}
GEMM = {'name': 'GEMM', 'files': 'add_files {./benchmarks/gemm/gemm.c}', 'top': 'set_top bbgemm', 'dict': 'open_project MOD_FIX_RUNS/GEMM_FIX_MOD_RUNS'}
GSM = {'name': 'GSM', 'files': 'add_files {../GRASP_DSE/benchmarks/gsm/gsm_add.c ../GRASP_DSE/benchmarks/gsm/gsm.c ../GRASP_DSE/benchmarks/gsm/gsm_lpc.c}', 'top': 'set_top Gsm_LPC_Analysis', 'dict': 'open_project MOD_FIX_RUNS/GSM_FIX_MOD_RUNS'}
KNN = {'name': 'KNN', 'files': 'add_files {../GRASP_DSE/benchmarks/knn/md.c}', 'top': 'set_top md_kernel', 'dict': 'open_project MOD_FIX_RUNS/KNN_FIX_MOD_RUNS'}
SHA = {'name': 'SHA', 'files': 'add_files {./benchmarks/sha/sha.c}', 'top': 'set_top sha_stream', 'dict': 'open_project MOD_FIX_RUNS/SHA_FIX_MOD_RUNS'}
STENCIL3D = {'name': 'STENCIL3D', 'files': 'add_files {./benchmarks/stencil3d/stencil.c}', 'top': 'set_top stencil3d', 'dict': 'open_project MOD_FIX_RUNS/STENCIL3D_FIX_MOD_RUNS'}
TRANS_FFT = {'name': 'TRANS_FFT', 'files': 'add_files {./benchmarks/transposed_fft/transposed_fft.c}', 'top': 'set_top fft1D_512', 'dict': 'open_project MOD_FIX_RUNS/STENCIL3D_FIX_MOD_RUNS'}

DICT_LIST = [GEMM, SHA, STENCIL3D, TRANS_FFT, ADPCM, BACKPROP, AES, KNN, GSM]
#DICT_LIST = [ADPCM, GEMM]

def verify_run_is_done(cwd, _dir, sol_number):
    is_done = False
    _path = os.path.join(cwd, _dir, f'solution_mod_{sol_number}')
    if Path(_path).is_dir():
        if Path(os.path.join(_path, 'impl/verilog/project.runs/impl_1')).is_dir():
            impl_path = os.path.join(_path, 'impl/verilog/project.runs/impl_1/')
            if Path(os.path.join(impl_path, 'bd_0_wrapper_power_routed.rpt')).is_file() and Path(os.path.join(impl_path, 'bd_0_wrapper_timing_summary_routed.rpt')).is_file() and Path(os.path.join(impl_path, 'bd_0_wrapper_utilization_placed.rpt')).is_file():
                if Path(os.path.join(impl_path, 'runme.log')).is_file():
                    with open(os.path.join(impl_path, 'runme.log'), 'r') as f:
                        lines = f.readlines()
                        for l in lines:
                            if l.find('INFO: [Common 17-1381] The checkpoint') != -1 and l.find('has been generated') != -1:
                                is_done = True
    return is_done

def run_paretto_runs(dir_tcl, dir_run, hls_only=False):
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
        if not verify_run_is_done(cwd, dir_run, sol_number):
            print(f'run {sol_number} not done yet!')
            with open(os.path.join(cwd, script_name), 'r') as f:
                lines = f.readlines()
                for i in range(len(lines)):
                    if lines[i].find('open_solution') != -1:
                        print(f'sol_number: {sol_number}')
                        if hls_only:
                            lines[i] = f'open_solution solution_hls_{sol_number}\n'
                        else:
                            lines[i] = f'open_solution solution_mod_{sol_number}\n'
                        #print(line)
            
            with open(os.path.join(cwd, script_name), 'w') as f:
                for line in lines:
                    f.write(line)
            subprocess.run(f'vitis_hls -f {script_name}', shell=True)
        else:
            print(f'run {sol_number} already dome! skipping...')

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

def run_missing_fix_runs(hls_dir, dest_dir, reports_dir):
    cwd = os.getcwd()
    if not Path(os.path.join(cwd, hls_dir)).is_dir():
        print(f'ERROR: hls_dir {hls_dir} not found!')
        return -1
    if not Path(os.path.join(cwd, dest_dir)).is_dir():
        print(f'ERROR: dest_dir {dest_dir} not found!')
        return -1 
    if not Path(os.path.join(cwd, reports_dir)).is_dir():
        print(f'ERROR: reports_dir {reports_dir} not found!')
        return -1 

    print('starting runs...')
    hls_exist = True
    for _dict in DICT_LIST:
        bench_name = _dict['name']
        current_dict = _dict['dict']
        current_top = _dict['top']
        current_files = _dict['files']
        print(f'starting {bench_name}...')
        hls_exist = True
        if not Path(os.path.join(cwd, dest_dir, bench_name)).is_dir():
            print(f'INFO: creating run directory for {bench_name}...')
            Path(os.path.join(cwd, dest_dir, bench_name)).mkdir()
        run_path = os.path.join(cwd, dest_dir, bench_name)

        if not Path(os.path.join(cwd, reports_dir, bench_name)).is_dir():
            print(f'INFO: creating report directory for {bench_name}...')
            Path(os.path.join(cwd, reports_dir, bench_name)).mkdir()
        rep_path = os.path.join(cwd, reports_dir, bench_name)

        if not Path(os.path.join(cwd, hls_dir, bench_name)).is_dir():
            print(f'ERROR: hls directory not found for {bench_name}! Skipping...')
            hls_exist = False
        hls_path = os.path.join(cwd, hls_dir, bench_name)

        if hls_exist:
            lines = []
            run_dict_index = -1
            files_index = -1
            main_func_index = -1
            i = 0
            with open(os.path.join(cwd, 'script.tcl'), 'r') as f:
                lines = f.readlines()
                for l in lines:
                    if l.find('open_project') != -1:
                        #print(f'open_project: {i}')
                        run_dict_index = i
                    if l.find('set_top') != -1:
                        #print(f'set_top: {i}')
                        main_func_index = i
                    if l.find('add_files') != -1:
                        #print(f'add_files: {i}')
                        files_index = i
                    i=i+1
            
            print('INFO: script reading done')
            with open(os.path.join(cwd, 'script.tcl'), 'w') as f:
                lines[run_dict_index] = f'{current_dict}\n'
                #print(f'current_dict')
                #print(current_dict)
                #print('########################################')
                lines[main_func_index] = f'{current_top}\n'
                #print(f'current_top')
                #print(current_top)
                #print('########################################')
                lines[files_index] = f'{current_files}\n'
                #print(f'current_files')
                #print(current_files)
                #print('########################################')
                i = 0
                for l in lines:
                    #print(l)
                    f.write(l)
                    #f.write('\n')
            print('INFO: script writing done')

            run_paretto_runs(hls_path, run_path, 0)
            print('INFO: finished run')
            copy_run_reports(run_path, rep_path, 0)
            print('INFO: finished report copying')

    print('INFO: finished all runs!')

def extract_rtl_files(src_dir, dest_dir, bench):
    print(f'starting verilog extraction of {bench}')
    cwd = os.getcwd()
    src_path = os.path.join(cwd, src_dir, bench)
    if not Path(src_path).is_dir():
        print(f'ERROR: source directory not found! Directory given: {src_path}')
        return -1
    
    dest_path = os.path.join(cwd, dest_dir, bench)

    runs = os.listdir(src_path)
    Path(dest_path).mkdir(exist_ok=True)

    for run in runs:
        if Path(os.path.join(src_path, run, 'syn/verilog')).is_dir():
            if not Path(os.path.join(dest_path, run, 'rtl')).is_dir() or (Path(os.path.join(dest_path, run, 'rtl')).is_dir() and len(os.listdir(os.path.join(dest_path, run, 'rtl'))) == 0):
                rtl_files = os.listdir(os.path.join(src_path, run, 'syn/verilog'))
                #os.makedirs(os.path.dirname(os.path.join(dest_path, run, 'rtl')), exist_ok=True)
                rtl_dir_path = os.path.join(dest_path, run, 'rtl')
                Path(rtl_dir_path).mkdir(parents=True, exist_ok=True)
                for rtl in rtl_files:
                    rtl_path = os.path.join(src_path, run, 'syn/verilog', rtl)
                    rtl_dest_path = os.path.join(dest_path, run, 'rtl', rtl)
                    
                    shutil.copy(rtl_path, rtl_dest_path)
            else:
                print(f'WARNING: non empty folder for solution {run} already exists. Skipping...')
        else:
            error_path = os.path.join(src_path, run, 'syn/verilog')
            print(f'ERROR: path not found! Path given: {error_path}')

def create_dataset_directory(_dir, _adb_name, _rtl_name, _dest_name):
    app_list = ['GEMM', 'GRAMSCHMIDT', 'GSM', 'KNN', 'SHA', 'STENCIL3D', 'TRANS_FFT'] #'ADPCM', 'AES', 'BACKPROP', 
    no_adb_dict = {}
    no_rtl_dict = {}
    cwd = os.getcwd()
    src_path = os.path.join(cwd, _dir)
    rtl_path = os.path.join(cwd, _dir, _rtl_name)
    adb_path = os.path.join(cwd, _dir, _adb_name)

    if not Path(src_path).is_dir():
        print(f'ERROR: specified dir {src_path} not found! Exiting...')
        return -1
    if not Path(rtl_path).is_dir():
        print(f'ERROR: specified rtl dir {rtl_path} not found! Exiting...')
        return -1
    if not Path(adb_path).is_dir():
        print(f'ERROR: specified adb dir {adb_path} not found! Exiting...')
        return -1

    dest_path = os.path.join(cwd, _dir, _dest_name)
    Path(dest_path).mkdir(parents=True, exist_ok=True)

    for app in app_list:
        print(f'Starting {app}...')
        app_path = os.path.join(dest_path, app)
        if not Path(app_path).is_dir():
            Path(app_path).mkdir(parents=True)

        filtered_path = os.path.join(src_path, f'filtered_{app.lower()}', app)
        sols = os.listdir(os.path.join(filtered_path))
        no_adbs = []
        no_rtl = []
        for sol in sols:
            if sol.find('_mod_') == -1:
                has_adbs = True
                has_rtl = True
                #filtered dataset files..
                sol_path = os.path.join(filtered_path, sol)
                dest_sol_path = os.path.join(dest_path, app, sol)
                shutil.copytree(os.path.join(sol_path, 'IRs'), os.path.join(dest_sol_path, 'IRs'), dirs_exist_ok=True)
                shutil.copytree(os.path.join(sol_path, 'reports'), os.path.join(dest_sol_path, 'reports'), dirs_exist_ok=True)
                shutil.copy(os.path.join(sol_path, f'{sol}.directive'), os.path.join(dest_sol_path, f'{sol}.directive'))
                shutil.copy(os.path.join(sol_path, f'{sol}_data.json'), os.path.join(dest_sol_path, f'{sol}_data.json'))

                Path(os.path.join(dest_sol_path, 'rtl')).mkdir(parents=True, exist_ok=True)
                Path(os.path.join(dest_sol_path, 'adb')).mkdir(parents=True, exist_ok=True)
            
                #adb files...
                if Path(os.path.join(src_path, _adb_name, app, sol, 'IRs')).is_dir():
                    adb_file_path = os.path.join(src_path, _adb_name, app, sol, 'IRs')
                    adb_files = os.listdir(adb_file_path)
                elif Path(os.path.join(src_path, _adb_name, app, sol, '.autopilot/db')).is_dir():
                    adb_file_path = os.path.join(src_path, _adb_name, app, sol, '.autopilot/db')
                    adb_files = os.listdir(adb_file_path)
                else:
                    has_adbs = False
                    first_path = os.path.join(src_path, _adb_name, app, sol, 'IRs')
                    second_path = os.path.join(src_path, _adb_name, app, sol, '.autopilot/db')
                    print(f'ERROR: adb path not found! Tried {first_path} and {second_path}')
                
                if has_adbs:
                    for adb in adb_files:
                        shutil.copy(os.path.join(adb_file_path, adb), os.path.join(dest_sol_path, 'adb', adb))
                else:
                    print(f'WARNING: no adb files for solution {sol} in benchmark {app}')
                    no_adbs.append(sol)
        
                #RTL files...
                if Path(os.path.join(src_path, _rtl_name, app, sol)).is_dir():
                    rtl_file_path = os.path.join(src_path, _rtl_name, app, sol, 'rtl')
                    rtl_files = os.listdir(rtl_file_path)
                else:
                    has_rtl = False
                    print(f'ERROR: RTL path not found! Path guiven: {rtl_file_path}')

                if has_rtl:
                    for rtl in rtl_files:
                        shutil.copy(os.path.join(rtl_file_path, rtl), os.path.join(dest_sol_path, 'rtl', rtl))
                else:
                    no_rtl.append(sol)
            else:
                print(f'INFO: mod solution {sol} skipped!')

        print(f'Finished benchmark {app}!\n')
        no_adb_dict[app] = no_adbs
        no_rtl_dict[app] = no_rtl

    print('Finished all benchmarks!')
    for key in no_adb_dict.keys():
        print(f'Missing adbs in {key}: {no_adb_dict[key]}')
        print(f'Missing rtl in {key}: {no_rtl_dict[key]}')

    print(f'\nResult is in path {dest_path}')
    print('Exiting...')


def gen_missing_adbs(_src, _dest):
    cwd = os.getcwd()

    gemm = ['solution166', 'solution66', 'solution67', 'solution68', 'solution69', 'solution71']
    rtl_gemm = ['solution71']
    sha = ['solution117', 'solution148', 'solution165', 'solution188', 'solution199', 'solution222', 'solution225', 'solution230', 'solution53', 'solution54', 'solution55', 'solution69', 'solution74', 'solution88', 'solution90']
    stencil3d = ['solution156', 'solution214', 'solution241', 'solution40', 'solution41', 'solution42', 'solution43', 'solution44']
    fft = ['solution107', 'solution133', 'solution144', 'solution146', 'solution150', 'solution153', 'solution159', 'solution162', 'solution167', 'solution169', 'solution177', 'solution182', 'solution183', 'solution184', 'solution187', 'solution196', 'solution200', 'solution201', 'solution218', 'solution226', 'solution229', 'solution230', 'solution232', 'solution236', 'solution238', 'solution249', 'solution253', 'solution255', 'solution256', 'solution263', 'solution276', 'solution277', 'solution323', 'solution75']
        
    missing_adbs = [gemm, sha, stencil3d, fft]

    src_path = os.path.join(cwd, _src)
    if not Path(src_path).is_dir():
        print(f'ERROR: specified source dir {src_path} not found! Exiting...')
        return -1

    dest_path = os.path.join(cwd, _dest)
    if not Path(dest_path).is_dir():
        print(f'ERROR: specified destination dir {dest_path} not found! Exiting...')
        return -1

    for app in missing_adbs:
        #setup
        print(f'starting {app}...')

        bench_name = DICT_LIST[app]['name']
        current_dict = DICT_LIST[app]['dict']
        current_top = DICT_LIST[app]['top']
        current_files = DICT_LIST[app]['files']

        run_dict_index = -1
        main_func_index = -1
        files_index = -1

        lines = []
        with open('script.tcl', 'r') as f:
            i = 0
            for l in lines:
                if l.find('open_project') != -1:
                    #print(f'open_project: {i}')
                    run_dict_index = i
                if l.find('set_top') != -1:
                    #print(f'set_top: {i}')
                    main_func_index = i
                if l.find('add_files') != -1:
                    #print(f'add_files: {i}')
                    files_index = i
                i=i+1

        

        for sol in app:
            solution_dict = []
            directs = []
            #extract directives
            with open(os.path.join(cwd, _src, app, sol, f'{sol}_data.json'), 'r') as jf:
                json_dict:dict = json.load(jf)
                solution_dict = json_dict['HlsSolution']['DirectiveTcl']

            for direct in solution_dict:
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
                    
                    directs.append(direct)

                if direct.find('set_directive_loop_merge') != -1:
                    directs.append(direct)

            with open('directives.tcl', 'w') as tcl:
                for d in directs:
                    tcl.write(d)
                    tcl.write('\n')

            subprocess.run(f'vitis_hls -f {script_name}', shell=True)
            print(f'finished run {sol}')

    print('finished all runs!')
            


if __name__ == '__main__':
    src_dir = input('source directory: ')
    dest_dir = input('destination directory: ')
    #bench = input('benchmark name: ')
    adb_name = input('adb directory name: ')
    rtl_name = input('rtl directory name: ')

    #extract_rtl_files(src_dir, dest_dir, bench)
    create_dataset_directory(src_dir, adb_name, rtl_name, dest_dir)
    #dir_tcl = input('tcl mod directory name: ')
    #dir_runs = input('run directory: ')
    #dir_report = input('report directory: ')
    #hls_s = input('hls only? : 1 or 0? ')

    # input_valid = False
    # hls = False
    # if int(hls_s) == 1:
    #     hls = True
    #     input_valid = True
    # elif int(hls_s) == 0:
    #     hls = False
    #     input_valid = True
    # else:
    #     input_valid = False

    # run_missing_fix_runs(dir_tcl, dir_runs, dir_report)
    #if input_valid:
    #    run_paretto_runs(dir_tcl, dir_runs, hls)
    #    copy_run_reports(dir_runs, dir_report, hls)
    #else:
    #print(type(int(hls_s)))
    #print(f'ERROR: hls option should be y or n (value assigned: {hls_s})! Exiting...')