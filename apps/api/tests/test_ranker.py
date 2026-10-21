from services.mapping.ranker import (
    WEIGHTS,
    build_issue_text,
    split_ident,
    tier_for,
    tokenize,
)


class TestTokenize:
    def test_lowercases_and_drops_stopwords(self):
        assert tokenize("The Login Page crashes") == ["login", "page", "crashes"]

    def test_empty_input(self):
        assert tokenize("") == []
        assert tokenize(None) == []

    def test_keeps_identifiers(self):
        tokens = tokenize("getUserById fails")
        assert "getuserbyid" in tokens

    def test_single_chars_dropped(self):
        assert tokenize("a b c") == []


class TestSplitIdent:
    def test_camel_case(self):
        assert split_ident("getUserById") == ["get", "user", "by", "id"]

    def test_snake_case(self):
        assert split_ident("user_repository") == ["user", "repository"]

    def test_acronyms(self):
        assert split_ident("parseHTMLNode") == ["parse", "html", "node"]

    def test_pascal_case(self):
        assert split_ident("LoginPage") == ["login", "page"]


class TestTierFor:
    def test_high(self):
        assert tier_for(0.75) == "high"
        assert tier_for(0.99) == "high"

    def test_medium(self):
        assert tier_for(0.50) == "medium"
        assert tier_for(0.74) == "medium"

    def test_low(self):
        assert tier_for(0.30) == "low"
        assert tier_for(0.49) == "low"

    def test_excluded(self):
        assert tier_for(0.29) == "excluded"
        assert tier_for(0.0) == "excluded"


class TestWeights:
    def test_sums_to_one(self):
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_semantic_dominant(self):
        assert WEIGHTS["semantic"] == max(WEIGHTS.values())


class TestBuildIssueText:
    def test_includes_title_body_labels(self):
        class FakeIssue:
            title = "Crash on login"
            body = "Steps to reproduce..."
            labels = ["bug", "auth"]

        text = build_issue_text(FakeIssue())
        assert "Crash on login" in text
        assert "Steps to reproduce" in text
        assert "bug, auth" in text

    def test_handles_missing_body(self):
        class FakeIssue:
            title = "Title only"
            body = None
            labels = []

        text = build_issue_text(FakeIssue())
        assert "Title only" in text
