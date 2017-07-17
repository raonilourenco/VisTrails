#!/usr/bin/env python
# 
# This program designs a strategy for determining future tests.
# It simulates the results of a formula and determines the critical
# variables. 
# To change the experiment, simply change the initialexperiments and/or
# formula in the DATA section.
# The program finds the variables that either causes the output of
# the simulation to be True  (here represented as 'good') or to be False
# (here represented as 'bad').
# A typical output might be: 
# believeddecisive is:  [[0, 'good', 2], [0, 'bad', 1], [0, 'bad', 3]]
# which means that if variable 0 has the value of 2, then the output of 
# the simulation will be True, if 1 or 3 then False. 

# The algorithm is simpler than a decision tree.
# determinepurity looks for the values of each variable that 
# result in a 'good' output and those that result in a 'bad' output
# in the experiments so far.
# manufacturetests takes candidate guesses (e.g. if variable 2 is 3 then
# the output will be good) and tries to determine whether that is true. 
# All the work to do that is in assembletests.

# The program is seeded with a set of initial experiments that consists
# of vectors of integers of length k (all the same length but k can be
# arbitrary). The formula applies to such vectors where index 0 is the first
# element of each vector.

# To use this in real life: assembletests currently
# generates test cases and calls evaluate. Instead, it will be necessary
# to write the tests to an external file and then call some workflow.
# At the end, the workflow must return True or False for each test
# and assembletests reads that in to allresults.


import math
import random
import copy
import sys, os # os.system(command)
import logging
from utils import loadtests, evaluate, goodbad, numtests

#logging.basicConfig(format='%(levelname)s:%(message)s', level=print)


# Given a matrix myarr and a target vector mytarg,
# determine for each column of the matrix the puregood values
# the purebad values and the mixed ones
# goodbad[0] is the good value and goodbad[1] is the bad value
def determinepurity(myarr, mytarg):
   myarrtrans = zip(*myarr) # transpose it
   puregoodlist =[]
   purebadlist =[]
   mixedlist =[]
   for a in myarrtrans:
     mygood = set([a[i] for i in range(len(mytarg)) if mytarg[i] == goodbad[0]])
     mybad = set([a[i] for i in range(len(mytarg)) if mytarg[i] == goodbad[1]])
     mymixed = mygood & mybad
     mypuregood = mygood - mybad
     mypurebad = mybad - mygood
     puregoodlist.append(list(mypuregood))
     purebadlist.append(list(mypurebad))
     mixedlist.append(list(mymixed))
   return [puregoodlist, purebadlist, mixedlist]

# Given the puregood, purebad, mixed values of each column,
# manufacture new test cases.
# take an index and a moralflag and determine if there is purity.
# If the candidate index appears to be pure, then puts it into 
# believeddecisive [variableindex, moralflag, value]
def manufacturetests(i, moralflag, alllists):
   global believeddecisive
   (puregoodlist, purebadlist, mixedlist) = alllists
   print("manufacturetests at index: "+str(i))
   print("puregoodlist: "+str(puregoodlist))
   print("purebadlist: "+str(purebadlist))
   if (moralflag == 'bad') and (0 < len(purebadlist[i])): 
       for j in range(len(purebadlist[i])):
         print("at step 2.5, j: "+str(j))
         z = assembletests(i, 'bad', purebadlist[i][j], alllists)
       return i
   if (moralflag == 'good') and (0 < len(puregoodlist[i])):
       for j in range(len(puregoodlist[i])):
         print("at step 3.5, j: "+str(j))
         z = assembletests(i, 'good', puregoodlist[i][j], alllists)
       return i
   
