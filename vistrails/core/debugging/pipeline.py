from vistrails.core.modules.module_registry import get_module_registry


class Pipeline(object):
    """This class represents a single Pipeline.

    It doesn't have a controller.
    """
    vistrail = None
    version = None
    _inputs = None
    _outputs = None
    _html = None

    def __init__(self, pipeline=None, vistrail=None):
        
        if pipeline is None:
            self.pipeline = _Pipeline()
        elif isinstance(pipeline, _Pipeline):
            self.pipeline = pipeline
        elif isinstance(pipeline, basestring):
            raise TypeError("Pipeline was constructed from %r.\n"
                            "Use load_pipeline() to get a Pipeline from a "
                            "file." % type(pipeline).__name__)
        else:
            raise TypeError("Pipeline was constructed from unexpected "
                            "argument type %r" % type(pipeline).__name__)
        if vistrail is not None:
            if (isinstance(vistrail, tuple) and len(vistrail) == 2 and
                    isinstance(vistrail[0], Vistrail)):
                self.vistrail, self.version = vistrail
            else:
                raise TypeError("Pipeline got unknown type %r as 'vistrail' "
                                "argument" % type(vistrail).__name__)

    @property
    def modules(self):
        for module in self.pipeline.module_list:
            yield Module(descriptor=module.module_descriptor,
                         module_id=module.id,
                         pipeline=self)

    def execute(self, *args, **kwargs):
        """Execute the pipeline.

        Positional arguments are either input values (created from
        ``module == value``, where `module` is a Module from the pipeline and
        `value` is some value or Function instance) for the pipeline's
        InputPorts, or Module instances (to select sink modules).

        Keyword arguments are also used to set InputPort by looking up inputs
        by name.

        Example::

           input_bound = pipeline.get_input('higher_bound')
           input_url = pipeline.get_input('url')
           sinkmodule = pipeline.get_module(32)
           pipeline.execute(sinkmodule,
                            input_bound == vt.Function(Integer, 10),
                            input_url == 'http://www.vistrails.org/',
                            resolution=15)  # kwarg: only one equal sign
        """
        sinks = set()
        inputs = {}

        reg = get_module_registry()
        InputPort_desc = reg.get_descriptor_by_name(
                get_vistrails_basic_pkg_id(),
                'InputPort')

        # Read args
        for arg in args:
            if isinstance(arg, ModuleValuePair):
                if arg.module.id in inputs:
                    raise ValueError(
                            "Multiple values set for InputPort %r" %
                            get_inputoutput_name(arg.module))
                if not reg.is_descriptor_subclass(arg.module.module_descriptor,
                                                  InputPort_desc):
                    raise ValueError("Module %d is not an InputPort" %
                                     arg.module.id)
                inputs[arg.module.id] = arg.value
            elif isinstance(arg, Module):
                sinks.add(arg.module_id)

        # Read kwargs
        for key, value in kwargs.iteritems():
            key = self.get_input(key)  # Might raise KeyError
            if key.module_id in inputs:
                raise ValueError("Multiple values set for InputPort %r" %
                                 get_inputoutput_name(key.module))
            inputs[key.module_id] = value

        reason = "API pipeline execution"
        sinks = sinks or None

        # Use controller only if no inputs were passed in
        if (not inputs and self.vistrail is not None and
                self.vistrail.current_version == self.version):
            controller = self.vistrail.controller
            results, changed = controller.execute_workflow_list([[
                    controller.locator,  # locator
                    self.version,  # version
                    self.pipeline,  # pipeline
                    DummyView(),  # view
                    None,  # custom_aliases
                    None,  # custom_params
                    reason,  # reason
                    sinks,  # sinks
                    None,  # extra_info
                    ]])
            result, = results
        else:
            pipeline = self.pipeline
            if inputs:
                id_scope = IdScope(1)
                pipeline = pipeline.do_copy(False, id_scope)

                # A hach to get ids from id_scope that we know won't collide:
                # make them negative
                id_scope.getNewId = lambda t, g=id_scope.getNewId: -g(t)

                create_module = \
                        VistrailController.create_module_from_descriptor_static
                create_function = VistrailController.create_function_static
                create_connection = VistrailController.create_connection_static
                # Fills in the ExternalPipe ports
                for module_id, values in inputs.iteritems():
                    module = pipeline.modules[module_id]
                    if not isinstance(values, (list, tuple)):
                        values = [values]

                    # Guess the type of the InputPort
                    _, sigstrings, _, _, _ = get_port_spec_info(pipeline, module)
                    sigstrings = parse_port_spec_string(sigstrings)

                    # Convert whatever we got to a list of strings, for the
                    # pipeline
                    values = [reg.convert_port_val(val, sigstring, None)
                              for val, sigstring in izip(values, sigstrings)]

                    if len(values) == 1:
                        # Create the constant module
                        constant_desc = reg.get_descriptor_by_name(
                                *sigstrings[0])
                        constant_mod = create_module(id_scope, constant_desc)
                        func = create_function(id_scope, constant_mod,
                                               'value', values)
                        constant_mod.add_function(func)
                        pipeline.add_module(constant_mod)

                        # Connect it to the ExternalPipe port
                        conn = create_connection(id_scope,
                                                 constant_mod, 'value',
                                                 module, 'ExternalPipe')
                        pipeline.db_add_connection(conn)
                    else:
                        raise RuntimeError("TODO : create tuple")

            interpreter = get_default_interpreter()
            result = interpreter.execute(pipeline,
                                         reason=reason,
                                         sinks=sinks)

        if result.errors:
            raise ExecutionErrors(self, result)
        else:
            return ExecutionResults(self, result)

    def get_module(self, module_id):
        if isinstance(module_id, (int, long)):  # module id
            module = self.pipeline.modules[module_id]
        elif isinstance(module_id, basestring):  # module name
            def desc(mod):
                if '__desc__' in mod.db_annotations_key_index:
                    return mod.get_annotation_by_key('__desc__').value
                else:
                    return None
            modules = [mod
                       for mod in self.pipeline.modules.itervalues()
                       if desc(mod) == module_id]
            if not modules:
                raise KeyError("No module with description %r" % module_id)
            elif len(modules) > 1:
                raise ValueError("Multiple modules with description %r" %
                                 module_id)
            else:
                module, = modules

        else:
            raise TypeError("get_module() expects a string or integer, not "
                            "%r" % type(module_id).__name__)
        return Module(descriptor=module.module_descriptor,
                      module_id=module.id,
                      pipeline=self)

    def _get_inputs_or_outputs(self, module_name):
        reg = get_module_registry()
        desc = reg.get_descriptor_by_name(
                'org.vistrails.vistrails.basic',
                module_name)
        modules = {}
        for module in self.pipeline.modules.itervalues():
            if module.module_descriptor is desc:
                name = get_inputoutput_name(module)
                if name is not None:
                    modules[name] = module
        return modules

    def get_input(self, name):
        try:
            module = self._get_inputs_or_outputs('InputPort')[name]
        except KeyError:
            raise KeyError("No InputPort module with name %r" % name)
        else:
            return Module(descriptor=module.module_descriptor,
                          module_id=module.id,
                          pipeline=self)

    def get_output(self, name):
        try:
            module = self._get_inputs_or_outputs('OutputPort')[name]
        except KeyError:
            raise KeyError("No OutputPort module with name %r" % name)
        else:
            return Module(descriptor=module.module_descriptor,
                          module_id=module.id,
                          pipeline=self)

    @property
    def inputs(self):
        if self._inputs is None:
            self._inputs = self._get_inputs_or_outputs('InputPort').keys()
        return self._inputs

    @property
    def outputs(self):
        if self._outputs is None:
            self._outputs = self._get_inputs_or_outputs('OutputPort').keys()
        return self._outputs

    def __repr__(self):
        desc = "<%s: %d modules, %d connections" % (
                self.__class__.__name__,
                len(self.pipeline.modules),
                len(self.pipeline.connections))
        inputs = self.inputs
        if inputs:
            desc += "; inputs: %s" % ", ".join(inputs)
        outputs = self.outputs
        if outputs:
            desc += "; outputs: %s" % ", ".join(outputs)
        return desc + ">"

    def _repr_html_(self):
        if self._html is None:
            import cgi
            try:
                from cStringIO import StringIO
            except ImportError:
                from StringIO import StringIO

            self._html = ''

            # http://www.graphviz.org/doc/info/shapes.html
            dot = ['digraph {\n    node [shape=plaintext];']

            # {moduleId: (input_ports, output_ports)}
            modules = dict((mod.id, (set(), set()))
                           for mod in self.pipeline.module_list)
            for conn in self.pipeline.connection_list:
                src, dst = conn.source, conn.destination
                modules[src.moduleId][1].add(src.name)
                modules[dst.moduleId][0].add(dst.name)

            # {moduleId: ({input_port_name: input_num},
            #             {output_port_name: output_num})
            # where input_num and output_num are just some sequences of numbers
            modules = dict((mod_id,
                            (dict((n, i) for i, n in enumerate(mod_ports[0])),
                             dict((n, i) for i, n in enumerate(mod_ports[1]))))
                           for mod_id, mod_ports in modules.iteritems())

            # Write out the modules
            for mod, port_lists in modules.iteritems():
                labels = []
                for port_type, ports in izip(('in', 'out'), port_lists):
                    label = ('<td port="%s%s">%s</td>' % (port_type, port_num, cgi.escape(port_name))
                             for port_name, port_num in ports.iteritems())
                    labels.append(''.join(label))

                label = ['<table border="0" cellborder="0" cellspacing="0">']
                if labels[0]:
                    label += ['<tr><td><table border="0" cellborder="1" cellspacing="0"><tr>', labels[0], '</tr></table></td></tr>']
                mod_obj = self.pipeline.modules[mod]
                if '__desc__' in mod_obj.db_annotations_key_index:
                    name = (mod_obj.get_annotation_by_key('__desc__')
                                 .value.strip())
                else:
                    name = mod_obj.label
                label += ['<tr><td border="1" bgcolor="grey"><b>', cgi.escape(name), '</b></td></tr>']
                if labels[1]:
                    label += ['<tr><td><table border="0" cellborder="1" cellspacing="0"><tr>', labels[1], '</tr></table></td></tr>']
                label += ['</table>']
                dot.append('    module%d [label=<%s>];' % (mod, '\n'.join(label)))
            dot.append('')

            # Write out the connections
            for conn in self.pipeline.connection_list:
                src, dst = conn.source, conn.destination
                dot.append('    module%d:out%d -> module%d:in%d;' % (
                           src.moduleId,
                           modules[src.moduleId][1][src.name],
                           dst.moduleId,
                           modules[dst.moduleId][0][dst.name]))

            dot.append('}')
            try:
                proc = subprocess.Popen(['dot', '-Tsvg'],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE)
                svg, _ = proc.communicate('\n'.join(dot))
                if proc.wait() == 0:
                    self._html += svg
            except OSError:
                pass
            self._html += '<pre>' + cgi.escape(repr(self)) + '</pre>'
        return self._html