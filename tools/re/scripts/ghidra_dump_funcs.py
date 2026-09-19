# Ghidra headless post-script: dump function names/sizes.
# @category SolanaGym
from ghidra.program.model.listing import FunctionManager  # noqa: F401

out = "/workspace/tools/re/notes/ghidra/tessera_funcs.txt"
fm = currentProgram.getFunctionManager()
n = 0
with open(out, "w") as f:
    f.write("program %s\n" % currentProgram.getName())
    for fn in fm.getFunctions(True):
        body = fn.getBody()
        f.write("%s\t%s\t%d\n" % (fn.getEntryPoint(), fn.getName(), body.getNumAddresses()))
        n += 1
    f.write("count %d\n" % n)
print("wrote", n, "functions to", out)
