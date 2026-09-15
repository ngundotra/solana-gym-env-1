//Search Tessera memory for tick magic / rust paths and dump xrefs.
//@category SolanaGym
import java.io.FileWriter;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.TerminatedStringDataType;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;

public class DumpTesseraXrefs extends GhidraScript {
    private static final String OUT = "/workspace/tools/re/notes/ghidra/tessera_xrefs.txt";

    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        byte[][] needles = new byte[][] {
            "MRKTKV01".getBytes("US-ASCII"),
            "MRKT".getBytes("US-ASCII"),
            "batch_clock.rs".getBytes("US-ASCII"),
            "Instruction slot does not match".getBytes("US-ASCII"),
        };
        try (FileWriter w = new FileWriter(OUT)) {
            w.write("program " + currentProgram.getName() + "\n");
            for (byte[] needle : needles) {
                w.write("NEEDLE " + new String(needle, "US-ASCII") + "\n");
                Address start = mem.getMinAddress();
                while (start != null) {
                    Address hit = mem.findBytes(start, needle, null, true, monitor);
                    if (hit == null) {
                        break;
                    }
                    w.write("  at " + hit + "\n");
                    Data data = getDataAt(hit);
                    if (data == null) {
                        try {
                            createData(hit, new TerminatedStringDataType());
                        } catch (Exception ignored) {
                        }
                    }
                    for (Reference ref : getReferencesTo(hit)) {
                        Address from = ref.getFromAddress();
                        Function fn = getFunctionContaining(from);
                        w.write("    xref " + from + " fn=" +
                            (fn == null ? "?" : fn.getName() + "@" + fn.getEntryPoint()) + "\n");
                    }
                    start = hit.add(1);
                }
            }
        }
        println("wrote " + OUT);
    }
}
