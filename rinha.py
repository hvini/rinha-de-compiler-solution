import llvmlite.binding as llvm
from llvmlite import ir
import subprocess
import json

int32 = ir.IntType(32)
int8 = ir.IntType(8)
float = ir.FloatType()
void = ir.VoidType()


class Generator:

    def __init__(self):

        self.module = ir.Module('module')

        printf_ty = ir.FunctionType(
            int32, [ir.PointerType(int8)], var_arg=True)
        func = ir.Function(self.module, printf_ty, 'printf')

        self.variables = {'printf': (func, int32)}

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

            self.builder.ret(self.builder.load(
                self.variables[expression['text']]))

        elif kind == 'Print':

            self.generate_print(expression)

        if next is not None:

            self.generate(next)

    def generate_print(self, expression):

        fnty = ir.FunctionType(int32, [])
        func = ir.Function(self.module, fnty, 'main')
        entry = func.append_basic_block('main_entry')

        self.builder = ir.IRBuilder(entry)

        value = self.visit_value(expression['value'])
        format_str = ir.GlobalVariable(self.module, ir.ArrayType(
            int8, len(b"%d\n") + 1), name="format_str")
        format_str.initializer = ir.Constant(ir.ArrayType(
            int8, len(b"%d\n") + 1), bytearray(b"%d\n\0"))
        format_str.align = 1

        printf_func, _ = self.variables['printf']
        printf_args = [format_str.gep(
            [ir.Constant(int32, 0), ir.Constant(int32, 0)]), value]
        self.builder.call(printf_func, printf_args)

        self.builder.ret(ir.Constant(int32, 0))

    def visit_value(self, value):

        kind = value['kind']
        if kind == 'Var':

            ptr = self.variables[value['text']
                                 ] if value['text'] in self.variables else None
            if ptr is None:

                ptr = self.builder.alloca(int32,  name=value['text'])
                self.variables[value['text']] = ptr

            return self.builder.load(ptr)

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

        if operator == 'Sub':

            value = self.builder.sub(lhs, rhs)

        if operator == 'Add':

            value = self.builder.add(lhs, rhs)

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

                self.visit_value(orelse)

        self.builder.ret(ir.Constant(int32, 0))

    def generate_function(self, name, value):

        parameters = value['parameters']

        types = len(parameters) * [int32]

        fnty = ir.FunctionType(int32, types)
        func = ir.Function(self.module, fnty, name)
        entry = func.append_basic_block('entry')

        self.builder = ir.IRBuilder(entry)

        self.generate(value['value'])


# Load your AST from the JSON file
with open('files/fib.json') as f:

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

# Print the LLVM module
print(module)

# Initialize LLVM
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

target = llvm.Target.from_default_triple()
target_machine = target.create_target_machine()
module.data_layout = target_machine.target_data

output_filename = "output.ll"  # Specify the output filename
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
