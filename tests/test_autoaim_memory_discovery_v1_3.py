import unittest
from tools.analyze_autoaim_mem_v1_3 import LABELS,OFFSETS,analyze

class V13AnalysisTests(unittest.TestCase):
    def test_two_independent_identical_runs(self):
        data={offset:{label:(1 if label not in ("OFF1","OFF_STABLE") else 0) for label in LABELS} for offset in OFFSETS}
        result=analyze([("runA",data),("runB",data)])
        self.assertEqual(5,sum(x["status"]=="reproduced_candidate_controls_only" for x in result))
    def test_negative_control_failure(self):
        def make():
            return {offset:{label:(1 if label not in ("OFF1","OFF_STABLE") else 0) for label in LABELS} for offset in OFFSETS}
        a,b=make(),make()
        b[OFFSETS[0]]["OTHER_OPTION_CONTROL"]=2
        self.assertEqual("needs_validation",analyze([("A",a),("B",b)])[0]["status"])
    def test_cross_run_disagreement(self):
        def make(on,off):
            return {offset:{label:(off if label in ("OFF1","OFF_STABLE") else on) for label in LABELS} for offset in OFFSETS}
        self.assertEqual("needs_validation",analyze([("A",make(1,0)),("B",make(2,0))])[0]["status"])
