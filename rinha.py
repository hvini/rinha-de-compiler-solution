from llvmlite import ir

int32 = ir.IntType(32)
int8 = ir.IntType(8)


class IntermediateRepresentation:

    def __init__(self):

        self.module = ir.Module('module')

        printf_type = ir.FunctionType(
            int32, [ir.PointerType(int8)], var_arg=True)
        printf_func = ir.Function(self.module, printf_type, 'printf')

        main_type = ir.FunctionType(int32, [])
        main_func = ir.Function(self.module, main_type, 'main')

        self.__variables = {'printf': printf_func, 'main': main_func}

        self.__builder = None
        self.aa = []

    def generate(self, expression):

        kind = expression['kind']
        name = expression['name'] if 'name' in expression else None
        value = expression['value'] if 'value' in expression else None
        next = expression['next'] if 'next' in expression else None

        if kind == 'Let':

            self.aa.append(next)

            if value['kind'] == 'Function':

                self._generate_function(name['text'], value)

            if value['kind'] == 'Binary':

                value, _ = self._visit_value(value)
                self.__variables[name['text']] = value

            if len(self.aa) > 1:

                val = self.aa.pop()
                self.generate(val)

            else:

                val = self.aa.pop()
                self.__builder = None
                self.generate(val)

        elif kind == 'If':

            self._generate_if(expression)

        elif kind == 'Var':

            self.__builder.ret(self.__variables[expression['text']])

        elif kind == 'Print':

            self._generate_print(expression)

    def _generate_print(self, expression):

        self.__builder = ir.IRBuilder(
            self.__variables['main'].append_basic_block('entry')) if self.__builder is None else self.__builder

        value, Type = self._visit_value(expression['value'])

        zero = ir.Constant(int32, 0)
        format_str = "%s\n" if Type == 'Str' else "%d\n"

        format_constant = ir.Constant(ir.ArrayType(int8, len(
            format_str)), bytearray(format_str.encode("utf8")))
        format_global = ir.GlobalVariable(
            self.module, format_constant.type, name="format_string")
        format_global.linkage = 'internal'
        format_global.global_constant = True
        format_global.initializer = format_constant
        format_global.align = 1

        format_ptr = self.__builder.gep(format_global, [zero, zero])
        format_ptr = self.__builder.bitcast(
            format_ptr, int8.as_pointer())

        printf_func = self.__variables['printf']
        self.__builder.call(printf_func, [format_ptr, value])

        self.__builder.ret(zero)

    def _visit_value(self, value):

        kind = value['kind']
        if kind == 'Var':

            text = value['text']

            ptr = self.__variables[text] if text in self.__variables else None
            if ptr is None:

                ptr = self.__builder.alloca(int32,  name=text)
                self.__variables[text] = ptr

            return ptr, kind

        if kind == 'Str':

            string = f'{value["value"]}\0'
            ptr = self.__builder.alloca(
                ir.ArrayType(int8, len(string)), name='str')
            self.__builder.store(ir.Constant(ir.ArrayType(int8, len(string)), bytearray(
                string.encode("utf8"))), ptr)
            return ptr, kind

        if kind == 'Int':

            return ir.Constant(int32, value['value']), kind

        if kind == 'Binary':

            return self._visit_expression(value), kind

        if kind == 'Call':

            return self._visit_call(value), kind

    def _visit_call(self, value):

        callee = value['callee']
        arguments = value['arguments']

        values = [self._visit_value(arg)[0] for arg in arguments]

        func = self.module.get_global(callee['text'])

        return self.__builder.call(func, values)

    def _visit_expression(self, expression):

        lhs, _ = self._visit_value(expression['lhs'])
        rhs, _ = self._visit_value(expression['rhs'])
        operator = expression['op']

        if operator == 'Lt':

            value = self.__builder.icmp_signed('<', lhs, rhs)

        elif operator == 'Sub':

            value = self.__builder.sub(lhs, rhs)

        elif operator == 'Add':

            value = self.__builder.add(lhs, rhs)

        elif operator == 'Eq':

            value = self.__builder.icmp_signed('==', lhs, rhs)

        elif operator == 'Or':

            value = self.__builder.or_(lhs, rhs)

        else:

            raise Exception('Invalid operator')

        return value

    def _generate_if(self, expr):

        condition = expr['condition']
        then = expr['then']
        orelse = expr['otherwise']

        value, _ = self._visit_value(condition)
        with self.__builder.if_else(value) as (true, otherwise):

            with true:

                if then['kind'] == 'Int':

                    self.__builder.ret(ir.Constant(int32, then['value']))

                else:

                    self.generate(then)

            with otherwise:

                value, _ = self._visit_value(orelse)
                self.__builder.ret(value)

        self.__builder.ret(ir.Constant(int32, 0))

    def _generate_function(self, name, value):

        parameters = value['parameters']

        types = [int32] * len(parameters)

        func_type = ir.FunctionType(int32, types)
        func = ir.Function(self.module, func_type, name)
        entry = func.append_basic_block('entry')

        self.__builder = ir.IRBuilder(entry)

        for param, arg in zip(parameters, self.__builder.function.args):

            self.__variables[param['text']] = arg

        self.generate(value['value'])
