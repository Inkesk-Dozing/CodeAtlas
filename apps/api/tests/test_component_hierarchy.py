
from parsers.javascript import JavaScriptParser
from services.ingestion.extractor import GraphExtractor

REACT_SAMPLE = """
import React, { useState } from 'react';
import { useAuth } from './hooks/useAuth';
import { UserAvatar } from './components/UserAvatar';
import { NotificationBadge } from './components/NotificationBadge';

export interface HeaderProps {
    title: string;
    showNotification?: boolean;
    theme?: string;
}

export function Header({ title, showNotification = true, theme = "dark" }: HeaderProps) {
    const { user } = useAuth();
    const [open, setOpen] = useState(false);

    return (
        <header className="header-bar">
            <div className="logo-container">
                <h1>{title}</h1>
            </div>
            <nav>
                <UserAvatar user={user} size={32} />
                {showNotification && <NotificationBadge count={5} />}
                <button onClick={() => setOpen(!open)}>Menu</button>
            </nav>
        </header>
    );
}

export const MemoizedHeader = React.memo(Header);
"""

HOOK_SAMPLE = """
import { useState, useEffect } from 'react';

export function useAuth() {
    const [user, setUser] = useState(null);
    useEffect(() => {
        // auth logic
    }, []);
    return { user };
}

export const useTheme = () => {
    return 'dark';
};
"""

CHILD_COMP_SAMPLE = """
import React from 'react';

export function UserAvatar({ user, size = 24 }: { user: any; size?: number }) {
    return (
        <div className="avatar">
            <img src={user?.avatarUrl} alt="Avatar" />
            <span>{user?.name}</span>
        </div>
    );
}

export function NotificationBadge({ count = 0 }) {
    return <span>{count}</span>;
}
"""


class TestReactComponentAndHookExtraction:
    def setup_method(self):
        self.parser = JavaScriptParser()

    def test_distinguishes_primitive_html_from_custom_components(self):
        result = self.parser.parse(REACT_SAMPLE, "src/Header.tsx")
        assert len(result.components) >= 1

        header_comp = next(c for c in result.components if c.name == "Header")
        renders = header_comp.metadata.get("renders", [])

        # Should include custom components
        assert "UserAvatar" in renders
        assert "NotificationBadge" in renders

        # Should NOT include primitive HTML elements
        assert "header" not in renders
        assert "div" not in renders
        assert "h1" not in renders
        assert "nav" not in renders
        assert "button" not in renders

    def test_captures_props_definitions_and_default_values(self):
        result = self.parser.parse(REACT_SAMPLE, "src/Header.tsx")
        header_comp = next(c for c in result.components if c.name == "Header")

        props = header_comp.metadata.get("props", [])
        prop_defaults = header_comp.metadata.get("prop_defaults", {})
        props_interface = header_comp.metadata.get("props_interface")

        assert "title" in props
        assert "showNotification" in props
        assert "theme" in props
        assert prop_defaults.get("showNotification") == "true"
        assert prop_defaults.get("theme") in ('"dark"', "'dark'")
        assert props_interface == "HeaderProps"

    def test_detects_custom_and_react_hooks(self):
        result = self.parser.parse(REACT_SAMPLE, "src/Header.tsx")
        header_comp = next(c for c in result.components if c.name == "Header")

        hooks_used = header_comp.metadata.get("hooks_used", [])
        assert "useAuth" in hooks_used
        assert "useState" in hooks_used

    def test_parses_custom_hook_definitions(self):
        result = self.parser.parse(HOOK_SAMPLE, "src/hooks/useAuth.ts")
        hook_names = [h.name for h in result.hooks]

        assert "useAuth" in hook_names
        assert "useTheme" in hook_names
        assert all(h.kind == "hook" for h in result.hooks)

    def test_maps_cross_file_component_renders_and_hook_edges(self):
        p_header = self.parser.parse(REACT_SAMPLE, "src/Header.tsx")
        p_hook = self.parser.parse(HOOK_SAMPLE, "src/hooks/useAuth.ts")
        p_child = self.parser.parse(CHILD_COMP_SAMPLE, "src/components/UserAvatar.tsx")

        files = [
            {"path": "src/Header.tsx", "language": "typescript", "content": REACT_SAMPLE, "parsed": p_header},
            {"path": "src/hooks/useAuth.ts", "language": "typescript", "content": HOOK_SAMPLE, "parsed": p_hook},
            {"path": "src/components/UserAvatar.tsx", "language": "typescript", "content": CHILD_COMP_SAMPLE, "parsed": p_child},
        ]

        extractor = GraphExtractor(repo_id="repo-react")
        nodes, edges = extractor.extract(files)

        # Verify nodes created
        node_names = {n["name"] for n in nodes}
        assert "Header" in node_names
        assert "UserAvatar" in node_names
        assert "NotificationBadge" in node_names
        assert "useAuth" in node_names

        # Verify cross-file renders edges
        render_edges = [e for e in edges if e["type"] == "renders"]
        assert any(
            "src/Header.tsx::Header::component" in e["source_key"]
            and "src/components/UserAvatar.tsx::UserAvatar::component" in e["target_key"]
            for e in render_edges
        )

        # Verify uses_hook edges linking component to hook definition
        hook_edges = [e for e in edges if e["type"] == "uses_hook"]
        assert any(
            "src/Header.tsx::Header::component" in e["source_key"]
            and "src/hooks/useAuth.ts::useAuth::hook" in e["target_key"]
            for e in hook_edges
        )
