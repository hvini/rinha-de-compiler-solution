import llvmlite.binding as llvm
from llvmlite import ir
import subprocess
import json

int32 = ir.IntType(32)
int8 = ir.IntType(8)


class Generator:

    def __init__(self):

        self.module = ir.Module('module')

        printf_type = ir.FunctionType(
            int32, [ir.PointerType(int8)], var_arg=True)
        printf_func = ir.Function(self.module, printf_type, 'printf')

        main_type = ir.FunctionType(int32, [])
        main_func = ir.Function(self.module, main_type, 'main')

        self.variables = {'printf': printf_func, 'main': main_func}

        self.builder = None

    def generate(self, expression):

        kind = expression['kind']
        name = expression['name'] if 'name' in expression else None
        value = expression['value'] if 'value' in expression else None
        next = expression['next'] if 'next' in expression else None

        if kind == 'Let':

            if value['kind'] == 'Function':

                self.generate_function(name['text'], value)

        elif kind == 'If':

            self.generate_if(expression)

        elif kind == 'Var':

            self.builder.ret(self.variables[expression['text']])

        elif kind == 'Print':

            self.generate_print(expression)

        if next is not None:

            self.builder = None
            self.generate(next)

    def generate_print(self, expression):

        value = expression['value']
        value_kind = value['kind']

        self.builder = ir.IRBuilder(
            self.variables['main'].append_basic_block('entry')) if self.builder is None else self.builder

        value = self.visit_value(value)

        zero = ir.Constant(int32, 0)
        format_str = "%s\n" if value_kind == 'Str' else "%d\n"

        format_constant = ir.Constant(ir.ArrayType(int8, len(
            format_str)), bytearray(format_str.encode("utf8")))
        format_global = ir.GlobalVariable(
            self.module, format_constant.type, name="format_string")
        format_global.linkage = 'internal'
        format_global.global_constant = True
        format_global.initializer = format_constant
        format_global.align = 1

        format_ptr = self.builder.gep(format_global, [zero, zero])
        format_ptr = self.builder.bitcast(
            format_ptr, int8.as_pointer())

        printf_func = self.variables['printf']
        self.builder.call(printf_func, [format_ptr, value])

        self.builder.ret(zero)

    def visit_value(self, value):

        kind = value['kind']
        if kind == 'Var':

            text = value['text']

            ptr = self.variables[text] if text in self.variables else None
            if ptr is None:

                ptr = self.builder.alloca(int32,  name=text)
                self.variables[text] = ptr

            return ptr

        if kind == 'Str':

            string = f'{value["value"]}\0'
            ptr = self.builder.alloca(
                ir.ArrayType(int8, len(string)), name='str')
            self.builder.store(ir.Constant(ir.ArrayType(int8, len(string)), bytearray(
                string.encode("utf8"))), ptr)
            return ptr

        if kind == 'Int':

            return ir.Constant(int32, value['value'])

        if kind == 'Binary':

            return self.visit_expression(value)

        if kind == 'Call':

            return self.visit_call(value)

    def visit_call(self, value):

        callee = value['callee']
        arguments = value['arguments']

        values = [self.visit_value(arg) for arg in arguments]

        func = self.module.get_global(callee['text'])

        return self.builder.call(func, values)

    def visit_expression(self, expression):

        lhs = self.visit_value(expression['lhs'])
        rhs = self.visit_value(expression['rhs'])
        operator = expression['op']

        if operator == 'Lt':

            value = self.builder.icmp_signed('<', lhs, rhs)

        elif operator == 'Sub':

            value = self.builder.sub(lhs, rhs)

        elif operator == 'Add':

            value = self.builder.add(lhs, rhs)

        elif operator == 'Eq':

            value = self.builder.icmp_signed('==', lhs, rhs)

        else:

            raise Exception('Invalid operator')

        return value

    def generate_if(self, expr):

        condition = expr['condition']
        then = expr['then']
        orelse = expr['otherwise']

        value = self.visit_value(condition)
        with self.builder.if_else(value) as (true, otherwise):

            with true:

                self.generate(then)

            with otherwise:

                value = self.visit_value(orelse)
                self.builder.ret(value)

        self.builder.ret(ir.Constant(int32, 0))

    def generate_function(self, name, value):

        parameters = value['parameters']

        types = [int32] * len(parameters)

        func_type = ir.FunctionType(int32, types)
        func = ir.Function(self.module, func_type, name)
        entry = func.append_basic_block('entry')

        self.builder = ir.IRBuilder(entry)

        for param, arg in zip(parameters, self.builder.function.args):

            self.variables[param['text']] = arg

        self.generate(value['value'])


# Load your AST from the JSON file
with open('files/print.json') as f:

    ast_data = json.load(f)

# Create an instance of the generator
generator = Generator()

# Generate LLVM IR code from the AST
if (ast_data['expression']):

    generator.generate(ast_data['expression'])

else:

    raise Exception('Invalid AST')

module = generator.module
module.triple = llvm.get_default_triple()

# Initialize LLVM
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

target = llvm.Target.from_default_triple()
target_machine = target.create_target_machine()
module.data_layout = target_machine.target_data

output_filename = "output.ll"
triple = llvm.get_default_triple()
module.triple = triple

with open(output_filename, "w") as output_file:
    output_file.write(str(module))

compile_command = ["llc", "-filetype=obj", "-o", "output.o", output_filename]
subprocess.run(compile_command, check=True)

# Link the object file to create an executable
link_command = ["clang", "-o", "output", "output.o"]
subprocess.run(link_command, check=True)

# Execute the generated executable
execute_command = ["./output"]
subprocess.run(execute_command, check=True)
