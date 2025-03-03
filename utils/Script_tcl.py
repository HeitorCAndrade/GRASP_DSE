from string import Template

def generateScript(cFile, prjFile, benchmark, sol = 'solution1'):
     filesSeparatedBySpace = ""
     for file in cFile:
          filesSeparatedBySpace = (filesSeparatedBySpace+ file + " ")
     subtituicoes = {
     'fun_top': prjFile,
     'arq_cpp': filesSeparatedBySpace, 
     'benchmark_path': "DATASETS/"+benchmark,
     'solution': sol
     }


     with open('./domain/script.tcl.txt', 'r') as f:
          src = Template(f.read())
     result = src.substitute(subtituicoes)

     # open text file
     text_file = open('./domain/script.tcl' , 'w')
 
     # write string to file
     text_file.write(result)

     # close file
     text_file.close()


def generateReportScript(benchname, sol, area, power, timing):
     report_area_command = ''
     report_power_command = ''
     report_timing_command = ''

     if area:
          report_area_command = f'report_utilization -f ./DATASETS/{benchname}/{sol}/impl/verilog/project.runs/impl/generated_utilization.rpt'
     if power:
          report_power_command = f'report_power -f ./DATASETS/{benchname}/{sol}/impl/verilog/project.runs/impl/generated_power.rpt'
     if timing:
          report_timing_command = f'report_timing_summary -f ./DATASETS/{benchname}/{sol}/impl/verilog/project.runs/impl/generated_timing_sum.rpt'

     subtituicoes = {
     'benchmark': f'{benchname}',
     'solution': f'{sol}'
     }

     with open('./domain/generate_report.tcl.txt', 'r') as f:
          src = Template(f.read())
     result = src.substitute(subtituicoes)

     # open text file
     text_file = open('./domain/generate_report.tcl' , 'w')
 
     # write string to file
     text_file.write(result)

     # close file
     text_file.close()