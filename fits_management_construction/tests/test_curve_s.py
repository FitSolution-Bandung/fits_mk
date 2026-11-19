from datetime import date, datetime

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "fits_mk")
class TestCurveS(TransactionCase):
    """Plan/actual weights flow from task progress into the project S-curve."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["project.project"].create({
            "name": "Proyek Uji MK",
            "total_cost": 1000.0,
            "date_start": date(2026, 1, 1),
            "date": date(2026, 1, 10),
        })
        cls.task_a = cls.env["project.task"].create({
            "name": "Pondasi", "project_id": cls.project.id, "task_cost": 600.0,
            "start_date": datetime(2026, 1, 1, 8), "end_date": datetime(2026, 1, 3, 17),
        })
        cls.task_b = cls.env["project.task"].create({
            "name": "Struktur", "project_id": cls.project.id, "task_cost": 400.0,
            "start_date": datetime(2026, 1, 3, 8), "end_date": datetime(2026, 1, 4, 17),
        })

    def test_task_weight_from_cost(self):
        self.assertAlmostEqual(self.task_a.task_weight, 60.0)
        self.assertAlmostEqual(self.task_b.task_weight, 40.0)

    def test_generate_progress_dates_per_task(self):
        (self.task_a | self.task_b).generate_progress_dates()
        self.assertEqual(len(self.task_a.progress_ids), 3)
        self.assertEqual(len(self.task_b.progress_ids), 2)
        # each task spreads its own weight, not the first task's
        self.assertAlmostEqual(sum(self.task_a.progress_ids.mapped("plan_weight")), 60.0)
        self.assertAlmostEqual(sum(self.task_b.progress_ids.mapped("plan_weight")), 40.0)

    def test_curve_cumulative_and_deviation(self):
        (self.task_a | self.task_b).generate_progress_dates()
        # Pondasi fully done on day 1 and 2 only (2/3 of its plan)
        for line in self.task_a.progress_ids.sorted("date")[:2]:
            line.progress = 100.0
        curve = self.env["project.curve.s"].create({"project_id": self.project.id})
        curve.calculate_progress()

        lines = curve.line_ids.sorted("date")
        self.assertEqual(lines.mapped("date"), [date(2026, 1, d) for d in (1, 2, 3, 4)])
        self.assertAlmostEqual(lines[-1].plan_weight, 100.0)
        self.assertAlmostEqual(curve.plan_weight, 100.0)
        self.assertAlmostEqual(curve.actual_weight, 40.0)
        self.assertAlmostEqual(curve.deviasi, -60.0)
        # cumulative: never decreasing
        plans = lines.mapped("plan_weight")
        self.assertEqual(plans, sorted(plans))

        self.project.update_progress_project()
        self.assertAlmostEqual(self.project.progress_project, 40.0)
