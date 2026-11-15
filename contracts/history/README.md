# Historical contract proposals

contracts/v1 is the single current canonical schema. The p1 directory preserves the
initial unfrozen proposal and its offline fixture inputs exactly as they existed in
commit 92626f5 before the accepted P2 revision-3 promotion. These files are historical,
not alternate consumer contracts. To reproduce historical candidate generation/checks,
use that immutable Git checkout. New bindings regenerate from the frozen contracts/v1.
