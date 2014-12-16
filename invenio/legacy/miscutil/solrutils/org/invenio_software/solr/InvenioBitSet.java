// Author: Jan Iwaszkiewicz
package org.invenio_software.solr;

import java.io.*;
import java.util.BitSet;
import java.util.Arrays;

public class InvenioBitSet extends BitSet {

    private static final long serialVersionUID = 1L;

    public InvenioBitSet() {
        super();
    }

    public InvenioBitSet(int nbits) {
        super(nbits);
    }

    // TODO: remove the trailing 8 bytes (added by intbitset format) and test
    public InvenioBitSet(byte[] bytes) {
        this(bytes == null? 0 : bytes.length * 8);
        for (int i = 0; i < size(); i++) {
            if (isBitOn(i, bytes))
                set(i);
        }
    }

    // convert to a byte array to be used as intbitset in Invenio
    public byte[] toByteArray()  {

        if (size() == 0)
            return new byte[0];

        // Find highest bit
        int hiBit = -1;
        for (int i = 0; i < size(); i++)  {
            if (get(i))
                hiBit = i;
        }

        // was: int n = (hiBit + 8) / 8;
        // +128 (64 for trailing zeros used in intbitset and 64 to avoid trancating)
        int n = ((hiBit + 128) / 64) * 8;
        byte[] bytes = new byte[n];
        if (n == 0)
            return bytes;

        Arrays.fill(bytes, (byte)0);
        for (int i=0; i<n*8; i++) {
            if (get(i))
                setBit(i, bytes);
        }
        return bytes;
    }

    protected static int BIT_MASK[] =
//        {0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01};
        {0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80};

    protected static boolean isBitOn(int bit, byte[] bytes) {
        int size = bytes == null ? 0 : bytes.length*8;
        if (bit >= size)
            return false;
        return (bytes[bit/8] & BIT_MASK[bit%8]) != 0;
    }

    protected static void setBit(int bit, byte[] bytes) {
        int size = bytes == null ? 0 : bytes.length*8;
        if (bit >= size)
            throw new ArrayIndexOutOfBoundsException("Byte array too small");
        bytes[bit/8] |= BIT_MASK[bit%8];
    }
}
