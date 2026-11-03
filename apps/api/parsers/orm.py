"""Dedicated ORM model parser for Prisma, SQLAlchemy, and Django ORM schemas."""

import logging
import re
from typing import Any

from parsers.base import BaseParser, ParsedSymbol, ParseResult

logger = logging.getLogger(__name__)


class PrismaParser(BaseParser):
    """Parser for Prisma schema files (schema.prisma)."""

    MODEL_BLOCK_REGEX = re.compile(r"model\s+(\w+)\s*\{([^}]*)\}", re.MULTILINE | re.DOTALL)
    ENUM_BLOCK_REGEX = re.compile(r"enum\s+(\w+)\s*\{([^}]*)\}", re.MULTILINE | re.DOTALL)
    FIELD_LINE_REGEX = re.compile(r"^\s*(\w+)\s+(\w+)(\?|\[\])?(?:\s+(.*))?$", re.MULTILINE)
    RELATION_ATTR_REGEX = re.compile(
        r"@relation\((?:name:\s*[\"']([^\"']+)[\"'],?\s*)?(?:fields:\s*\[([^\]]+)\],?\s*)?(?:references:\s*\[([^\]]+)\])?.*?\)"
    )

    def parse(self, content: str, path: str) -> ParseResult:
        result = ParseResult(loc=self._count_loc(content))

        # 1. Parse Enums
        for match in self.ENUM_BLOCK_REGEX.finditer(content):
            enum_name = match.group(1)
            body = match.group(2)
            values = [line.strip() for line in body.splitlines() if line.strip() and not line.strip().startswith("//")]
            start_pos = match.start()
            line_num = content[:start_pos].count("\n") + 1
            result.symbols.append(
                ParsedSymbol(
                    name=enum_name,
                    kind="enum",
                    line=line_num,
                    metadata={"values": values, "orm": "prisma"},
                )
            )

        # 2. Parse Models
        for match in self.MODEL_BLOCK_REGEX.finditer(content):
            model_name = match.group(1)
            body = match.group(2)
            start_pos = match.start()
            line_num = content[:start_pos].count("\n") + 1
            end_line = content[: match.end()].count("\n") + 1

            fields: list[dict[str, Any]] = []
            foreign_keys: list[dict[str, Any]] = []
            primary_keys: list[str] = []
            relations: list[dict[str, Any]] = []

            for raw_line in body.splitlines():
                stripped = raw_line.strip()
                if not stripped or stripped.startswith("//"):
                    continue

                # Model level @@id([id, ...])
                if stripped.startswith("@@id"):
                    m_pk = re.search(r"@@id\(\[([^\]]+)\]\)", stripped)
                    if m_pk:
                        pks = [k.strip() for k in m_pk.group(1).split(",")]
                        primary_keys.extend(pks)
                    continue

                f_match = self.FIELD_LINE_REGEX.match(stripped)
                if not f_match:
                    continue

                field_name = f_match.group(1)
                field_type = f_match.group(2)
                type_modifier = f_match.group(3) or ""
                attributes = f_match.group(4) or ""

                is_nullable = "?" in type_modifier
                is_list = "[]" in type_modifier
                is_pk = "@id" in attributes
                is_unique = "@unique" in attributes

                if is_pk:
                    primary_keys.append(field_name)

                # Check @relation
                rel_match = self.RELATION_ATTR_REGEX.search(attributes)
                if rel_match:
                    rel_name = rel_match.group(1) or ""
                    fk_fields_raw = rel_match.group(2)
                    ref_fields_raw = rel_match.group(3)
                    fk_fields = [f.strip() for f in fk_fields_raw.split(",")] if fk_fields_raw else []
                    ref_fields = [f.strip() for f in ref_fields_raw.split(",")] if ref_fields_raw else []

                    rel_info = {
                        "field": field_name,
                        "target_model": field_type,
                        "name": rel_name,
                        "fields": fk_fields,
                        "references": ref_fields,
                    }
                    relations.append(rel_info)
                    for fk in fk_fields:
                        foreign_keys.append({
                            "column": fk,
                            "target_model": field_type,
                            "target_column": ref_fields[0] if ref_fields else "id",
                        })
                elif field_type[0].isupper() and field_type not in (
                    "String",
                    "Int",
                    "Boolean",
                    "Float",
                    "DateTime",
                    "Json",
                    "Bytes",
                    "Decimal",
                    "BigInt",
                ):
                    # Inferred Prisma relation without explicit @relation attribute
                    relations.append({
                        "field": field_name,
                        "target_model": field_type,
                        "is_list": is_list,
                    })

                fields.append({
                    "name": field_name,
                    "type": field_type,
                    "nullable": is_nullable,
                    "is_primary_key": is_pk,
                    "is_unique": is_unique,
                    "is_list": is_list,
                })

            model_symbol = ParsedSymbol(
                name=model_name,
                kind="model",
                line=line_num,
                end_line=end_line,
                metadata={
                    "orm": "prisma",
                    "fields": fields,
                    "primary_keys": primary_keys,
                    "foreign_keys": foreign_keys,
                    "relations": relations,
                },
            )
            result.models.append(model_symbol)
            result.symbols.append(model_symbol)

        return result


