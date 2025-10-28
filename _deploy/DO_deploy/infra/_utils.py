from pathlib import Path

from jinja2 import Template

from DO_deploy._types import EnvVarDataClass


def render_cloud_config(name: str, env_vars: EnvVarDataClass) -> str:
    """Return the plain-text contents of a cloud-config YAML file, ready to be passed to
    the body of a `client.droplets.create()` call (ie. a DropletRequest object).
    """
    PACKAGE_ROOT = Path(__file__).resolve().parent.parent
    template_fname = f"{name}.yaml.jinja"
    template_path = PACKAGE_ROOT / "infra" / "cloud_config_templates" / template_fname
    template_text = template_path.read_text(encoding="utf-8")
    return Template(template_text).render(**env_vars.as_dict())