# assembletests creates tests for index testindex either good or bad 
# If the test is for good, then it takes val at location testindex
# and then it takes values from bad or mixed for all other indexes.
# It takes at a maximum numtests such tests.
def assembletests(testindex, moralflag, val, alllists):
   global believeddecisive
   (puregoodlist, purebadlist, mixedlist) = alllists
   outlist = []
   if moralflag == 'good':
     for j in range(len(purebadlist)):
       if j == testindex:
         outlist.append([val])
       else:
         print("looking for a decisive good")
         print("purebadlist[j] is: "+str(purebadlist[j]))
         print("mixedlist[j] is: "+str(mixedlist[j]))
         print("j is: "+str(j))

         y = []
         for z in purebadlist[j]:
           y.append(z)
         for z in mixedlist[j]:
           y.append(z)
         if 0 == len(y):
           y = puregoodlist[j]
           print("added a member of good for "+str(j)+"  which might skew the results for "+str(testindex)+", "+str(val))
         print("moralflag is good, j is: "+str(j)+" y is: "+str(y))
         outlist.append(y)
   if moralflag == 'bad':
     for j in range(len(puregoodlist)):
       if j == testindex:
         outlist.append([val])
       else:
         print("looking for a decisive bad")
         print("puregoodlist[j] is: "+str(puregoodlist[j]))
         print("mixedlist[j] is: "+str(mixedlist[j]))
         y = []
         for z in puregoodlist[j]:
           y.append(z)
         for z in mixedlist[j]:
           y.append(z)
         if 0 == len(y):
           y = purebadlist[j]
           print("added a member of bad for "+str(j)+"  which might skew the results for "+str(testindex)+", "+str(val))
         print("moralflag is bad, j is: "+str(j)+" y is: "+str(y))
         outlist.append(y)
   print("in assembletests, outlist is: "+str(outlist))
   # Now just choose random values from these lists to generate experiments
   experiments = []
   costs = []
   for i in range(numtests):
     x = []
     for mylist in outlist:
       x.append(random.choice(mylist))
     if (x not in expers):
          expers.append(x)
	  experiments.append(x)
          costs.append(evaluate(x,cost))
          
   print("experiments are: "+str(experiments))
  # Executing experiments in ascending order of costs
   allrets = []
   indices = [t[0] for t in sorted(enumerate(costs), key = lambda x: x[1])]
   if workflow:
      for i in indices:
         e = experiments[i]
         e = workflow(e)
         print("e is: "+str(e)) 
         if (1 >= len(set(allrets))) and (e): 
           # use experiments as long as labels so far are unambiguous
           allexperiments.append(e)
           x = copy.deepcopy(e)
           x.append(evaluate(e, formula))
           allrets.append(x[-1])
           allresults.append(x)
   print("allrets are: "+str(allrets)+" # "+str(len(set(allrets))))
   if (1 == len(set(allrets))):
    if (moralflag == 'bad') and (allrets[0] == goodbad[1]):
      believeddecisive.append([testindex, 'bad', val])
    if (moralflag == 'good') and (allrets[0] == goodbad[0]):
      believeddecisive.append([testindex, 'good', val])
   if (0 == len(set(allrets))):
      believeddecisive.append([testindex, moralflag, val])
   return True

   
#----------------------------------------------------------------------------------------------------------------
def run(pipeline, input_dict):
  global my_kwargs
  global my_inputs
  global my_outputs
  global my_pipeline 
  my_pipeline = pipeline
  my_inputs = pipeline.inputs
  my_outputs = pipeline.outputs
  for i in range(8):
      exp = []
      my_kwargs = {}
      for param in my_inputs:
          value = random.choice(input_dict[param])
          exp.append(value)
          my_kwargs[param] = value
      result = my_pipeline.execute(**my_kwargs)
      for output in my_outputs:
          exp.append(str(result.output_port(output)))
      allexperiments.append(exp)

  for e in allexperiments:
      x = copy.deepcopy(e)
      x.append(evaluate(e, formula))
      allresults.append(x)


  cols = my_inputs + my_outputs

  #----------------------------------------------------------------------------------------------------------------
  #workflow,allexperiments,allresults,formula,cost,cols = loadtests("classification_traces.txt")


  print("allresults is: "+str(allresults))
  # Initially we prefer indices with few distinct values and less impure  
  expers = [allresults[j][:-2] for j in range(len(allresults))]
  print("expers is: "+str(expers))
  rets = [allresults[j][-1] for j in range(len(allresults))]
  print("rets is: "+str(rets))
  myalllists = determinepurity(expers, rets)


  #ordering the indices
  translist = zip(*myalllists)
  pairs = [(len(tup[0])+len(tup[1])+len(tup[2]),len(tup[2])) for tup in translist]
  tuples= sorted(enumerate(pairs), key = lambda x: x[1])
  indices = [t[0] for t in tuples]

  manufacture = True
  while manufacture:
    manufacture = False
    for i in indices:
      
      x = manufacturetests(i, 'good', myalllists)
      print("after manufacturetests for good up to index: "+str(x))
      print("believeddecisive is: "+str(believeddecisive))
      x = manufacturetests(i, 'bad', myalllists)
      print("after manufacturetests for bad up to index: "+str(x))
      print("believeddecisive is: "+str(believeddecisive))
      print("length of all experiments is: "+str(len(allexperiments)))
      
      if not (i == indices[-1]):
          expers = [allresults[j][:-2] for j in range(len(allresults))]
          print("expers is: "+str(expers))
          rets = [allresults[j][-1] for j in range(len(allresults))]
          print("rets is: "+str(rets))
          myalllists = determinepurity(expers, rets)

          #ordering the indices
          translist = zip(*myalllists)
          pairs = [(len(tup[0])+len(tup[1])+len(tup[2]),len(tup[2])) for tup in translist]
          tuples= sorted(enumerate(pairs), key = lambda x: x[1])
          newindices = [t[0] for t in tuples]
      
      if not (newindices == indices):
          manufacture = True
          indices = newindices
          continue
  return believeddecisive



def run_workflow(parameter_list):
  for i in range(len(parameter_list)):
      my_kwargs[my_inputs[i]] = parameter_list[i]
  result = my_pipeline.execute(**my_kwargs)
  for output in my_outputs:
      parameter_list.append(str(result.output_port(output)))
  return parameter_list

allexperiments = []
allresults = []
formula = '(local[3]>\'0.5\')'
cost = '1'
cols = []
believeddecisive = []
workflow = run_workflow
expers = []
myalllists = []
rets = []
my_kwargs = {}
my_inputs = []
my_outputs = []
my_pipeline = None
    
