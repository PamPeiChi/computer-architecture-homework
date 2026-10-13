// my_predictor.h
// This file contains a sample gshare_predictor class.
// It is a simple 32,768-entry gshare with a history length of 15.

class gshare_update : public branch_update {
public:
	unsigned int index;
};

class gshare_predictor : public branch_predictor {
public:
#define HISTORY_LENGTH	15
#define TABLE_BITS	15
	gshare_update u;
	branch_info bi;
	unsigned int history;
	unsigned char tab[1<<TABLE_BITS];

	gshare_predictor (void) : history(0) { 
		memset (tab, 0, sizeof (tab));
	}

	branch_update *predict (branch_info & b) {
		bi = b;
		if (b.br_flags & BR_CONDITIONAL) {
			u.index = 
				  (history << (TABLE_BITS - HISTORY_LENGTH)) 
				^ (b.address & ((1<<TABLE_BITS)-1));
			u.direction_prediction (tab[u.index] >> 1);
		} else {
			u.direction_prediction (true);
		}
		u.target_prediction (0);
		return &u;
	}

	void update (branch_update *u, bool taken, unsigned int target) {
		if (bi.br_flags & BR_CONDITIONAL) {
			unsigned char *c = &tab[((gshare_update*)u)->index];
			if (taken) {
				if (*c < 3) (*c)++;
			} else {
				if (*c > 0) (*c)--;
			}
			history <<= 1;
			history |= taken;
			history &= (1<<HISTORY_LENGTH)-1;
		}
	}
};

//
// Pentium M hybrid branch predictor (bimodal + 2-way tagged global predictor)
//
// Simplified model of the Pentium M branch *outcome* predictor (loop predictor,
// PIR and target prediction are skipped, as allowed by the assignment).
//
//  - Bimodal table : 2^BIM_BITS 2-bit saturating counters, indexed by low
//                    bits of the branch address.
//  - Global table  : 2^GP_ROW_BITS rows x GP_WAYS(=2) ways. Each entry holds
//                    valid, tag, 2-bit counter and LRU state. The row and tag
//                    both come from (branch address XOR global history):
//                    row = upper GP_ROW_BITS bits, tag = lower GP_TAG_BITS bits
//                    (same split as the worked example in the assignment).
//  - Prediction    : if the global table hits, use its counter; otherwise use
//                    the bimodal counter.
//  - Update        : bimodal counter is always updated. On a global hit its
//                    counter is updated and the way becomes MRU. On a global
//                    miss, a new entry is allocated (replacing an invalid way,
//                    else the LRU way) -- by default only when the bimodal
//                    prediction was wrong (GP_ALLOC_ON_MISPRED=1).
//  - GHR           : shift register of the last GHR_BITS conditional outcomes.
//
// All sizes can be overridden at compile time with -D flags, e.g.
//   g++ -O3 -DGHR_BITS=12 -DGP_ROW_BITS=10 ...

#ifndef BIM_BITS
#define BIM_BITS 12            // bimodal table: 4096 counters
#endif
#ifndef BIM_SHIFT
#define BIM_SHIFT 0            // address bits skipped before indexing (x86: 0)
#endif
#ifndef GHR_BITS
#define GHR_BITS 16            // global history length
#endif
#ifndef GP_ROW_BITS
#define GP_ROW_BITS 10         // global table rows: 1024
#endif
#ifndef GP_TAG_BITS
#define GP_TAG_BITS 10         // tag width
#endif
#ifndef GP_WAYS
#define GP_WAYS 2              // 2-way global predictor
#endif
#ifndef GP_ALLOC_ON_MISPRED
#define GP_ALLOC_ON_MISPRED 1  // allocate global entry only if bimodal was wrong
#endif

class pm_update : public branch_update {
public:
        unsigned int bim_index;   // bimodal index used at prediction
        unsigned int row, tag;    // global row / tag used at prediction
        int hit_way;              // way that hit in global table, -1 on miss
        bool bim_pred;            // bimodal's own prediction
        bool conditional;
};

class pm_predictor : public branch_predictor {
public:
        pm_update u;

        struct gp_entry {
                bool valid;
                unsigned int tag;
                unsigned char ctr;   // 2-bit saturating counter
                unsigned char lru;   // 0 = most recently used; larger = older
        };