class PythonORMParser:
    """Helper parser to extract SQLAlchemy and Django ORM metadata from Python classes."""

    @classmethod
    def extract_model_metadata(
        cls,
        class_name: str,
        bases: list[str],
        body_text: str,
    ) -> dict[str, Any] | None:
        """Inspects class AST/text to determine if it is SQLAlchemy or Django and extracts details."""
        is_django = any("models.Model" in b or b == "Model" for b in bases) or "models." in body_text
        is_sqlalchemy = any(b in ("Base", "DeclarativeBase", "db.Model") for b in bases) or (
            "Column(" in body_text or "mapped_column(" in body_text
        )

        if not (is_django or is_sqlalchemy):
            return None

        orm_type = "django" if is_django else "sqlalchemy"
        fields: list[dict[str, Any]] = []
        foreign_keys: list[dict[str, Any]] = []
        primary_keys: list[str] = []
        relations: list[dict[str, Any]] = []

        for line in body_text.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue

            # Django ORM patterns
            # e.g.: user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
            # e.g.: tags = models.ManyToManyField("Tag")
            # e.g.: title = models.CharField(max_length=200, null=False)
            dj_match = re.search(r"^(\w+)\s*=\s*models\.(\w+)\s*\((.*)\)", line_str)
            if dj_match:
                fname, ftype, args = dj_match.group(1), dj_match.group(2), dj_match.group(3)
                nullable = bool(re.search(r"null\s*=\s*True", args))
                is_pk = bool(re.search(r"primary_key\s*=\s*True", args))
                if is_pk:
                    primary_keys.append(fname)

                if ftype in ("ForeignKey", "OneToOneField"):
                    target_match = re.search(r"^(?:to\s*=\s*)?['\"]?(\w+)['\"]?", args)
                    target_model = target_match.group(1) if target_match else ""
                    if target_model and target_model != "self":
                        foreign_keys.append({
                            "column": fname,
                            "target_model": target_model,
                            "target_column": "id",
                        })
                    relations.append({
                        "field": fname,
                        "type": ftype,
                        "target_model": target_model,
                        "nullable": nullable,
                    })
                elif ftype == "ManyToManyField":
                    target_match = re.search(r"^(?:to\s*=\s*)?['\"]?(\w+)['\"]?", args)
                    target_model = target_match.group(1) if target_match else ""
                    relations.append({
                        "field": fname,
                        "type": "ManyToMany",
                        "target_model": target_model,
                    })

                fields.append({
                    "name": fname,
                    "type": ftype,
                    "nullable": nullable,
                    "is_primary_key": is_pk,
                })
                continue

            # SQLAlchemy ORM patterns
            # e.g.: id = Column(Integer, primary_key=True)
            # e.g.: id: Mapped[int] = mapped_column(Integer, primary_key=True)
            # e.g.: user_id = Column(Integer, ForeignKey("users.id"))
            # e.g.: user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
            # e.g.: user = relationship("User", back_populates="posts")
            sa_rel = re.search(r"^(\w+)(?::\s*[^=]+)?\s*=\s*relationship\s*\(\s*['\"]?(\w+)['\"]?", line_str)
            if sa_rel:
                fname, target_model = sa_rel.group(1), sa_rel.group(2)
                relations.append({
                    "field": fname,
                    "type": "relationship",
                    "target_model": target_model,
                })
                continue

            sa_col = re.search(
                r"^(\w+)(?::\s*(?:Mapped\[([^\]]+)\]|[^=]+))?\s*=\s*(?:db\.)?(?:Column|mapped_column)\s*\((.*)\)",
                line_str,
            )
            if sa_col:
                fname = sa_col.group(1)
                mapped_type = sa_col.group(2) or ""
                args = sa_col.group(3)

                is_pk = bool(re.search(r"primary_key\s*=\s*True", args))
                if is_pk:
                    primary_keys.append(fname)

                nullable = True
                if re.search(r"nullable\s*=\s*False", args) or (mapped_type and not mapped_type.startswith("Optional")):
                    nullable = False
                if is_pk:
                    nullable = False

                # Foreign Key check
                fk_match = re.search(r"ForeignKey\s*\(\s*['\"]([\w.]+)(?:\.(\w+))?['\"]", args)
                if fk_match:
                    target_table_or_model = fk_match.group(1)
                    target_col = fk_match.group(2) or "id"
                    # Format Target: table or model
                    target_model = target_table_or_model.split(".")[0]
                    foreign_keys.append({
                        "column": fname,
                        "target_model": target_model,
                        "target_column": target_col,
                    })

                col_type = mapped_type
                if not col_type:
                    type_match = re.search(r"(?:Column|mapped_column)\s*\(\s*([A-Za-z0-9_]+)", line_str)
                    col_type = type_match.group(1) if type_match else "unknown"

                fields.append({
                    "name": fname,
                    "type": col_type,
                    "nullable": nullable,
                    "is_primary_key": is_pk,
                })

        return {
            "orm": orm_type,
            "fields": fields,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "relations": relations,
        }
