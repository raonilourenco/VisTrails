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


class AutoDebug(object):


  # Given a matrix myarr and a target vector mytarg,
  # determine for each column of the matrix the puregood values
  # the purebad values and the mixed ones
  # goodbad[0] is the good value and goodbad[1] is the bad value
  def determinepurity(self, myarr, mytarg):
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
  def manufacturetests(self, i, moralflag, alllists):
     global believeddecisive
     (puregoodlist, purebadlist, mixedlist) = alllists
     print("manufacturetests at index: "+str(i))
     print("puregoodlist: "+str(puregoodlist))
     print("purebadlist: "+str(purebadlist))
     if (moralflag == 'bad') and (0 < len(purebadlist[i])): 
         for j in range(len(purebadlist[i])):
           print("at step 2.5, j: "+str(j))
           z = self.assembletests(i, 'bad', purebadlist[i][j], alllists)
         return i
     if (moralflag == 'good') and (0 < len(puregoodlist[i])):
         for j in range(len(puregoodlist[i])):
           print("at step 3.5, j: "+str(j))
           z = self.assembletests(i, 'good', puregoodlist[i][j], alllists)
         return i
     
  # assembletests creates tests for index testindex either good or bad 
  # If the test is for good, then it takes val at location testindex
  # and then it takes values from bad or mixed for all other indexes.
  # It takes at a maximum numtests such tests.
  def assembletests(self, testindex, moralflag, val, alllists):
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
       if (x not in self.expers):
            self.expers.append(x)
            experiments.append(x)
            costs.append(evaluate(x,self.cost))
            
     print("experiments are: "+str(experiments))
    # Executing experiments in ascending order of costs
     allrets = []
     indices = [t[0] for t in sorted(enumerate(costs), key = lambda x: x[1])]
     if self.workflow:
        for i in indices:
           e = experiments[i]
           e = self.workflow(e)
           print("e is: "+str(e)) 
           if (1 >= len(set(allrets))) and (e): 
             # use experiments as long as labels so far are unambiguous
             self.allexperiments.append(e)
             x = copy.deepcopy(e)
             x[-1] = eval(e[-1])
             allrets.append(x[-1])
             self.allresults.append(x)
     print("allrets are: "+str(allrets)+" # "+str(len(set(allrets))))
     if (1 == len(set(allrets))):
      if (moralflag == 'bad') and (allrets[0] == goodbad[1]):
        self.believeddecisive.append([testindex, 'bad', val])
      if (moralflag == 'good') and (allrets[0] == goodbad[0]):
        self.believeddecisive.append([testindex, 'good', val])
     if (0 == len(set(allrets))):
        self.believeddecisive.append([testindex, moralflag, val])
     return True

     
  #----------------------------------------------------------------------------------------------------------------
  def run(self, pipeline, input_dict):
    self.my_pipeline = pipeline
    self.my_inputs = input_dict.keys()
    self.my_outputs = pipeline.outputs
    num_initial_tests = 1
    for param in self.my_inputs:
      num_initial_tests *= len(input_dict[param])
    for i in range(10):
        exp = []
        my_kwargs = {}
        for param in self.my_inputs:
            value = random.choice(input_dict[param])
            exp.append(value)
            my_kwargs[param] = value
        try:
          result = self.my_pipeline.execute(**my_kwargs)
          for output in self.my_outputs:
            exp.append(str(result.output_port(output)))
        except:
          exp.append(str(False))
        self.allexperiments.append(exp)

    for e in self.allexperiments:
        x = copy.deepcopy(e)
        x[-1] = eval(e[-1])
        self.allresults.append(x)


    self.cols = self.my_inputs + self.my_outputs

    #----------------------------------------------------------------------------------------------------------------
    #workflow,allexperiments,allresults,formula,cost,cols = loadtests("classification_traces.txt")


    print("allresults is: "+str(self.allresults))
    # Initially we prefer indices with few distinct values and less impure  
    self.expers = [self.allresults[j][:-1] for j in range(len(self.allresults))]
    print("expers is: "+str(self.expers))
    self.rets = [self.allresults[j][-1] for j in range(len(self.allresults))]
    print("rets is: "+str(self.rets))
    self.myalllists = self.determinepurity(self.expers, self.rets)


    #ordering the indices
    translist = zip(*self.myalllists)
    pairs = [(len(tup[0])+len(tup[1])+len(tup[2]),len(tup[2])) for tup in translist]
    tuples= sorted(enumerate(pairs), key = lambda x: x[1])
    indices = [t[0] for t in tuples]
    newindices = indices

    manufacture = True
    while manufacture:
      manufacture = False
      for i in indices:
        
        x = self.manufacturetests(i, 'good', self.myalllists)
        print("after manufacturetests for good up to index: "+str(x))
        print("believeddecisive is: "+str(self.believeddecisive))
        x = self.manufacturetests(i, 'bad', self.myalllists)
        print("after manufacturetests for bad up to index: "+str(x))
        print("believeddecisive is: "+str(self.believeddecisive))
        print("length of all experiments is: "+str(len(self.allexperiments)))
        
        if not (i == indices[-1]):
            self.expers = [self.allresults[j][:-1] for j in range(len(self.allresults))]
            print("expers is: "+str(self.expers))
            rets = [self.allresults[j][-1] for j in range(len(self.allresults))]
            print("rets is: "+str(self.rets))
            self.myalllists = self.determinepurity(self.expers, self.rets)

            #ordering the indices
            translist = zip(*self.myalllists)
            pairs = [(len(tup[0])+len(tup[1])+len(tup[2]),len(tup[2])) for tup in translist]
            tuples= sorted(enumerate(pairs), key = lambda x: x[1])
            newindices = [t[0] for t in tuples]
        
        if not (newindices == indices):
            manufacture = True
            indices = newindices
            continue
    return self.believeddecisive



  def workflow(self, parameter_list):
    for i in range(len(parameter_list)):
        self.my_kwargs[self.my_inputs[i]] = parameter_list[i]
    try:
      result = self.my_pipeline.execute(**my_kwargs)
      for output in self.my_outputs:
        parameter_list.append(str(result.output_port(output)))
    except:
      parameter_list.append(str(False))
    return parameter_list
  
  def __init__(self):

    self.allexperiments = []
    self.allresults = []
    self.cost = '1'
    self.cols = []
    self.believeddecisive = []
    self.expers = []
    self.myalllists = []
    self.rets = []
    self.my_kwargs = {}
    self.my_inputs = []
    self.my_outputs = []
    self.my_pipeline = None
      
