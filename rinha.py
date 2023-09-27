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
        main_builder = ir.IRBuilder(
            main_func.append_basic_block('entry'))

        self.__variables = {'printf': printf_func, 'main': main_builder}

        self.__builder = None
        self.__next_expr = []

    def generate(self, expression):

        kind = expression['kind']
        name = expression['name'] if 'name' in expression else None
        value = expression['value'] if 'value' in expression else None
        next = expression['next'] if 'next' in expression else None

        self.__builder = self.__variables['main'] if self.__builder is None else self.__builder

        if kind == 'Let':

            self.__next_expr.append(next)

            self._generate_let(name, value)

            if len(self.__next_expr) > 0:

                self.generate(self.__next_expr.pop())

        elif kind == 'If':

            self._generate_if(expression)

        elif kind == 'Var':

            self.__builder.ret(self.__variables[expression['text']])

        elif kind == 'Print':

            self._generate_print(expression)

        else:

            raise Exception('Invalid expression')

    def _generate_let(self, name, value):

        kind = value['kind']
        text = name['text']

        if kind == 'Function':

            self._generate_function(text, value)

        elif kind == 'Binary':

            value, _ = self._visit_value(value)
            self.__variables[text] = value

        elif kind == 'Int':

            ptr = self.__builder.alloca(int32,  name=text)
            self.__builder.store(ir.Constant(
                int32, value['value']), ptr)
            self.__variables[text] = ptr

        elif kind == 'Str':

            string = f'{value["value"]}\0'
            ptr = self.__builder.alloca(
                ir.ArrayType(int8, len(string)), name=text)
            self.__builder.store(ir.Constant(ir.ArrayType(int8, len(string)), bytearray(
                string.encode("utf8"))), ptr)
            self.__variables[text] = ptr

        elif kind == 'Print':

            self._generate_print(value)

        else:

            raise Exception('Invalid')

    def _get_pointee_type(self, value):

        if value.type == int32:

            return 'Int'

        elif value.type == ir.ArrayType(int8, len(value.type)):

            return 'Str'

        raise Exception('Invalid print type')

    def _generate_print(self, expression):

        value, Type = self._visit_value(expression['value'])
        if Type == 'Var':

            ptr_val = self.__builder.load(value)
            Type = self._get_pointee_type(ptr_val)
            value = ptr_val if Type == 'Int' else value

        zero = ir.Constant(int32, 0)

        format_name = f'format_{Type}'
        if format_name in self.__variables:

            format_global = self.__variables[format_name]

        else:

            format_str = "%s\n\0" if Type == 'Str' else "%d\n\0"

            format_constant = ir.Constant(ir.ArrayType(int8, len(
                format_str)), bytearray(format_str.encode("utf8")))
            format_global = ir.GlobalVariable(
                self.module, format_constant.type, name=format_name)
            format_global.linkage = 'internal'
            format_global.global_constant = True
            format_global.initializer = format_constant
            format_global.align = 1

            self.__variables[format_name] = format_global

        format_ptr = self.__builder.gep(format_global, [zero, zero])
        format_ptr = self.__builder.bitcast(
            format_ptr, int8.as_pointer())

        printf_func = self.__variables['printf']
        self.__builder.call(printf_func, [format_ptr, value])

        if len(self.__next_expr) == 0:
            self.__builder.ret(ir.Constant(int32, 0))

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

        raise Exception('Invalid value')

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

        elif operator == 'Gt':

            value = self.__builder.icmp_signed('>', lhs, rhs)

        elif operator == 'Sub':

            value = self.__builder.sub(lhs, rhs)

        elif operator == 'Add':

            value = self.__builder.add(lhs, rhs)

        elif operator == 'Eq':

            value = self.__builder.icmp_signed('==', lhs, rhs)

        elif operator == 'Or':

            value = self.__builder.or_(lhs, rhs)

        elif operator == 'Mul':

            value = self.__builder.mul(lhs, rhs)

        elif operator == 'Div':

            value = self.__builder.sdiv(lhs, rhs)

        elif operator == 'Rem':

            value = self.__builder.srem(lhs, rhs)

        elif operator == 'Neq':

            value = self.__builder.icmp_signed('!=', lhs, rhs)

        elif operator == 'And':
                
            value = self.__builder.and_(lhs, rhs)
        
        elif operator == 'Lte':

            value = self.__builder.icmp_signed('<=', lhs, rhs)

        elif operator == 'Gte':

            value = self.__builder.icmp_signed('>=', lhs, rhs)

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

        self.__builder = None
