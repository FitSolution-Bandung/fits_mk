from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged

MK_USER = "fits_management_construction.group_management_construction_user"


@tagged("post_install", "-at_install", "fits_mk")
class TestProjectAccess(TransactionCase):
    """K11: MK documents follow the read access of their project.project."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.member = new_test_user(cls.env, "mk_member", groups=f"base.group_user,{MK_USER}")
        cls.outsider = new_test_user(cls.env, "mk_outsider", groups=f"base.group_user,{MK_USER}")
        Project = cls.env["project.project"]
        cls.private = Project.create({"name": "Proyek Tertutup", "privacy_visibility": "followers"})
        cls.private.message_subscribe(partner_ids=cls.member.partner_id.ids)
        cls.open = Project.create({"name": "Proyek Terbuka", "privacy_visibility": "employees"})
        cls.report_private = cls.env["daily.report"].create({"project": cls.private.id})
        cls.report_open = cls.env["daily.report"].create({"project": cls.open.id})
        cls.hse_private = cls.env["health.safety.environment"].create({"project_id": cls.private.id})

    def _visible(self, user, model):
        return self.env[model].with_user(user).search([]).ids

    def test_member_sees_private_project_documents(self):
        ids = self._visible(self.member, "daily.report")
        self.assertIn(self.report_private.id, ids)
        self.assertIn(self.report_open.id, ids)

    def test_outsider_cannot_see_private_project_documents(self):
        ids = self._visible(self.outsider, "daily.report")
        self.assertNotIn(self.report_private.id, ids)
        self.assertIn(self.report_open.id, ids)
        self.assertNotIn(self.hse_private.id, self._visible(self.outsider, "health.safety.environment"))
        with self.assertRaises(AccessError):
            self.report_private.with_user(self.outsider).read(["project"])
        with self.assertRaises(AccessError):
            self.report_private.with_user(self.outsider).write({"project": self.open.id})

    def test_access_follows_project_membership_changes(self):
        self.private.message_subscribe(partner_ids=self.outsider.partner_id.ids)
        self.env.flush_all()
        self.assertIn(self.report_private.id, self._visible(self.outsider, "daily.report"))

    def test_create_assigns_document_number(self):
        """Odoo 19 create() gets a list; the legacy numbering overrides must still run."""
        self.assertNotEqual(self.report_private.no_dr, "New")
        self.assertNotEqual(self.hse_private.no_hse, "New")
        two = self.env["daily.report"].create([{"project": self.open.id}, {"project": self.open.id}])
        self.assertEqual(len(two), 2)
        self.assertNotEqual(two[0].no_dr, two[1].no_dr)

    def test_company_follows_project(self):
        self.assertEqual(self.report_private.company_id, self.private.company_id)
        self.assertEqual(self.hse_private.company_id, self.private.company_id)

    def test_every_field_document_has_a_project(self):
        """All MK document models declare their project field and it is required."""
        missing = []
        for name in self.env.registry.models:
            model = self.env[name]
            field = getattr(type(model), "_mk_project_field", None)
            if field is None:
                continue
            if not model._fields[field].required and name not in ("task.progress", "curve.s.line", "project.curve.s"):
                missing.append(f"{name}.{field} not required")
        self.assertFalse(missing, "\n".join(missing))
        for name in ("analysis.risk.mitigation", "health.safety.environment", "execution.permits",
                     "implementation.permits", "overtime.form", "supervision.form",
                     "stakeholder.analysis", "document.inbond.outbond"):
            self.assertTrue(self.env[name]._fields["project_id"].required, name)
