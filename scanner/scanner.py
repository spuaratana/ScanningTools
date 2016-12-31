import xml.etree.ElementTree as ET
import os
import importlib
from itertools import *
from tabulate import tabulate
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-c", "--checkpointindex", action="store", type="int", dest="checkpointindex", default=0)
parser.add_option("-s", "--sort", action="store_true", dest="sort", default=False)
parser.add_option("-e", "--evalmodule", action="store", type="string", dest="evalmodule", default="")
parser.add_option("-n", "--numsort", action="store", type="int", dest="numsort", default=100)
parser.add_option("-f", "--formatfile", action="store", type="string", dest="formatfile", default="ckpt")
parser.add_option("-v", "--varfile", action="store", type="string", dest="varfile", default="")
[options, args] = parser.parse_args()
checkpointindex = options.checkpointindex
sort = options.sort
evalmodule = options.evalmodule
formatfile = options.formatfile
numsort = options.numsort
varfile = options.varfile

# Get tree root
tree = ET.parse(varfile)
root = tree.getroot()
files = root.find('files')
# print(ET.dump(files))

# Get relevant files
workingdir = files.find('workingdir').text
pythonmain = files.find('pythonmain').text
outputfile = files.find('outputfile').text
logfilename = files.find('logfilename').text

# Extract parameter list
parameters = root.find('parameters')
num_parameters = len(parameters)
parameters_list = [[] for l in range(num_parameters)]
parameters_name = []
for i in range(num_parameters):
    parameters_name.append(parameters[i].get('name'))
    for j in range(len(parameters[i])):
        parameters_list[i].append(parameters[i][j].text)

# Cartesian product of parameters
combinations_list = list(product(*parameters_list))

# Create command lists
argument_list = []
for index,combination_list in enumerate(combinations_list):
    command = "python ./" + pythonmain
    for j in range(num_parameters):
        command = command + " --" + parameters_name[j] + " " + combination_list[j]
    logfile = logfilename + "/logfile" + str(index) + '.txt'
    command = command + " -w " + logfilename + "/savedmodel" + str(index) + "." + formatfile + " > " + logfile
    argument_list.append(command)
    # print(command)

# Run command and save outputs
checkpointfile = logfilename + "/checkpointfile.txt"
if not os.path.exists(logfilename):
    os.makedirs(logfilename)

latest_index = 0
for index,argument in enumerate(argument_list):
    if (index >= checkpointindex):
        print("Running " + str(index) + " out of " + str(len(argument_list)-1))
        exit_code  = os.system(argument)
        if exit_code!= 0:
            f = open(checkpointfile, 'w')
            print >>f, "checkpoint index " + str(index)
            f.close()
            break
        else:
            latest_index = index

# Sort if run all combinations successfully
if (sort and latest_index == len(argument_list)-1):
    print("Sorting")
    try:
        evalmod = importlib.import_module(evalmodule)
    except IOError:
        print("Cannot find evalmodule for output file")
    score_list = []
    for index in range(len(argument_list)):
        logfile = logfilename + "/logfile" + str(index) + '.txt'
        score = evalmod.eval_output(logfile)
        score_list.append(score)

    sortedindices = sorted(range(len(score_list)),key=lambda k:score_list[k],reverse=True)
    output_list = []
    output_list.append(("Score","Indices") + tuple(parameters_name))
    with open(outputfile, 'w') as f:
        for i in range(min(len(argument_list),numsort)):
            output_list.append((score_list[sortedindices[i]],sortedindices[i])+tuple(combinations_list[sortedindices[i]]))
        print >>f,tabulate(output_list)
        f.close()
        print("Done, result shown in " + outputfile)
