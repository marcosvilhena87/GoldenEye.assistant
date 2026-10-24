import unittest
from tools.analyze_spatial_communities_v3_2 import (
    audit, components, community_partition, validate, PARAMS, BLOCKS, PAIRS
)
from tools.analyze_spatial_position_v2_4 import PHASES

class CommunityV32Tests(unittest.TestCase):
    def sample(self):
        rows=[]
        for left,right in PAIRS:
            strong=(left,right) in {
                (BLOCKS[0],BLOCKS[1]),
                (BLOCKS[1],BLOCKS[2]),
                (BLOCKS[4],BLOCKS[5]),
            }
            for phase in PHASES:
                rows.append(dict(original="s1",replica="s2",left=left,right=right,
                    phase=phase,accuracy_gain=.15 if strong else -.01,
                    test_sync=.97 if strong else .3,
                    logloss_gain=.03 if strong else -.02))
        return rows

    def test_audit_shape(self):
        result=audit(self.sample())
        edges,communities,sensitivity,persistence,ranks=result
        self.assertEqual(len(edges),190)
        self.assertEqual(len(communities),20)
        self.assertEqual(len(sensitivity),len(PARAMS))
        self.assertEqual(len(persistence),9)
        self.assertEqual(len(ranks),190)
        self.assertEqual(sum(int(r["direct"]) for r in edges),3)
        self.assertEqual(next(r for r in sensitivity if float(r["gain"])==.02)["edge_count"],3)

    def test_direct_vs_transitive(self):
        e={(BLOCKS[0],BLOCKS[1]),(BLOCKS[1],BLOCKS[2])}
        self.assertEqual(len(components(BLOCKS[:3],e)),1)
        p=community_partition(BLOCKS[:3],e)
        self.assertEqual(set(x for group in p for x in group),set(BLOCKS[:3]))
        self.assertNotIn((BLOCKS[0],BLOCKS[2]),e)

    def test_invalid_and_duplicate(self):
        rows=self.sample()
        with self.assertRaises(ValueError):validate(rows[:-1])
        with self.assertRaises(ValueError):validate(rows[:-1]+[rows[0]])
        with self.assertRaises(ValueError):validate([dict(r,replica="s1") for r in rows])

if __name__=="__main__":
    unittest.main()
