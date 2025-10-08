from pathlib import Path
import configparser
import re
import logging

logger = logging.getLogger(__name__)

class SmartConfig(configparser.ConfigParser):
    def __init__(self, config_path):
        super().__init__(strict=False)
        self.config_path = Path(config_path)
        self._comments = {}
        self._load_comments()
        self.read(self.config_path)
        self.changed = False

    def _load_comments(self):
        """Parse existing comments from file into self._comments dict."""
        if not self.config_path.exists():
            return
        section = None
        option = None
        last_comment_lines = []
        with self.config_path.open(encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    last_comment_lines = []
                    continue
                if stripped.startswith('[') and stripped.endswith(']'):
                    section = stripped[1:-1]
                    last_comment_lines = []
                    option = None
                elif stripped.startswith('#'):
                    last_comment_lines.append(stripped.lstrip('# ').rstrip())
                else:
                    match = re.match(r'([^=]+)=(.*)', line)
                    if match and section:
                        option = match.group(1).strip()
                        if last_comment_lines:
                            comment = "\n".join(last_comment_lines)
                            self._comments[(section, option)] = comment
                        last_comment_lines = []
                    else:
                        last_comment_lines = []

    def _write_with_comments(self):
        lines = []
        for section in self.sections():
            lines.append(f"[{section}]")
            for key, value in self.items(section):
                comment = self._comments.get((section, key))
                if comment:
                    for line in comment.splitlines():
                        lines.append(f"# {line}")
                lines.append(f"{key} = {value}")
            lines.append("")
        self.changed = True
        self.config_path.write_text("\n".join(lines), encoding='utf-8')

    def _set_with_comment(self, section, option, value, description=None):
        if not self.has_section(section):
            self.add_section(section)
        if not self.has_option(section, option):
            logger.debug(f"Adding config item [{section}]{option} = {value} with description: {description}")
            self.set(section, option, str(value))
            if description:
                self._comments[(section, option)] = description
            self._write_with_comments()

    def config_changed(self) -> bool:
        return self.changed

    def get(self, section, option, fallback=None, choices=None, description=None, **kwargs):
        if not self.has_option(section, option):
            if fallback is None:
                raise KeyError(f"Missing '{section}.{option}' and no fallback provided.")
            self._set_with_comment(section, option, fallback, description)
        value = super().get(section, option, fallback=fallback, **kwargs)
        if choices is not None and type(choices) == list:
            if value not in choices:
                if fallback is None:
                    raise KeyError(f"Missing '{section}.{option}' and no fallback provided.")
                return fallback
        return value

    def getboolean(self, section, option, fallback=None, description=None):
        if not self.has_option(section, option):
            if fallback is None:
                raise KeyError(f"Missing '{section}.{option}' and no fallback provided.")
            self._set_with_comment(section, option, fallback, description)
        return super().getboolean(section, option, fallback=fallback)

    def getint(self, section, option, fallback=None, description=None):
        if not self.has_option(section, option):
            if fallback is None:
                raise KeyError(f"Missing '{section}.{option}' and no fallback provided.")
            self._set_with_comment(section, option, fallback, description)
        return super().getint(section, option, fallback=fallback)

    def getfloat(self, section, option, fallback=None, description=None):
        if not self.has_option(section, option):
            if fallback is None:
                raise KeyError(f"Missing '{section}.{option}' and no fallback provided.")
            self._set_with_comment(section, option, fallback, description)
        return super().getfloat(section, option, fallback=fallback)
