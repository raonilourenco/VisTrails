import math
import random
import copy
import sys, os
import tree
import Queue
import logging
from utils import load_runs, evaluate, goodbad, numtests,load_combinatorial

class AutoDebug(object):

    def determinenodepurity(self, node, path):
        print( "path is: "+str(path))
        if node.results is None:
            pathfalse = copy.deepcopy(path)
            pathfalse.append((node.col,node.value,False))
            path.append((node.col,node.value,True))
            self.determinenodepurity(node.fb,pathfalse)
            self.determinenodepurity(node.tb,path)
        elif (len(node.results.items())>1):
            mixedlist.append(path)
        elif(node.results.items()[0][0]):
            self.puregoodlist.append(path)
        else:
            self.purebadlist.append(path)
            
    def findshoertestpaths(self, node):
        q = Queue.Queue()
        q.put((node,[]))
        puregoodpath = None
        purebadpath = None
        while (not q.empty()) and ((puregoodpath is None) or (purebadpath is None)):
            current = q.get()
            if current[0].results is None:
                q.put((current[0].fb,current[1]+[(current[0].col,current[0].value,False)]))
                q.put((current[0].tb,current[1]+[(current[0].col,current[0].value,True)]))
            elif (len(current[0].results.items())>1):
                continue
            elif(current[0].results.items()[0][0]) and (puregoodpath is None):
                puregoodpath = current[1]
            elif (not current[0].results.items()[0][0]) and (purebadpath is None):
                purebadpath = current[1]
        return [puregoodpath, purebadpath]

    def manufacturetests(self, moralflag, alist):
        rebuild = False; 
        print("a list: "+str(alist))
        if (moralflag == 'bad'):
            for path in alist:
                print("at step 2.5, path: "+str(path))
                z = self.assembletests('bad', path)
                if z: 
                    print("believeddecisive for bad: "+str(path))
                else:
                    rebuild = True
         
        if (moralflag == 'good'):
            for path in alist:
                print( "at step 3.5, path: "+str(path))
                z = self.assembletests('good', path)
                if z: 
                    print( "believeddecisive for good: "+str(path))
                else:
                    rebuild = True
        return rebuild
        
        
    def assembletests(self, moralflag, path):
        outlist = []
        myarrtrans = zip(*self.allexperiments)
        
        
        for j in range(len(self.cols) - 1):
            y = set(myarrtrans[j])
            print( "y is: "+str(y))
            for index,value,flag in [tup for tup in path if tup[0] == j]:
                if flag:
                    y = {value}
                else:
                    y = y - {value}
            outlist.append(list(y))
                
                
       
        print("in assembletests, outlist is: "+str(outlist))
        # Now just choose random values from these lists to generate experiments
        experiments = []
        costs = []
        experiments = []
        for i in range(numtests):
           x = []
           for mylist in outlist:
              x.append(random.choice(mylist))
           if (x not in experiments) and (x not in [e[:-1] for e in self.allexperiments]):
              print("marked to call workflow")
              experiments.append(x)
              costs.append(evaluate(x,self.cost))
           
              
        print("experiments are: "+str(experiments))

        # Executing experiments in ascending order of costs

        indices = [t[0] for t in sorted(enumerate(costs), key = lambda x: x[1])]
        for i in indices:
            e = experiments[i]
            e = self.workflow(e) 
            # use experiments as long as labels so far are unambiguous
            self.allexperiments.append(e)
            x = copy.deepcopy(e)
            x[-1] = eval(e[-1])
            self.allresults.append(x)
            if ((moralflag == 'good') and (x[-1] == goodbad[1])) or ((moralflag == 'bad') and (x[-1] == goodbad[0])) :
                return False
        return True


    def run(self, pipeline, input_dict):

        self.my_pipeline = pipeline
        self.my_inputs = input_dict.keys()
        self.my_outputs = pipeline.outputs
        num_initial_tests = 1
        for param in self.my_inputs:
          num_initial_tests *= len(input_dict[param])
        self.allexperiments,self.allresults = load_runs(pipeline.controller.vistrail.locator.name.replace(".vt",".adb"),self.my_inputs)
        print("allresults is: "+str(self.allresults))
        print("Debug", "Initial Experiments")
        if len(self.allexperiments) < (num_initial_tests/10):
            print("Debug", "load_combinatorial(input_dict)")        
            for d in load_combinatorial(input_dict):
              exp = []
              my_kwargs = {}
              for param in self.my_inputs:
                  value = d[param]
                  exp.append(value)
                  my_kwargs[param] = value
              try:
                print("Executing",str(my_kwargs))
                print("From dict",str(d))
                result = self.my_pipeline.execute(**my_kwargs)
                print("Executed")
                for output in self.my_outputs:
                  exp.append(str(result.output_port(output)))
              except:
                print("Error")
                exp.append(str(False))
              self.allexperiments.append(exp)
            print("Debug", "allexperiments")
            for e in self.allexperiments:
                x = copy.deepcopy(e)
                x[-1] = eval(x[-1])
                self.allresults.append(x)
    
        
        


        self.cols = self.my_inputs + self.my_outputs
        rebuild = True
        count = 0
        while rebuild:
            rebuild = False
            print("rebuild")
            print("allresults is: "+str(self.allresults))
            print("allexperiments are: "+str(self.allexperiments))
            t = tree.build(self.allresults, cols=self.cols)
            print("built")
            filename = "tree"+str(count)+".jpeg"
            tree.draw_tree(t, jpeg=filename)
            goodpath, badpath = self.findshoertestpaths(t)
            print("paths")
            rebuild = rebuild or self.manufacturetests('good', [goodpath])
            rebuild = rebuild or self.manufacturetests('bad', [badpath])
            print(str(len(self.allexperiments))+" experiments so far")
            count += 1

        self.puregoodlist = []
        self.purebadlist = []
        self.mixedlist = []
        t = tree.build(self.allresults, cols=self.cols)
        tree.draw_tree(t)
        self.determinenodepurity(t,[])
        self.manufacturetests('good', self.puregoodlist)
        self.manufacturetests('bad', self.purebadlist)

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
        self.puregoodlist = []
        self.purebadlist = []
        self.mixedlist = []
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
   



