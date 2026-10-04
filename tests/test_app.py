import json,tempfile,unittest
from pathlib import Path
from contextlib import redirect_stdout,redirect_stderr
from io import StringIO
from habitloop.app import main, pd
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory()
  self.db=Path(self.t.name)/"x.json"
  self.args=["--data",str(self.db)]
 def tearDown(self):self.t.cleanup()
 def invoke(self,*a):
  o,e=StringIO(),StringIO()
  with redirect_stdout(o),redirect_stderr(e):c=main(self.args+list(a))
  return c,o.getvalue(),e.getvalue()
 def test_persist(self):self.assertEqual(self.invoke("add","阅读")[0],0);self.assertIn("阅读",self.invoke("list")[1])
 def test_duplicate_and_future(self):self.invoke("add","跑步");self.assertEqual(self.invoke("checkin","1","--date","2020-01-01")[0],0);self.assertEqual(self.invoke("checkin","1","--date","2020-01-01")[0],2);self.assertEqual(self.invoke("checkin","1","--date","2999-01-01")[0],2)
 def test_weekly_report(self):self.invoke("add","写作","--cadence","weekly","--target","2");self.invoke("checkin","1","--date","2020-01-01");self.invoke("checkin","1","--date","2020-01-02");self.assertIn("100.0%",self.invoke("report","1","--start","2020-01-01","--end","2020-01-05")[1])
 def test_weekly_rate_counts_missed_weeks_and_dates_are_strict(self):
  self.invoke("add","阅读","--cadence","weekly","--target","2")
  self.invoke("checkin","1","--date","2020-01-01")
  self.invoke("checkin","1","--date","2020-01-02")
  self.assertIn("50.0%",self.invoke("report","1","--start","2020-01-01","--end","2020-01-12")[1])
  with self.assertRaises(ValueError):pd("20200101")
 def test_uncheck(self):self.invoke("add","冥想");self.invoke("checkin","1","--date","2020-02-02");self.assertEqual(self.invoke("uncheck","1","--date","2020-02-02")[0],0);self.assertEqual(json.loads(self.db.read_text())["habits"][0]["checkins"],[])
 def test_bad_month(self):self.invoke("add","学习");self.assertEqual(self.invoke("calendar","1","--month","nope")[0],2)
