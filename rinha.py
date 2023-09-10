import llvmlite.binding as llvm
from llvmlite import ir
import json

int64 = ir.IntType(64)
int8 = ir.IntType(8)
float = ir.FloatType()
void = ir.VoidType()


class Generator:
    def __init__(self):

        self.module = ir.Module('module')

        self.builder = None

    def generate(self, expression):

        kind = expression['kind']
        name = expression['name']
        value = expression['value']
        next = expression['next']
        location = expression['location']

        if kind == 'Let':

            self.generate_let(expression)

    def generate_let(self, expression):

        name = expression['name']['text']
        value = expression['value']
        next = expression['next']
        location = expression['location']

        if value['kind'] == 'Function':

            self.generate_function(name, value)

    def generate_function(self, name, value):

        parameters = value['parameters']

        types = len(parameters) * [int64]

        fnty = ir.FunctionType(int64, types)
        func = ir.Function(self.module, fnty, name)
        entry = func.append_basic_block('entry')

        builder = ir.IRBuilder(entry)

        self.generate_body(func, builder, value['value'])

        builder.ret(int64(0))

    def generate_body(self, func, builder, body):

        kind = body['kind']
        condition = body['condition']
        then = body['then']
        otherwise = body['otherwise']

        if kind == 'If':

            if_then_block = func.append_basic_block('if.then')
            if_otherwise_block = func.append_basic_block('if.else')
            return_block = func.append_basic_block('if.end')

            if condition['kind'] == 'Binary':

                left = condition['lhs']
                right = condition['rhs']
                operator = condition['op']

                if left['kind'] == 'Var' and right['kind'] == 'Int':

                    left_var = func.args[0]

                sign = '<' if operator == 'Lt' else '>' if operator == 'Gt' else '=='

                with builder.if_then(builder.icmp_signed(sign, left_var, ir.Constant(ir.IntType(64), int(right['value'])))):

                    if then['kind'] == 'Var':

                        builder.position_at_end(if_then_block)
                        builder.ret(left_var)

                with builder.if_else(builder.icmp_signed(sign, left_var, ir.Constant(ir.IntType(64), int(right['value'])))):

                    builder.position_at_end(if_otherwise_block)
                    if otherwise['kind'] == 'Binary':

                        left = otherwise['lhs']
                        right = otherwise['rhs']
                        operator = otherwise['op']

                        if left['kind'] == 'Call' and right['kind'] == 'Call':

                            pass
                        

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
# llvm.initialize()
# llvm.initialize_native_target()
# llvm.initialize_native_asmprinter()
