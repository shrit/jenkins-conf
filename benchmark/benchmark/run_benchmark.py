'''
  @file run_benchmark.py
  @author Marcus Edel

  Perform the timing benchmark.
'''

import os, sys, inspect

# Import the util path, this method even works if the path contains
# symlinks to modules.
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(
  os.path.split(inspect.getfile(inspect.currentframe()))[0], '../util')))
if cmd_subfolder not in sys.path:
  sys.path.insert(0, cmd_subfolder)

from log import *
from system import *
from loader import * 
from parser import *

import argparse

'''
Show system informations. Are there no data available, the value is 'N/A'.
'''
def SystemInformation():
  
  Log.Info('CPU Model: ' + SystemInfo.GetCPUModel())
  Log.Info('Distribution: ' + SystemInfo.GetDistribution())
  Log.Info('Platform: ' + SystemInfo.GetPlatform())
  Log.Info('Memory: ' + SystemInfo.GetMemory())
  Log.Info('CPU Cores: ' + SystemInfo.GetCPUCores())

'''
Normalize the dataset name. If the dataset is a list of datasets, take the first
dataset as name. If necessary remove characters like '.', '_'.

@para dataset - Dataset file or a list of datasets files.
@return Normalized dataset name.
'''
def NormalizeDatasetName(dataset):
  if  not isinstance(dataset, basestring):
    return os.path.splitext(os.path.basename(dataset[0]))[0].split('_')[0]
  else:
    return os.path.splitext(os.path.basename(dataset))[0].split('_')[0]

'''
Add all rows from a given matrix to a given table.

@para matrix - 2D array contains the row.
@para table - Table in which the rows are inserted.
@return Table with the inserted rows.
'''
def AddMatrixToTable(matrix, table):
  for row in matrix:
    table.append(row)
  return table

'''
Count all datasets to determine the dataset size.

@para libraries - Contains the Dataset List.
@return Dataset count.
'''
def CountLibrariesDatasets(libraries):
  datasetList = []
  for libary in libraries:
    for dataset in libary[1]:
      name = NormalizeDatasetName(dataset)
      if not name in datasetList:
        datasetList.append(name)

  return len(datasetList)

'''
Search the correct row to insert the new data. We look at the left column for
a free place or for the matching name.

@para dataMatrix - In this Matrix we search for the right position.
@para datasetName - Name of the dataset.
@para datasetCount - Maximum dataset count.
'''
def FindRightRow(dataMatrix, datasetName, datasetCount):
  for row in range(datasetCount):
    if (dataMatrix[row][0] == datasetName) or (dataMatrix[row][0] == "-"):
      return row

'''
Start the main benchmark routine. The method shows some DEBUG information and 
prints a table with the runtime information.

@para configfile - Start the benchmark with this configuration file.
'''
def Main(configfile): 

  # Read Config.
  config = Parser(configfile, verbose=False)
  streamData = config.StreamMerge()

  # Iterate through all libraries.
  for method, sets in streamData.items():
    Log.Info("Method: " + method)    
    for options, libraries in sets.items():
      Log.Info('Options: ' + (options if options != '' else 'None'))

      # Create the Table.
      table = []
      header = ['']
      table.append(header)

      # Count the Datasets.
      datasetCount = CountLibrariesDatasets(libraries)

      # Create the matrix which contains the time and dataset informations.
      dataMatrix = [['-' for x in xrange(len(libraries) + 1)] for x in 
          xrange(datasetCount)] 

      col = 1
      for libary in libraries:
        name = libary[0]
        datsets = libary[1]
        trials = libary[2]
        script = libary[3]

        Log.Info("Libary: " + name)
        header.append(name)

        # Load script.
        module = Loader.ImportModuleFromPath(script)
        methodCall = getattr(module, method)       

        for dataset in datsets:  
          datasetName = NormalizeDatasetName(dataset)          
          row = FindRightRow(dataMatrix, datasetName, datasetCount)      

          dataMatrix[row][0] = NormalizeDatasetName(dataset)
          Log.Info("Dataset: " + dataMatrix[row][0])        

          time = 0
          for trial in range(trials + 1):
            instance = methodCall(dataset, verbose=False)
            if trial > 0:
              time += instance.RunMethod(options);

          # Set time.
          dataMatrix[row][col] = "{0:.6f}".format(time / trials)
          row += 1
        col += 1

      # Show results in a table.
      Log.Notice("\n\n")
      Log.PrintTable(AddMatrixToTable(dataMatrix, table))
      Log.Notice("\n\n")

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="""Perform the benchmark with the
      given config.""")
  parser.add_argument('-c','--config', help='Configuration file name.', 
      required=True)

  args = parser.parse_args()

  if args:
    SystemInformation()
    Main(args.config)