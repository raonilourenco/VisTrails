import copy
import sys, os
import random
import logging
from vistrails.core.vistrail.controller import VistrailController as BaseController
from vistrails.core.modules.module_registry import get_module_registry
import json

goodbad = [True, False]
numtests = 10

def evaluate(x, formula):
	local = x
	logging.debug("local is: "+str(local))
	logging.debug("formula is: "+formula)
	ret = eval(formula)
	logging.debug("ret is "+str(ret))
	return ret


def loadtests(filename):
	fileicareabout = open(filename,"r")
	text = fileicareabout.readlines()
	fileicareabout.close()
	workflow = text[0]

	if (workflow != "null\n"):
		script,func = (workflow[:-1]).split(",")
		workflow = getattr(__import__(script), func)
	else:
		workflow = None
	formula = text[1]
	cost = text[2]
	cols = text[3][:-1].split(",")
	alllines = text[4:]


	allexperiments = []
	allresults = [] # experiments and their results

	for e in alllines:
		exp = (e[:-1]).split(",")
		allexperiments.append(exp)
  

	for e in allexperiments:
		x = copy.deepcopy(e)
		x.append(evaluate(e, formula))
		allresults.append(x)

	return [workflow,allexperiments,allresults,formula,cost,cols]

def load_runs(filename, input_keys):
	print('calling load run',filename)
	fileicareabout = open(filename,"r")
	alllines = fileicareabout.readlines()
	fileicareabout.close()

	allexperiments = []
	allresults = [] # experiments and their results

	for e in alllines:
		exp = []
		exp_dict = json.loads(e[:-1])
		for key in input_keys:
			exp.append(exp_dict[key].encode("utf-8"))
		exp.append(exp_dict['result'].encode("utf-8"))
		allexperiments.append(exp)
  		
  	for e in allexperiments:
		x = copy.deepcopy(e)
		x[-1] = eval(x[-1])
		allresults.append(x)

	return [allexperiments,allresults]

def record_run(moduleInfo,result):
	paramDict = {}
	vistrail_name = moduleInfo['locator'].name
	file_name = vistrail_name.replace('.vt','.adb')
	f = open(file_name,"a")
	reg = get_module_registry()
	pipeline = moduleInfo['controller'].current_pipeline
	sortedModules = sorted(pipeline.modules.iteritems(),
	                       key=lambda item: item[1].name)
	for mId, module in sortedModules:
	    if len(module.functions)>0:
	        for fId in xrange(len(module.functions)):
	            function = module.functions[fId]
	            desc = reg.get_descriptor_by_name('org.vistrails.vistrails.basic','OutputPort')
	            if module.module_descriptor is desc: continue
	            desc = reg.get_descriptor_by_name('org.vistrails.vistrails.basic','PythonSource')
	            if (module.module_descriptor is desc) and (function.name == 'source'): continue
	            if len(function.params)==0: continue
	            v = ', '.join([p.strValue for p in function.params])
	            paramDict[function.name] = str(v)
	            
	paramDict['result'] = str(result)              
	f.write(json.dumps(paramDict)+ '\n')
	f.close()
