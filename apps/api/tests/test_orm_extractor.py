
from parsers import get_parser
from parsers.orm import PrismaParser
from parsers.python import PythonParser
from services.ingestion.extractor import GraphExtractor

PRISMA_SCHEMA = """
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

enum Role {
  USER
  ADMIN
}

model User {
  id        Int       @id @default(autoincrement())
  email     String    @unique
  role      Role      @default(USER)
  posts     Post[]
  profile   Profile?
  createdAt DateTime  @default(now())
}

model Profile {
  id     Int     @id @default(autoincrement())
  bio    String?
  userId Int     @unique
  user   User    @relation(fields: [userId], references: [id])
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  authorId  Int
  author    User     @relation(fields: [authorId], references: [id])
  published Boolean  @default(false)
}
"""

SQLALCHEMY_MODELS = """
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=True)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="orders")
"""

DJANGO_MODELS = """
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True)

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    is_published = models.BooleanField(default=False)
"""


class TestPrismaParser:
    def test_parses_prisma_models_and_enums(self):
        parser = PrismaParser()
        result = parser.parse(PRISMA_SCHEMA, "prisma/schema.prisma")

        model_names = [m.name for m in result.models]
        assert "User" in model_names
        assert "Profile" in model_names
        assert "Post" in model_names

        user_model = next(m for m in result.models if m.name == "User")
        assert "id" in user_model.metadata["primary_keys"]
        assert any(f["name"] == "email" and f["is_unique"] for f in user_model.metadata["fields"])

        profile_model = next(m for m in result.models if m.name == "Profile")
        assert any(fk["column"] == "userId" and fk["target_model"] == "User" for fk in profile_model.metadata["foreign_keys"])

        enums = [s for s in result.symbols if s.kind == "enum"]
        assert len(enums) == 1
        assert enums[0].name == "Role"
        assert "ADMIN" in enums[0].metadata["values"]

    def test_registry_resolves_prisma(self):
        parser = get_parser("prisma")
        assert isinstance(parser, PrismaParser)


class TestSQLAlchemyExtraction:
    def test_parses_sqlalchemy_declarative_models(self):
        parser = PythonParser()
        result = parser.parse(SQLALCHEMY_MODELS, "models.py")

        model_names = [m.name for m in result.models]
        assert "User" in model_names
        assert "Order" in model_names

        user_model = next(m for m in result.models if m.name == "User")
        assert user_model.metadata.get("orm") == "sqlalchemy"
        assert "id" in user_model.metadata["primary_keys"]

        order_model = next(m for m in result.models if m.name == "Order")
        assert any(fk["column"] == "user_id" and fk["target_model"] == "users" for fk in order_model.metadata["foreign_keys"])


class TestDjangoORMExtraction:
    def test_parses_django_models(self):
        parser = PythonParser()
        result = parser.parse(DJANGO_MODELS, "myapp/models.py")

        model_names = [m.name for m in result.models]
        assert "Author" in model_names
        assert "Book" in model_names

        author_model = next(m for m in result.models if m.name == "Author")
        assert author_model.metadata.get("orm") == "django"
        assert any(f["name"] == "name" for f in author_model.metadata["fields"])

        book_model = next(m for m in result.models if m.name == "Book")
        assert any(fk["column"] == "author" and fk["target_model"] == "Author" for fk in book_model.metadata["foreign_keys"])


class TestGraphExtractorORMIntegration:
    def test_extractor_creates_references_model_and_route_edges(self):
        prisma_parser = PrismaParser()
        py_parser = PythonParser()

        parsed_prisma = prisma_parser.parse(PRISMA_SCHEMA, "schema.prisma")

        api_code = """
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
def get_users():
    return []

@router.post("/posts")
def create_post():
    return {}
"""
        parsed_api = py_parser.parse(api_code, "api/routes.py")

        files = [
            {"path": "schema.prisma", "language": "prisma", "content": PRISMA_SCHEMA, "parsed": parsed_prisma},
            {"path": "api/routes.py", "language": "python", "content": api_code, "parsed": parsed_api},
        ]

        extractor = GraphExtractor(repo_id="test-repo")
        nodes, edges = extractor.extract(files)

        # 1. Verify model nodes created
        model_nodes = [n for n in nodes if n["type"] == "model"]
        assert len(model_nodes) >= 3
        model_names = {n["name"] for n in model_nodes}
        assert {"User", "Profile", "Post"}.issubset(model_names)

        # 2. Verify references_model edges
        ref_edges = [e for e in edges if e["type"] == "references_model"]
        assert len(ref_edges) >= 2

        # Profile -> User, Post -> User
        ref_targets = [e["target_key"] for e in ref_edges]
        assert any("User::model" in t for t in ref_targets)

        # 3. Verify route to model edges (queries_model and mutates_model)
        query_edges = [e for e in edges if e["type"] == "queries_model"]
        mutate_edges = [e for e in edges if e["type"] == "mutates_model"]

        assert any("GET /users" in e["source_key"] and "User::model" in e["target_key"] for e in query_edges)
        assert any("POST /posts" in e["source_key"] and "Post::model" in e["target_key"] for e in mutate_edges)
