import llvmlite.binding as llvm
from rinha import IntermediateRepresentation
import subprocess
import json

with open('/var/rinha/source.rinha.json') as f:

    ast_data = json.load(f)

ir = IntermediateRepresentation()

if (ast_data['expression']):

    ir.generate(ast_data['expression'])

else:

    raise Exception('Invalid AST')

module = ir.module
module.triple = llvm.get_default_triple()

llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

target = llvm.Target.from_default_triple()
target_machine = target.create_target_machine()
module.data_layout = target_machine.target_data

output_filename = f"output.ll"
triple = llvm.get_default_triple()
module.triple = triple

with open(output_filename, "w") as output_file:
    output_file.write(str(module))

compile_command = ["llc", "-filetype=obj", "-relocation-model=pic",
                   "-tailcallopt", "-o", "output.o", output_filename]
subprocess.run(compile_command, check=True)

link_command = ["clang", "-o", "output", "output.o", "-fPIE"]
subprocess.run(link_command, check=True)

execute_command = ["./output"]
subprocess.run(execute_command, check=True)
