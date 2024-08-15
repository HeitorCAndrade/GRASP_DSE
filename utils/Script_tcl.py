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
     