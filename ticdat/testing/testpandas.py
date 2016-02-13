import os
import unittest
import ticdat.utils as utils
import shutil
from ticdat.ticdatfactory import TicDatFactory, pd
from ticdat.testing.ticdattestutils import dietData, dietSchema, netflowData
from ticdat.testing.ticdattestutils import  netflowSchema, firesException
from ticdat.testing.ticdattestutils import sillyMeData, sillyMeSchema, failToDebugger
from ticdat.testing.ticdattestutils import  makeCleanDir, runSuite, addNetflowForeignKeys

#@failToDebugger
class TestPandas(unittest.TestCase):
    def testDiet(self):
        tdf = TicDatFactory(**dietSchema())
        tdf.enable_foreign_key_links()
        oldDat = tdf.freeze_me(tdf.TicDat(**{t:getattr(dietData(),t) for t in tdf.primary_key_fields}))
        ticDat = tdf.copy_to_pandas(oldDat)
        for k in oldDat.foods:
            self.assertTrue(oldDat.foods[k]["cost"] == ticDat.foods.cost[k])
        for k in oldDat.categories:
            self.assertTrue(oldDat.categories[k]["minNutrition"] == ticDat.categories.minNutrition[k])
        for k1, k2 in oldDat.nutritionQuantities:
            self.assertTrue(oldDat.nutritionQuantities[k1,k2]["qty"] ==
                            ticDat.nutritionQuantities.qty[k1,k2])
        nut = ticDat.nutritionQuantities
        self.assertTrue(firesException(lambda : nut.qty.loc[:, "fatty"]))
        self.assertTrue(firesException(lambda : nut.qty.loc["chickeny", :]))
        self.assertFalse(firesException(lambda : nut.qty.sloc[:, "fatty"]))
        self.assertFalse(firesException(lambda : nut.qty.sloc["chickeny", :]))
        self.assertTrue(0 == sum(nut.qty.sloc[:, "fatty"]) == sum(nut.qty.sloc["chickeny", :]))
        self.assertTrue(sum(nut.qty.sloc[:, "fat"]) == sum(nut.qty.loc[:, "fat"]) ==
                        sum(r["qty"] for (f,c),r in oldDat.nutritionQuantities.items() if c == "fat"))
        self.assertTrue(sum(nut.qty.sloc["chicken",:]) == sum(nut.qty.loc["chicken",:]) ==
                        sum(r["qty"] for (f,c),r in oldDat.nutritionQuantities.items() if f == "chicken"))


    def testNetflow(self):
        tdf = TicDatFactory(**netflowSchema())
        tdf.enable_foreign_key_links()
        addNetflowForeignKeys(tdf)
        oldDat = tdf.freeze_me(tdf.TicDat(**{t:getattr(netflowData(),t) for t in tdf.primary_key_fields}))
        ticDat = tdf.copy_to_pandas(oldDat, ["arcs", "cost"])
        self.assertTrue(all(hasattr(ticDat, t) == (t in ["arcs", "cost"]) for t in tdf.all_tables))
        self.assertTrue(len(ticDat.arcs.capacity.sloc["Boston",:]) == len(oldDat.nodes["Boston"].arcs_source) == 0)
        self.assertTrue(len(ticDat.arcs.capacity.sloc[:,"Boston"]) == len(oldDat.nodes["Boston"].arcs_destination) == 2)
        self.assertTrue(all(ticDat.arcs.capacity.sloc[:,"Boston"][src] == r["capacity"]
                            for src, r in oldDat.nodes["Boston"].arcs_destination.items()))

    def testSilly(self):
        tdf = TicDatFactory(**dict({"d" : [("dData1", "dData2", "dData3", "dData4"),[]],
                                    "e" : [["eData"],[]]}, **sillyMeSchema()))
        ticDat = tdf.copy_to_pandas(tdf.TicDat(**sillyMeData()))
        self.assertFalse(len(ticDat.d) + len(ticDat.e))
        oldDat = tdf.freeze_me(tdf.TicDat(**dict({"d" : {(1,2,3,4):{}, (1, "b","c","d"):{}, ("a", 2,"c","d"):{}},
                                                  "e" : {11:{},"boger":{}}},
                                **sillyMeData())))
        ticDat = tdf.copy_to_pandas(oldDat)
        def checkTicDat():
            self.assertTrue(len(ticDat.d) ==3 and len(ticDat.e) == 2)
            self.assertTrue(set(ticDat.d.index.values) == {(1,2,3,4), (1, "b","c","d"), ("a", 2,"c","d")})
            self.assertTrue(set(ticDat.e.index.values) == {11,"boger"})
            self.assertTrue(len(ticDat.c) == len(oldDat.c) == 3)
            self.assertTrue(ticDat.c.loc[i] == oldDat.c[i] for i in range(3))
        checkTicDat()
        self.assertFalse(hasattr(ticDat.d, "dData1") or hasattr(ticDat.e, "eData"))

        ticDat = tdf.copy_to_pandas(oldDat, drop_pk_columns=False)
        checkTicDat()
        self.assertTrue(len(ticDat.d.dData1.sloc[1,:,:,:]) == 2 and ticDat.e.loc[11].values[0] == 11)



def runTheTests(fastOnly=True) :
    if not pd :
        print "!!!!!!!!!FAILING PANDAS UNIT TESTS DUE TO FAILURE TO LOAD PANDAS LIBRARIES!!!!!!!!"
        return
    runSuite(TestPandas, fastOnly=fastOnly)
# Run the tests.
if __name__ == "__main__":
    runTheTests()