        unsigned char bim[1 << BIM_BITS];
        gp_entry gp[1 << GP_ROW_BITS][GP_WAYS];
        unsigned int ghr;

        pm_predictor (void) : ghr(0) {
                memset (bim, 1, sizeof (bim));          // weakly not-taken
                memset (gp, 0, sizeof (gp));
                for (int r = 0; r < (1 << GP_ROW_BITS); r++)
                        for (int w = 0; w < GP_WAYS; w++)
                                gp[r][w].lru = w;       // distinct LRU ranks
        }

        static void sat_update (unsigned char *c, bool taken) {
                if (taken) { if (*c < 3) (*c)++; }
                else       { if (*c > 0) (*c)--; }
        }

        // make way w the most recently used way of row r
        void touch (unsigned int r, int w) {
                unsigned char old = gp[r][w].lru;
                for (int i = 0; i < GP_WAYS; i++)
                        if (gp[r][i].lru < old) gp[r][i].lru++;
                gp[r][w].lru = 0;
        }

        branch_update *predict (branch_info & b) {
                u.conditional = (b.br_flags & BR_CONDITIONAL) != 0;
                u.hit_way = -1;

                if (u.conditional) {
                        // bimodal prediction
                        u.bim_index = (b.address >> BIM_SHIFT) & ((1 << BIM_BITS) - 1);
                        u.bim_pred = bim[u.bim_index] >> 1;

                        // global lookup: hash = address XOR history
                        const unsigned int hbits = GP_ROW_BITS + GP_TAG_BITS;
                        unsigned int h = ((b.address >> BIM_SHIFT) ^ ghr) & ((1u << hbits) - 1);
                        u.row = h >> GP_TAG_BITS;
                        u.tag = h & ((1u << GP_TAG_BITS) - 1);

                        for (int w = 0; w < GP_WAYS; w++) {
                                if (gp[u.row][w].valid && gp[u.row][w].tag == u.tag) {
                                        u.hit_way = w;
                                        break;
                                }
                        }

                        if (u.hit_way >= 0)
                                u.direction_prediction (gp[u.row][u.hit_way].ctr >> 1);
                        else
                                u.direction_prediction (u.bim_pred);
                } else {
                        u.direction_prediction (true);
                }

                // branch target prediction is skipped in this assignment
                u.target_prediction (0);
                return &u;
        }

        void update (branch_update *bu, bool taken, unsigned int target) {
                pm_update *p = (pm_update *) bu;
                if (!p->conditional) return;

                // bimodal is always trained
                sat_update (&bim[p->bim_index], taken);

                if (p->hit_way >= 0) {
                        // global hit: train that counter, make it MRU
                        sat_update (&gp[p->row][p->hit_way].ctr, taken);
                        touch (p->row, p->hit_way);
                } else if (!GP_ALLOC_ON_MISPRED || p->bim_pred != taken) {
                        // global miss: allocate (invalid way first, else LRU)
                        int victim = 0;
                        for (int w = 0; w < GP_WAYS; w++) {
                                if (!gp[p->row][w].valid) { victim = w; goto found; }
                        }
                        for (int w = 0; w < GP_WAYS; w++)
                                if (gp[p->row][w].lru > gp[p->row][victim].lru) victim = w;
                found:
                        gp[p->row][victim].valid = true;
                        gp[p->row][victim].tag   = p->tag;
                        gp[p->row][victim].ctr   = taken ? 2 : 1;   // weak, toward outcome
                        touch (p->row, victim);
                }

                // shift outcome into global history
                ghr = ((ghr << 1) | (taken ? 1 : 0)) & ((1u << GHR_BITS) - 1);
        }
};

//
// Complete Pentium M branch predictors for extra credit
// This class implements the complete Pentium M branch prediction units. 
// It implements both branch target prediction and branch outcome predicton. 
class cpm_update : public branch_update {
public:
        unsigned int index;
};

class cpm_predictor : public branch_predictor {
public:
        cpm_update u;

        cpm_predictor (void) {
        }

        branch_update *predict (branch_info & b) {
            u.direction_prediction (true);
            u.target_prediction (0);
            return &u;
        }

        void update (branch_update *u, bool taken, unsigned int target) {
        }

};


