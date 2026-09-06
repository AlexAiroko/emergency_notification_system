from types import SimpleNamespace

import pytest

from app.exceptions.notification_template import TemplateRenderError
from app.services.template_renderer import TemplateRenderer


template = SimpleNamespace(subject="Subject: {{name}}", body="Hello {{name}}, id={{contact_id}}")
contact = SimpleNamespace(id=42, name="Alice")


class TestRenderBody:
    def test_system_vars(self):
        result = TemplateRenderer.render_body(template, contact, {})
        assert result == "Hello Alice, id=42"

    def test_custom_vars(self):
        tpl = SimpleNamespace(subject=None, body="Status: {{status}}")
        result = TemplateRenderer.render_body(tpl, contact, {"status": "active"})
        assert result == "Status: active"

    def test_mixed_vars(self):
        result = TemplateRenderer.render_body(template, contact, {"extra": "val"})
        assert "Alice" in result
        assert "42" in result


class TestRenderSubject:
    def test_subject_none(self):
        tpl = SimpleNamespace(subject=None, body="Body")
        result = TemplateRenderer.render_subject(tpl, contact, {})
        assert result is None

    def test_subject_with_vars(self):
        result = TemplateRenderer.render_subject(template, contact, {})
        assert result == "Subject: Alice"


class TestValidateVariables:
    def test_ok(self):
        missing = TemplateRenderer.validate_variables("Hello {{name}}", {})
        assert missing == []

    def test_missing(self):
        missing = TemplateRenderer.validate_variables("{{x}}", {})
        assert missing == ["x"]

    def test_subject_included(self):
        missing = TemplateRenderer.validate_variables("Body", {}, subject="Sub {{x}}")
        assert missing == ["x"]

    def test_sorted(self):
        missing = TemplateRenderer.validate_variables("{{b}} {{a}}", {})
        assert missing == ["a", "b"]


class TestRenderErrors:
    def test_syntax_error(self):
        tpl = SimpleNamespace(subject=None, body="{{bad")
        with pytest.raises(TemplateRenderError):
            TemplateRenderer.render_body(tpl, contact, {})

    def test_undefined_variable(self):
        tpl = SimpleNamespace(subject=None, body="{{x}}")
        result = TemplateRenderer.render_body(tpl, contact, {})
        assert result == ""
