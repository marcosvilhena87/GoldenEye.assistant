import unittest
from tools.analyze_enemy_freeze_v1_1 import build_reports

def candidate(offset,encoding,p1,p2):
    return dict(offset_int=offset,offset_hex=f"0x{offset:06X}",
                encoding=encoding,p1=p1,p2=p2,delta=p2-p1,
                abs_delta=abs(p2-p1),raw_p1="00000000",raw_p2="00000000")

class CandidateRankingTests(unittest.TestCase):
    def test_cluster_pair_and_rank(self):
        data=[candidate(0x100,"float32_big",100,105),
              candidate(0x104,"float32_big",20,30),
              candidate(0x108,"float32_little",20,30),
              candidate(0x200,"float32_big",2,3)]
        ranked,clusters,pairs=build_reports(data)
        self.assertEqual(len(ranked),4)
        self.assertEqual(len(clusters),2)
        self.assertEqual(clusters[0]["distinct_offsets"],3)
        self.assertTrue(any(p["offset_a"]=="0x000100" and
                            p["offset_b"]=="0x000104" for p in pairs))
        self.assertFalse(any(p["offset_a"]=="0x000104" and
                             p["offset_b"]=="0x000108" for p in pairs))
        self.assertEqual({r["rank"] for r in ranked},{1,2,3,4})
        self.assertTrue(all(r["cluster_id"] for r in ranked))
    def test_empty(self):
        self.assertEqual(build_reports([]),([],[],[]))
    def test_scale_heuristic(self):
        ranked,_,_=build_reports([candidate(0x100,"float32_big",1e6,1e6+3)])
        self.assertEqual(ranked[0]["plausible_scale"],0)

if __name__=="__main__":
    unittest.main()
