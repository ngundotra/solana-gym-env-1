//Dump Tessera function table after eBPF analysis.
//@category SolanaGym
import java.io.FileWriter;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;

public class DumpTesseraFuncs extends GhidraScript {
    @Override
    public void run() throws Exception {
        String out = "/workspace/tools/re/notes/ghidra/tessera_funcs.txt";
        FunctionManager fm = currentProgram.getFunctionManager();
        int n = 0;
        int swapish = 0;
        try (FileWriter w = new FileWriter(out)) {
            w.write("program " + currentProgram.getName() + "\n");
            for (Function fn : fm.getFunctions(true)) {
                String name = fn.getName();
                int sz = (int) fn.getBody().getNumAddresses();
                w.write(fn.getEntryPoint() + "\t" + name + "\t" + sz + "\n");
                n++;
                String low = name.toLowerCase();
                if (low.contains("swap") || low.contains("tick") || low.contains("clock")) {
                    swapish++;
                }
            }
            w.write("count " + n + " swapish " + swapish + "\n");
        }
        println("wrote " + n + " functions");
    }
}
